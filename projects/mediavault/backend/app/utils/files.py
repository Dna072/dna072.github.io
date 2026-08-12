"""Upload validation and file inspection helpers."""

from __future__ import annotations

import hashlib
import struct
from typing import BinaryIO

from app.core.config import settings
from app.core.exceptions import ValidationError

# Magic-number signatures used to sanity-check that the declared content type
# matches the actual bytes, mitigating content-type spoofing on upload.
_SIGNATURES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "application/pdf": [b"%PDF-"],
    "image/webp": [b"RIFF"],  # followed by WEBP at offset 8
    "video/mp4": [b"\x00\x00\x00"],  # ftyp box appears near the start
    "video/quicktime": [b"\x00\x00\x00"],
    "video/webm": [b"\x1a\x45\xdf\xa3"],
    "video/x-matroska": [b"\x1a\x45\xdf\xa3"],
}

# Client-supplied aliases → canonical MIME types we accept.
_CONTENT_TYPE_ALIASES: dict[str, str] = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
    "audio/mp4": "video/mp4",
    "video/x-m4v": "video/mp4",
    "video/mpeg4": "video/mp4",
    "video/x-mp4": "video/mp4",
    "application/mp4": "video/mp4",
    "video/mov": "video/quicktime",
    "video/x-quicktime": "video/quicktime",
    "application/x-matroska": "video/x-matroska",
}


def normalize_content_type(content_type: str | None) -> str:
    """Strip parameters, lowercase, and map common browser aliases."""
    if not content_type:
        return "application/octet-stream"
    raw = content_type.split(";", 1)[0].strip().lower()
    if not raw:
        return "application/octet-stream"
    return _CONTENT_TYPE_ALIASES.get(raw, raw)


def sniff_content_type(header: bytes) -> str | None:
    """Return a canonical content type detected from magic bytes, if any."""
    if not header:
        return None

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"

    # PDFs may include a UTF-8 BOM or a small amount of leading whitespace.
    trimmed = header.lstrip(b"\x00\t\n\r\x0c ")
    if trimmed.startswith(b"\xef\xbb\xbf"):
        trimmed = trimmed[3:].lstrip(b"\x00\t\n\r\x0c ")
    if trimmed.startswith(b"%PDF-") or b"%PDF-" in header[:64]:
        return "application/pdf"

    if header.startswith(b"\x1a\x45\xdf\xa3"):
        # EBML container used by both WebM and Matroska; default to WebM.
        return "video/webm"

    # ISO BMFF (MP4 / MOV): look for an 'ftyp' box in the first 64 bytes.
    if _has_ftyp_box(header):
        brand = _ftyp_brand(header)
        if brand in {b"qt  ", b"nvr1"}:
            return "video/quicktime"
        return "video/mp4"

    return None


def _has_ftyp_box(header: bytes) -> bool:
    # Typical layout: [size:4][ftyp:4][brand:4]… — also allow a short skip.
    window = header[:64]
    idx = window.find(b"ftyp")
    if idx < 4:
        return False
    # The 4 bytes before 'ftyp' are the box size; treat that as a soft check.
    return True


def _ftyp_brand(header: bytes) -> bytes | None:
    idx = header[:64].find(b"ftyp")
    if idx < 0:
        return None
    start = idx + 4
    end = start + 4
    if len(header) < end:
        return None
    return header[start:end]


def validate_content_type(content_type: str) -> None:
    if content_type not in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported content type '{content_type}'.",
            code="unsupported_media_type",
            status_code=415,
        )


def sniff_matches(content_type: str, header: bytes) -> bool:
    """Best-effort magic-number check against a declared content type."""
    content_type = normalize_content_type(content_type)
    signatures = _SIGNATURES.get(content_type)
    if not signatures:
        return True

    detected = sniff_content_type(header)
    if detected is not None:
        return _types_compatible(content_type, detected)

    if content_type in {"video/mp4", "video/quicktime"}:
        return _has_ftyp_box(header)
    if content_type == "image/webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if content_type == "application/pdf":
        return b"%PDF-" in header[:1024]
    return any(header.startswith(sig) for sig in signatures)


def _types_compatible(declared: str, detected: str) -> bool:
    if declared == detected:
        return True
    # MP4 and QuickTime share the ISO BMFF container.
    iso_bmff = {"video/mp4", "video/quicktime"}
    if declared in iso_bmff and detected in iso_bmff:
        return True
    # WebM / Matroska share EBML.
    ebml = {"video/webm", "video/x-matroska"}
    if declared in ebml and detected in ebml:
        return True
    return False


def resolve_upload_content_type(declared: str | None, header: bytes) -> str:
    """Resolve the content type to persist for an upload.

    Prefers magic-byte detection when the client sends a generic/empty type or
    a mismatched type that we can confidently correct from the file bytes.
    """
    normalized = normalize_content_type(declared)
    detected = sniff_content_type(header)

    if detected is None:
        if normalized in settings.ALLOWED_UPLOAD_CONTENT_TYPES and sniff_matches(normalized, header):
            return normalized
        if normalized in settings.ALLOWED_UPLOAD_CONTENT_TYPES and not sniff_matches(normalized, header):
            raise ValidationError(
                "File contents do not match the declared content type.",
                code="content_type_mismatch",
            )
        raise ValidationError(
            f"Unsupported content type '{normalized}'.",
            code="unsupported_media_type",
            status_code=415,
        )

    if normalized in {"application/octet-stream", "binary/octet-stream"}:
        return detected

    if _types_compatible(normalized, detected):
        # Prefer the client's more specific ISO BMFF label when compatible.
        if normalized in {"video/mp4", "video/quicktime"}:
            return normalized
        if normalized in {"video/webm", "video/x-matroska"}:
            return normalized
        return detected

    # Client lied or mislabeled — trust the bytes when they are an allowed type.
    if detected in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        return detected

    raise ValidationError(
        "File contents do not match the declared content type.",
        code="content_type_mismatch",
    )


def stream_to_temp_with_limits(
    fileobj: BinaryIO, content_type: str, max_bytes: int
) -> tuple[bytes, str, int]:
    """Read a stream fully into memory-safe chunks, enforcing the size limit.

    Returns ``(header_bytes, sha256_hex, total_size)`` and leaves ``fileobj``
    exhausted. Callers should ``seek(0)`` before persisting.
    """
    hasher = hashlib.sha256()
    size = 0
    header = b""
    while chunk := fileobj.read(1024 * 1024):
        size += len(chunk)
        if size > max_bytes:
            raise ValidationError(
                f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                code="payload_too_large",
                status_code=413,
            )
        if not header:
            header = chunk[:64]
        hasher.update(chunk)
    if size == 0:
        raise ValidationError("Uploaded file is empty.")
    return header, hasher.hexdigest(), size


def read_png_dimensions(header: bytes) -> tuple[int | None, int | None]:
    """Extract width/height from a PNG IHDR chunk when possible."""
    try:
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            width, height = struct.unpack(">II", header[16:24])
            return width, height
    except struct.error:
        pass
    return None, None
