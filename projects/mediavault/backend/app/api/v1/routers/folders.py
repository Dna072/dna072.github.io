"""Folder hierarchy endpoints (nested under a workspace)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import DbSession, WorkspaceCtx
from app.models.enums import Role
from app.schemas.common import Message
from app.schemas.folder import Breadcrumb, FolderCreate, FolderRead, FolderTree, FolderUpdate
from app.services.folder import FolderService

router = APIRouter(prefix="/workspaces/{workspace_id}/folders", tags=["folders"])


@router.get("", response_model=list[FolderTree])
def list_folders(ctx: WorkspaceCtx, db: DbSession) -> list[FolderTree]:
    return FolderService(db).list_tree(ctx.workspace.id)


@router.post("", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(payload: FolderCreate, ctx: WorkspaceCtx, db: DbSession) -> FolderRead:
    ctx.require(Role.MEMBER)
    folder = FolderService(db).create(ctx.workspace.id, ctx.user, payload.name, payload.parent_id)
    db.commit()
    db.refresh(folder)
    return FolderRead.model_validate(folder)


@router.get("/{folder_id}/breadcrumbs", response_model=list[Breadcrumb])
def folder_breadcrumbs(folder_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> list[Breadcrumb]:
    return FolderService(db).breadcrumbs(ctx.workspace.id, folder_id)


@router.patch("/{folder_id}", response_model=FolderRead)
def update_folder(
    folder_id: uuid.UUID, payload: FolderUpdate, ctx: WorkspaceCtx, db: DbSession
) -> FolderRead:
    ctx.require(Role.MEMBER)
    service = FolderService(db)
    folder = service.get(ctx.workspace.id, folder_id)
    move = "parent_id" in payload.model_fields_set
    folder = service.rename_or_move(ctx.workspace.id, folder, payload.name, payload.parent_id, move)
    db.commit()
    db.refresh(folder)
    return FolderRead.model_validate(folder)


@router.delete("/{folder_id}", response_model=Message)
def delete_folder(folder_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> Message:
    ctx.require(Role.MEMBER)
    service = FolderService(db)
    folder = service.get(ctx.workspace.id, folder_id)
    service.delete(folder)
    db.commit()
    return Message(detail="Folder deleted.")
