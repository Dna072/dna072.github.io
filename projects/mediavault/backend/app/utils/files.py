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
    "video/mp4": [b"\x00\x00\x00"],  # ftyp box appears at offset 4
    "video/webm": [b"\x1a\x45\xdf\xa3"],
    "video/x-matroska": [b"\x1a\x45\xdf\xa3"],
}


def validate_content_type(content_type: str) -> None:
    if content_type not in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported content type '{content_type}'.",
            code="unsupported_media_type",
            status_code=415,
        )


def sniff_matches(content_type: str, header: bytes) -> bool:
    """Best-effort magic-number check. Unknown types pass (declared-only)."""
    signatures = _SIGNATURES.get(content_type)
    if not signatures:
        return True
    if content_type in {"video/mp4", "video/quicktime"}:
        # MP4/MOV: bytes 4..8 spell 'ftyp'.
        return b"ftyp" in header[:16]
    if content_type == "image/webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    return any(header.startswith(sig) for sig in signatures)


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
            header = chunk[:32]
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
