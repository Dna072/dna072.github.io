from __future__ import annotations

from sqlalchemy import select

from app.models.project import Project
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    def list_for_user(self, user_id: str) -> list[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_membership(self, workspace_id: str, user_id: str) -> WorkspaceMember | None:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def slug_exists(self, slug: str) -> bool:
        return self.db.scalar(select(Workspace.id).where(Workspace.slug == slug)) is not None


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def list_for_workspace(self, workspace_id: str) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
