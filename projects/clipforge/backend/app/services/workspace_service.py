"""Workspace & project business logic with membership authorization."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.workspace import ProjectRepository, WorkspaceRepository
from app.schemas.workspace import ProjectCreate, WorkspaceCreate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workspace"


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.projects = ProjectRepository(db)

    def list_workspaces(self, user_id: str) -> list[Workspace]:
        return self.workspaces.list_for_user(user_id)

    def create_workspace(self, user_id: str, data: WorkspaceCreate) -> Workspace:
        base_slug = _slugify(data.name)
        slug = base_slug
        suffix = 1
        while self.workspaces.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        workspace = Workspace(name=data.name, slug=slug, owner_id=user_id)
        self.workspaces.add(workspace)
        self.db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user_id, role="owner"))
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def require_membership(self, workspace_id: str, user_id: str) -> Workspace:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace not found")
        if self.workspaces.get_membership(workspace_id, user_id) is None:
            raise ForbiddenError("You do not have access to this workspace")
        return workspace

    def list_projects(self, workspace_id: str, user_id: str) -> list[Project]:
        self.require_membership(workspace_id, user_id)
        return self.projects.list_for_workspace(workspace_id)

    def create_project(self, workspace_id: str, user_id: str, data: ProjectCreate) -> Project:
        self.require_membership(workspace_id, user_id)
        project = Project(
            name=data.name, description=data.description, workspace_id=workspace_id
        )
        self.projects.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: str, user_id: str) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        self.require_membership(project.workspace_id, user_id)
        return project
