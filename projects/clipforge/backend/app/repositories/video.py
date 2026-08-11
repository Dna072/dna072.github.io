from __future__ import annotations

from sqlalchemy import Select, func, or_, select

from app.models.project import Project
from app.models.video import Video, VideoStatus
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository


class VideoRepository(BaseRepository[Video]):
    model = Video

    def _user_scoped(self, user_id: str) -> Select:
        """Base query restricted to videos in workspaces the user belongs to."""
        return (
            select(Video)
            .join(Project, Project.id == Video.project_id)
            .join(Workspace, Workspace.id == Project.workspace_id)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
        )

    def get_for_user(self, video_id: str, user_id: str) -> Video | None:
        stmt = self._user_scoped(user_id).where(Video.id == video_id)
        return self.db.scalar(stmt)

    def search(
        self,
        user_id: str,
        *,
        query: str | None = None,
        status: VideoStatus | None = None,
        project_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Video], int]:
        stmt = self._user_scoped(user_id)

        if project_id:
            stmt = stmt.where(Video.project_id == project_id)
        if status:
            stmt = stmt.where(Video.status == status)
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Video.title).like(like),
                    func.lower(func.coalesce(Video.summary, "")).like(like),
                    func.lower(func.coalesce(Video.transcript, "")).like(like),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Video.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def recent_for_user(self, user_id: str, limit: int = 5) -> list[Video]:
        stmt = self._user_scoped(user_id).order_by(Video.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
