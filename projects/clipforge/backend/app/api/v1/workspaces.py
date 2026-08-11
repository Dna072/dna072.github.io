from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.workspace import (
    ProjectCreate,
    ProjectRead,
    WorkspaceCreate,
    WorkspaceRead,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(current_user: CurrentUser, db: DbSession) -> list[WorkspaceRead]:
    items = WorkspaceService(db).list_workspaces(current_user.id)
    return [WorkspaceRead.model_validate(w) for w in items]


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    data: WorkspaceCreate, current_user: CurrentUser, db: DbSession
) -> WorkspaceRead:
    workspace = WorkspaceService(db).create_workspace(current_user.id, data)
    return WorkspaceRead.model_validate(workspace)


@router.get("/{workspace_id}/projects", response_model=list[ProjectRead])
def list_projects(
    workspace_id: str, current_user: CurrentUser, db: DbSession
) -> list[ProjectRead]:
    items = WorkspaceService(db).list_projects(workspace_id, current_user.id)
    return [ProjectRead.model_validate(p) for p in items]


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    workspace_id: str, data: ProjectCreate, current_user: CurrentUser, db: DbSession
) -> ProjectRead:
    project = WorkspaceService(db).create_project(workspace_id, current_user.id, data)
    return ProjectRead.model_validate(project)
