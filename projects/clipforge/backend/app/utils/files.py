"""Filesystem helpers for uploaded media storage."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.config import settings


def ensure_storage_dir() -> Path:
    """Ensure the configured storage directory exists and return it."""
    path = Path(settings.storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def video_dir(video_id: str) -> Path:
    """Return (and create) the directory for a specific video's artifacts."""
    path = ensure_storage_dir() / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def human_size(num_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def safe_extension(filename: str) -> str:
    """Return the lowercased extension (without dot) of a filename."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()
