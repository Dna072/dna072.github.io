"""Share repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.share import Share
from app.repositories.base import BaseRepository


class ShareRepository(BaseRepository[Share]):
    model = Share

    def get_by_token(self, token: str) -> Share | None:
        stmt = select(Share).where(Share.token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_asset(self, asset_id: uuid.UUID) -> list[Share]:
        stmt = select(Share).where(Share.asset_id == asset_id).order_by(Share.created_at.desc())
        return list(self.db.execute(stmt).scalars())
