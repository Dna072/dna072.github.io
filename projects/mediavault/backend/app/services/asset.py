"""Asset service: validated upload, metadata, signed access, tagging."""

from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.security import sign_asset_url
from app.models.asset import Asset
from app.models.enums import AssetKind, AssetStatus
from app.models.user import User
from app.repositories.asset import AssetFilter, AssetRepository
from app.repositories.folder import FolderRepository
from app.repositories.tag import TagRepository
from app.schemas.asset import SignedUrlResponse
from app.services.storage import get_storage
from app.utils.files import (
    read_png_dimensions,
    resolve_upload_content_type,
    stream_to_temp_with_limits,
)


class AssetService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assets = AssetRepository(db)
        self.folders = FolderRepository(db)
        self.tags = TagRepository(db)
        self.storage = get_storage()

    # --- Upload -------------------------------------------------------------
    def upload(
        self,
        workspace_id: uuid.UUID,
        user: User,
        *,
        fileobj: BinaryIO,
        filename: str,
        content_type: str,
        name: str | None = None,
        description: str = "",
        folder_id: uuid.UUID | None = None,
    ) -> Asset:
        if folder_id is not None and self.folders.get_scoped(workspace_id, folder_id) is None:
            raise NotFoundError("Target folder not found.")

        # Read once to validate size + compute checksum, then rewind for storage.
        header, checksum, size = stream_to_temp_with_limits(
            fileobj, content_type, settings.max_upload_size_bytes
        )
        # Prefer magic-byte detection so browser mislabels (image/jpg, empty,
        # octet-stream, charset parameters) don't reject legitimate media.
        content_type = resolve_upload_content_type(content_type, header)

        kind = AssetKind.from_content_type(content_type)
        width, height = (read_png_dimensions(header) if content_type == "image/png" else (None, None))

        asset_id = uuid.uuid4()
        storage_key = f"{workspace_id}/{asset_id}/{filename}"
        fileobj.seek(0)
        self.storage.save(storage_key, fileobj)

        asset = Asset(
            id=asset_id,
            workspace_id=workspace_id,
            folder_id=folder_id,
            name=name or filename,
            description=description,
            storage_key=storage_key,
            original_filename=filename,
            content_type=content_type,
            kind=kind,
            size_bytes=size,
            checksum_sha256=checksum,
            status=AssetStatus.READY,
            width=width,
            height=height,
            uploaded_by=user.id,
        )
        self.assets.add(asset)
        self._reindex(asset)
        return asset

    def _reindex(self, asset: Asset) -> None:
        """Populate the search vector on PostgreSQL (no-op on SQLite)."""
        if not settings.is_postgres:
            return
        from sqlalchemy import func, select

        vector = select(
            func.setweight(func.to_tsvector("english", func.coalesce(asset.name, "")), "A")
            .op("||")(func.setweight(func.to_tsvector("english", func.coalesce(asset.description, "")), "B"))
            .op("||")(func.setweight(func.to_tsvector("english", func.coalesce(asset.original_filename, "")), "C"))
        )
        asset.search_vector = self.db.execute(vector).scalar_one()
        self.db.flush()

    # --- Retrieval ----------------------------------------------------------
    def get(self, workspace_id: uuid.UUID, asset_id: uuid.UUID) -> Asset:
        asset = self.assets.get_scoped(workspace_id, asset_id)
        if asset is None:
            raise NotFoundError("Asset not found.")
        return asset

    def list(self, f: AssetFilter, *, offset: int, limit: int) -> tuple[list[Asset], int]:
        return self.assets.search(f, offset=offset, limit=limit)

    # --- Mutation -----------------------------------------------------------
    def update(
        self,
        asset: Asset,
        *,
        name: str | None,
        description: str | None,
        folder_id: uuid.UUID | None,
        folder_provided: bool,
    ) -> Asset:
        if name is not None:
            asset.name = name
        if description is not None:
            asset.description = description
        if folder_provided:
            if folder_id is not None and self.folders.get_scoped(asset.workspace_id, folder_id) is None:
                raise NotFoundError("Target folder not found.")
            asset.folder_id = folder_id
        self.db.flush()
        self._reindex(asset)
        return asset

    def set_tags(self, asset: Asset, tag_ids: list[uuid.UUID]) -> Asset:
        tags = self.tags.list_scoped(asset.workspace_id, tag_ids)
        found = {t.id for t in tags}
        missing = [str(t) for t in tag_ids if t not in found]
        if missing:
            raise NotFoundError(f"Unknown tag(s): {', '.join(missing)}")
        asset.tags = tags
        self.db.flush()
        return asset

    def delete(self, asset: Asset) -> None:
        with contextlib.suppress(Exception):  # storage cleanup is best-effort
            self.storage.delete(asset.storage_key)
        self.assets.delete(asset)

    # --- Signed access ------------------------------------------------------
    def signed_url(self, asset: Asset, expires_in: int | None = None) -> SignedUrlResponse:
        ttl = expires_in or settings.SIGNED_URL_EXPIRE_SECONDS
        # Prefer a native presigned URL (S3/CloudFront) when the backend offers one.
        native = self.storage.presigned_url(asset.storage_key, ttl)
        if native:
            expires_at = int(datetime.now(UTC).timestamp()) + ttl
            return SignedUrlResponse(url=native, expires_at=expires_at)

        expires_at = int(datetime.now(UTC).timestamp()) + ttl
        signature = sign_asset_url(str(asset.id), expires_at)
        path = f"{settings.API_V1_PREFIX}/assets/{asset.id}/download"
        url = f"{path}?expires={expires_at}&signature={signature}"
        return SignedUrlResponse(url=url, expires_at=expires_at)

    def open_stream(self, asset: Asset) -> BinaryIO:
        return self.storage.open(asset.storage_key)
