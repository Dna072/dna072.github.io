"""Workspace endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Message
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspacePublic,
    WorkspaceUpdate,
    WorkspaceWithStats,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspacePublic, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate, current_user: CurrentUser, db: DbSession
) -> WorkspacePublic:
    workspace = WorkspaceService(db).create(current_user, payload)
    return WorkspacePublic.model_validate(workspace)


@router.get("", response_model=list[WorkspaceWithStats])
def list_workspaces(
    current_user: CurrentUser, db: DbSession
) -> list[WorkspaceWithStats]:
    service = WorkspaceService(db)
    result: list[WorkspaceWithStats] = []
    for workspace in service.list(current_user):
        stats = WorkspaceWithStats.model_validate(workspace)
        stats.video_count = service.video_count(workspace.id)
        result.append(stats)
    return result


@router.get("/{workspace_id}", response_model=WorkspaceWithStats)
def get_workspace(
    workspace_id: str, current_user: CurrentUser, db: DbSession
) -> WorkspaceWithStats:
    service = WorkspaceService(db)
    workspace = service.get(current_user, workspace_id)
    stats = WorkspaceWithStats.model_validate(workspace)
    stats.video_count = service.video_count(workspace.id)
    return stats


@router.patch("/{workspace_id}", response_model=WorkspacePublic)
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspacePublic:
    workspace = WorkspaceService(db).update(current_user, workspace_id, payload)
    return WorkspacePublic.model_validate(workspace)


@router.delete("/{workspace_id}", response_model=Message)
def delete_workspace(
    workspace_id: str, current_user: CurrentUser, db: DbSession
) -> Message:
    WorkspaceService(db).delete(current_user, workspace_id)
    return Message(message="Workspace deleted.")
