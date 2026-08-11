"""Video repository with search and filtering."""

from __future__ import annotations

from sqlalchemy import func, or_, select

from app.models.enums import VideoStatus
from app.models.video import Video
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class VideoRepository(BaseRepository[Video]):
    model = Video

    def _owner_scoped(self, owner_id: str):
        """Base select joined to workspaces to enforce ownership."""
        return (
            select(Video)
            .join(Workspace, Video.workspace_id == Workspace.id)
            .where(Workspace.owner_id == owner_id)
        )

    def get_for_owner(self, video_id: str, owner_id: str) -> Video | None:
        stmt = self._owner_scoped(owner_id).where(Video.id == video_id)
        return self.db.scalar(stmt)

    def search(
        self,
        owner_id: str,
        *,
        query: str | None = None,
        workspace_id: str | None = None,
        status: VideoStatus | None = None,
        tag: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Video], int]:
        stmt = self._owner_scoped(owner_id)

        if workspace_id:
            stmt = stmt.where(Video.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(Video.status == status)
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Video.title).like(like),
                    func.lower(func.coalesce(Video.description, "")).like(like),
                    func.lower(func.coalesce(Video.summary, "")).like(like),
                    func.lower(func.coalesce(Video.transcript, "")).like(like),
                )
            )

        # Count before applying pagination.
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = stmt.order_by(Video.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.scalars(stmt).all())

        # Tag filtering is applied in Python because JSON containment differs
        # across SQLite/Postgres; datasets per user are small in this app.
        if tag:
            items = [v for v in items if v.tags and tag in v.tags]

        return items, total

    def recent_for_owner(self, owner_id: str, limit: int = 5) -> list[Video]:
        stmt = (
            self._owner_scoped(owner_id)
            .order_by(Video.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def all_for_owner(self, owner_id: str) -> list[Video]:
        return list(self.db.scalars(self._owner_scoped(owner_id)).all())
