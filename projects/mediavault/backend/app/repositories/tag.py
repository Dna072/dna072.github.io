"""Tag repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    model = Tag

    def list_for_workspace(self, workspace_id: uuid.UUID) -> list[Tag]:
        stmt = select(Tag).where(Tag.workspace_id == workspace_id).order_by(Tag.name)
        return list(self.db.execute(stmt).scalars())

    def get_scoped(self, workspace_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.workspace_id == workspace_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Tag | None:
        stmt = select(Tag).where(
            Tag.workspace_id == workspace_id, func.lower(Tag.name) == name.lower()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_scoped(self, workspace_id: uuid.UUID, ids: list[uuid.UUID]) -> list[Tag]:
        if not ids:
            return []
        stmt = select(Tag).where(Tag.workspace_id == workspace_id, Tag.id.in_(ids))
        return list(self.db.execute(stmt).scalars())
