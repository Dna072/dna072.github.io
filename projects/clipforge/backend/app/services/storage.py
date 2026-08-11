"""Local filesystem storage abstraction.

Mirrors an object-store interface (put/path/url) so the production swap to S3 is
localized to this module. See the README AWS section for the mapping.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class LocalStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.storage_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _abs(self, key: str) -> Path:
        target = (self.base_dir / key).resolve()
        base = self.base_dir.resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("path traversal detected")
        return target

    def save_stream(self, key: str, stream: BinaryIO) -> int:
        """Persist an uploaded stream to ``key``; returns bytes written."""
        dest = self._abs(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with open(dest, "wb") as fh:
            while chunk := stream.read(1024 * 1024):
                fh.write(chunk)
                size += len(chunk)
        return size

    def path(self, key: str) -> str:
        return str(self._abs(key))

    def exists(self, key: str) -> bool:
        return self._abs(key).exists()

    def delete(self, key: str) -> None:
        p = self._abs(key)
        if p.exists():
            p.unlink()

    def delete_prefix(self, prefix: str) -> None:
        target = self._abs(prefix)
        if target.exists() and target.is_dir():
            shutil.rmtree(target)

    @staticmethod
    def public_url(key: str | None) -> str | None:
        """Return a client-facing URL for a stored asset.

        Locally these are served by the API's ``/media`` static mount. In
        production this becomes a CloudFront/S3 signed URL.
        """
        if not key:
            return None
        return f"/media/{key.lstrip('/')}"


storage = LocalStorage()

__all__ = ["LocalStorage", "storage"]
