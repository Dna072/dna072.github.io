"""Unit tests for upload content-type normalization and magic-byte sniffing."""

from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.utils.files import (
    normalize_content_type,
    resolve_upload_content_type,
    sniff_content_type,
    sniff_matches,
)

PNG_HEADER = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4")
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 20
PDF_HEADER = b"%PDF-1.7\n"
PDF_WITH_BOM = b"\xef\xbb\xbf%PDF-1.4\n"
MP4_HEADER = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 20
MP4_AFTER_FREE = b"\x00\x00\x00\x10free" + b"\x00" * 8 + b"\x00\x00\x00\x18ftypisom" + b"\x00" * 8


def test_normalize_aliases_and_parameters():
    assert normalize_content_type("image/jpg") == "image/jpeg"
    assert normalize_content_type("IMAGE/PNG; charset=binary") == "image/png"
    assert normalize_content_type("") == "application/octet-stream"
    assert normalize_content_type(None) == "application/octet-stream"


def test_sniff_common_formats():
    assert sniff_content_type(PNG_HEADER) == "image/png"
    assert sniff_content_type(JPEG_HEADER) == "image/jpeg"
    assert sniff_content_type(PDF_HEADER) == "application/pdf"
    assert sniff_content_type(PDF_WITH_BOM) == "application/pdf"
    assert sniff_content_type(MP4_HEADER) == "video/mp4"
    assert sniff_content_type(MP4_AFTER_FREE) == "video/mp4"


def test_resolve_corrects_mislabeled_png():
    # Browser said jpeg, bytes are png → trust bytes.
    assert resolve_upload_content_type("image/jpeg", PNG_HEADER) == "image/png"


def test_resolve_accepts_octet_stream_when_sniffable():
    assert resolve_upload_content_type("application/octet-stream", PNG_HEADER) == "image/png"
    assert resolve_upload_content_type("image/jpg", JPEG_HEADER) == "image/jpeg"


def test_resolve_rejects_true_mismatch_for_unknown_bytes():
    with pytest.raises(ValidationError) as exc:
        resolve_upload_content_type("image/png", b"not-a-real-png")
    assert exc.value.code == "content_type_mismatch"


def test_quicktime_no_longer_blindly_passes():
    # Previously video/quicktime had no signature entry and always returned True.
    assert sniff_matches("video/quicktime", MP4_HEADER) is True
    assert sniff_matches("video/quicktime", b"hello world") is False
