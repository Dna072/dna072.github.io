"""Workspace service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.utils.text import slugify


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WorkspaceRepository(db)

    def _unique_slug(self, name: str, owner_id: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while self.repo.slug_exists(slug, owner_id):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def create(self, user: User, payload: WorkspaceCreate) -> Workspace:
        workspace = Workspace(
            name=payload.name,
            description=payload.description,
            slug=self._unique_slug(payload.name, user.id),
            owner_id=user.id,
        )
        self.repo.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def list(self, user: User) -> list[Workspace]:
        return self.repo.list_for_owner(user.id)

    def get(self, user: User, workspace_id: str) -> Workspace:
        workspace = self.repo.get_for_owner(workspace_id, user.id)
        if not workspace:
            raise NotFoundError("Workspace not found.")
        return workspace

    def update(
        self, user: User, workspace_id: str, payload: WorkspaceUpdate
    ) -> Workspace:
        workspace = self.get(user, workspace_id)
        if payload.name is not None:
            workspace.name = payload.name
        if payload.description is not None:
            workspace.description = payload.description
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def delete(self, user: User, workspace_id: str) -> None:
        workspace = self.get(user, workspace_id)
        self.repo.delete(workspace)
        self.db.commit()

    def video_count(self, workspace_id: str) -> int:
        return self.repo.video_count(workspace_id)

    def ensure_default_workspace(self, user: User) -> Workspace:
        """Return the user's first workspace, creating one if none exist."""
        existing = self.repo.list_for_owner(user.id)
        if existing:
            return existing[0]
        return self.create(user, WorkspaceCreate(name="My Workspace"))
