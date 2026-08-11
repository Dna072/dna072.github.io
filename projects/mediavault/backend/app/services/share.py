"""Public share-link service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.share import Share
from app.repositories.asset import AssetRepository
from app.repositories.share import ShareRepository
from app.utils.text import random_token


class ShareService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shares = ShareRepository(db)
        self.assets = AssetRepository(db)

    def create(
        self,
        workspace_id: uuid.UUID,
        asset_id: uuid.UUID,
        created_by: uuid.UUID,
        *,
        expires_in_seconds: int | None,
        max_downloads: int | None,
        allow_download: bool,
    ) -> Share:
        asset = self.assets.get_scoped(workspace_id, asset_id)
        if asset is None:
            raise NotFoundError("Asset not found.")
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_in_seconds)
            if expires_in_seconds
            else None
        )
        share = Share(
            asset_id=asset_id,
            token=random_token(24),
            created_by=created_by,
            expires_at=expires_at,
            max_downloads=max_downloads,
            allow_download=allow_download,
        )
        return self.shares.add(share)

    def list_for_asset(self, asset_id: uuid.UUID) -> list[Share]:
        return self.shares.list_for_asset(asset_id)

    def revoke(self, workspace_id: uuid.UUID, share_id: uuid.UUID) -> None:
        share = self.shares.get(share_id)
        if share is None:
            raise NotFoundError("Share not found.")
        asset = self.assets.get_scoped(workspace_id, share.asset_id)
        if asset is None:
            raise NotFoundError("Share not found.")
        share.revoked = True
        self.db.flush()

    def resolve_public(self, token: str) -> tuple[Share, Asset]:
        share = self.shares.get_by_token(token)
        if share is None or share.revoked:
            raise NotFoundError("Share link not found.")
        if share.expires_at is not None:
            expires = share.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires < datetime.now(UTC):
                raise PermissionDeniedError("This share link has expired.")
        if share.max_downloads is not None and share.download_count >= share.max_downloads:
            raise PermissionDeniedError("This share link has reached its download limit.")
        asset = self.assets.get(share.asset_id)
        if asset is None:
            raise NotFoundError("Shared asset no longer exists.")
        return share, asset

    def register_download(self, share: Share) -> None:
        share.download_count += 1
        self.db.flush()


from app.models.asset import Asset  # noqa: E402  (type only, avoids cycle)
