"""Workspace repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.video import Video
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    def list_for_owner(self, owner_id: str) -> list[Workspace]:
        stmt = (
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_for_owner(self, workspace_id: str, owner_id: str) -> Workspace | None:
        stmt = select(Workspace).where(
            Workspace.id == workspace_id, Workspace.owner_id == owner_id
        )
        return self.db.scalar(stmt)

    def video_count(self, workspace_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Video)
            .where(Video.workspace_id == workspace_id)
        )
        return int(self.db.scalar(stmt) or 0)

    def slug_exists(self, slug: str, owner_id: str) -> bool:
        stmt = select(Workspace.id).where(
            Workspace.slug == slug, Workspace.owner_id == owner_id
        )
        return self.db.scalar(stmt) is not None
