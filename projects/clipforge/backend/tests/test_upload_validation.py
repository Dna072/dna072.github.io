from __future__ import annotations

import pytest
from app.core.config import settings
from app.services.video_service import UploadValidationError, VideoService


def test_valid_upload_passes():
    VideoService.validate_upload("clip.mp4", "video/mp4", 1024)


def test_empty_file_rejected():
    with pytest.raises(UploadValidationError):
        VideoService.validate_upload("clip.mp4", "video/mp4", 0)


def test_oversized_file_rejected():
    with pytest.raises(UploadValidationError):
        VideoService.validate_upload("clip.mp4", "video/mp4", settings.max_upload_bytes + 1)


def test_bad_extension_rejected():
    with pytest.raises(UploadValidationError):
        VideoService.validate_upload("malware.exe", "video/mp4", 1024)


def test_bad_mime_rejected():
    with pytest.raises(UploadValidationError):
        VideoService.validate_upload("clip.mp4", "application/x-msdownload", 1024)
