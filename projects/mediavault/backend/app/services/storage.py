"""Storage abstraction supporting local disk and S3-compatible backends.

The API surface intentionally mirrors the small subset of object-storage
operations MediaVault needs (put, open, delete, presign) so the backend can be
swapped between local disk (development) and S3/MinIO (production) without
touching call sites.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(ABC):
    """Abstract object store."""

    @abstractmethod
    def save(self, key: str, fileobj: BinaryIO) -> int:
        """Persist a stream under ``key`` and return the number of bytes written."""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Open an object for reading."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    def presigned_url(self, key: str, expires_in: int) -> str | None:
        """Return a backend-native presigned URL when supported, else ``None``.

        The local backend returns ``None`` so the app falls back to serving the
        object through its own signed streaming endpoint.
        """
        return None


class LocalStorage(StorageBackend):
    """Filesystem-backed storage rooted at ``STORAGE_LOCAL_DIR``."""

    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal outside the storage root.
        target = (self.base / key).resolve()
        if not str(target).startswith(str(self.base.resolve())):
            raise ValueError("Invalid storage key")
        return target

    def save(self, key: str, fileobj: BinaryIO) -> int:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with open(path, "wb") as out:
            while chunk := fileobj.read(1024 * 1024):
                out.write(chunk)
                size += len(chunk)
        logger.info("stored object", fields={"key": key, "bytes": size, "backend": "local"})
        return size

    def open(self, key: str) -> BinaryIO:
        return open(self._path(key), "rb")

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage(StorageBackend):
    """S3-compatible storage (AWS S3 or MinIO) using boto3.

    boto3 is imported lazily so local/test environments do not require the
    dependency unless the S3 backend is actually selected.
    """

    def __init__(self) -> None:
        import boto3  # noqa: PLC0415 - lazy import by design

        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )

    def save(self, key: str, fileobj: BinaryIO) -> int:
        self.client.upload_fileobj(fileobj, self.bucket, key)
        head = self.client.head_object(Bucket=self.bucket, Key=key)
        size = int(head["ContentLength"])
        logger.info("stored object", fields={"key": key, "bytes": size, "backend": "s3"})
        return size

    def open(self, key: str) -> BinaryIO:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"]

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError  # noqa: PLC0415

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def presigned_url(self, key: str, expires_in: int) -> str | None:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the process-wide storage backend selected by configuration."""
    global _backend
    if _backend is None:
        if settings.STORAGE_BACKEND == "s3":
            _backend = S3Storage()
        else:
            _backend = LocalStorage(settings.STORAGE_LOCAL_DIR)
    return _backend


def reset_storage() -> None:
    """Reset the cached backend (used by tests)."""
    global _backend
    _backend = None
