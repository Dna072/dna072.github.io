"""Storage abstraction.

`StorageBackend` defines the contract used by the API layer. `LocalStorage` is
the only implementation shipped here (files on disk under `STORAGE_ROOT`),
but the interface mirrors what an S3-backed implementation would look like
(`save`, `open_stream`, `delete`, `exists`) so swapping backends in production
is a matter of implementing this protocol against boto3, not rewriting the
API. Signed, time-limited download URLs are generated with `itsdangerous`
rather than exposing raw storage keys, matching the ergonomics of S3
presigned URLs.
"""

import hashlib
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="mediavault-signed-url")


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, file_obj: BinaryIO) -> tuple[int, str]:
        """Persist a file under `key`. Returns (size_bytes, sha256_checksum)."""

    @abstractmethod
    def open_stream(self, key: str) -> BinaryIO:
        """Return a readable binary stream for the stored object."""

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalStorage(StorageBackend):
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or settings.STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def build_key(self, workspace_id: uuid.UUID, filename: str) -> str:
        safe_name = Path(filename).name
        return f"{workspace_id}/{uuid.uuid4().hex}_{safe_name}"

    def _resolve(self, key: str) -> Path:
        resolved = (self.root / key).resolve()
        if self.root.resolve() not in resolved.parents and resolved != self.root.resolve():
            raise ValueError("Invalid storage key (path traversal detected)")
        return resolved

    def save(self, key: str, file_obj: BinaryIO) -> tuple[int, str]:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        hasher = hashlib.sha256()
        size = 0
        with open(path, "wb") as out:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                hasher.update(chunk)
                size += len(chunk)
                out.write(chunk)
        return size, hasher.hexdigest()

    def open_stream(self, key: str) -> BinaryIO:
        path = self._resolve(key)
        return open(path, "rb")

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def wipe(self) -> None:
        """Test-only helper: remove all stored files."""
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)


def get_storage() -> StorageBackend:
    return LocalStorage()


def generate_signed_download_token(
    asset_id: uuid.UUID, expires_seconds: int | None = None
) -> tuple[str, datetime]:
    expires_seconds = expires_seconds or settings.SIGNED_URL_EXPIRE_SECONDS
    token = _serializer.dumps({"asset_id": str(asset_id)})
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_seconds)
    return token, expires_at


def verify_signed_download_token(
    token: str, expires_seconds: int | None = None
) -> uuid.UUID | None:
    expires_seconds = expires_seconds or settings.SIGNED_URL_EXPIRE_SECONDS
    try:
        data = _serializer.loads(token, max_age=expires_seconds)
    except (BadSignature, SignatureExpired):
        return None
    try:
        return uuid.UUID(data["asset_id"])
    except (KeyError, ValueError, TypeError):
        return None
