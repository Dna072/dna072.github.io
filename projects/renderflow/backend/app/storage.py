"""Object storage abstraction.

The rest of the codebase talks to an :class:`ObjectStorage` interface so we can
swap a local filesystem (dev / CI) for S3-compatible storage (production) with
a single config flag and no code changes.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from .config import Settings, get_settings


class ObjectStorage(ABC):
    """Minimal object storage contract used by the workers."""

    @abstractmethod
    def save(self, local_path: str, key: str) -> str:
        """Persist ``local_path`` under ``key`` and return a canonical URI."""

    @abstractmethod
    def open_local(self, uri: str) -> str:
        """Return a local filesystem path for ``uri`` (downloading if needed)."""

    @abstractmethod
    def exists(self, uri: str) -> bool:
        ...


class LocalStorage(ObjectStorage):
    """Filesystem-backed storage rooted at ``storage_local_dir``."""

    scheme = "file://"

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, uri: str) -> Path:
        if uri.startswith(self.scheme):
            uri = uri[len(self.scheme) :]
        path = Path(uri)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    def save(self, local_path: str, key: str) -> str:
        dest = self.base_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        if Path(local_path).resolve() != dest.resolve():
            shutil.copy2(local_path, dest)
        return f"{self.scheme}{dest}"

    def open_local(self, uri: str) -> str:
        return str(self._resolve(uri))

    def exists(self, uri: str) -> bool:
        # http(s) inputs are assumed reachable; workers validate at fetch time.
        if uri.startswith(("http://", "https://")):
            return True
        return self._resolve(uri).exists()


class S3Storage(ObjectStorage):
    """S3-compatible storage (AWS S3, MinIO, ...). Requires boto3.

    Kept import-light: boto3 is only imported when this backend is selected so
    local/CI runs don't need the dependency installed.
    """

    scheme = "s3://"

    def __init__(self, settings: Settings) -> None:
        import boto3  # local import; optional dependency

        self.bucket = settings.s3_bucket
        self._tmp = Path(tempfile.gettempdir()) / "renderflow-s3"
        self._tmp.mkdir(parents=True, exist_ok=True)
        client_kwargs: dict = {"region_name": settings.s3_region}
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url
        self.client = boto3.client("s3", **client_kwargs)

    def _split(self, uri: str) -> tuple[str, str]:
        path = uri[len(self.scheme) :] if uri.startswith(self.scheme) else uri
        bucket, _, key = path.partition("/")
        return bucket, key

    def save(self, local_path: str, key: str) -> str:
        self.client.upload_file(local_path, self.bucket, key)
        return f"{self.scheme}{self.bucket}/{key}"

    def open_local(self, uri: str) -> str:
        bucket, key = self._split(uri)
        dest = self._tmp / key.replace("/", "_")
        self.client.download_file(bucket, key, str(dest))
        return str(dest)

    def exists(self, uri: str) -> bool:
        if uri.startswith(("http://", "https://")):
            return True
        bucket, key = self._split(uri)
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:  # noqa: BLE001 - treat any failure as "missing"
            return False


def get_storage(settings: Settings | None = None) -> ObjectStorage:
    settings = settings or get_settings()
    if settings.storage_backend == "s3":
        return S3Storage(settings)
    return LocalStorage(settings.storage_local_dir)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
