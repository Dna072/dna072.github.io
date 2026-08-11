"""Workspace and membership endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession, WorkspaceCtx
from app.schemas.common import Message
from app.schemas.workspace import (
    MemberInvite,
    MemberRoleUpdate,
    MembershipRead,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
    WorkspaceWithRole,
)
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceWithRole])
def list_workspaces(current_user: CurrentUser, db: DbSession) -> list[WorkspaceWithRole]:
    service = WorkspaceService(db)
    result = []
    for workspace, membership in service.list_for_user(current_user):
        base = WorkspaceRead.model_validate(workspace, from_attributes=True)
        result.append(WorkspaceWithRole(**base.model_dump(), role=membership.role))
    return result


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, current_user: CurrentUser, db: DbSession) -> WorkspaceRead:
    service = WorkspaceService(db)
    workspace = service.create(current_user, payload.name, payload.slug, payload.description)
    db.commit()
    db.refresh(workspace)
    return WorkspaceRead.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceWithRole)
def get_workspace(ctx: WorkspaceCtx) -> WorkspaceWithRole:
    base = WorkspaceRead.model_validate(ctx.workspace, from_attributes=True)
    return WorkspaceWithRole(**base.model_dump(), role=ctx.role)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(payload: WorkspaceUpdate, ctx: WorkspaceCtx, db: DbSession) -> WorkspaceRead:
    ctx.require_admin()
    service = WorkspaceService(db)
    workspace = service.update(ctx.workspace, payload.name, payload.description)
    db.commit()
    db.refresh(workspace)
    return WorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}", response_model=Message)
def delete_workspace(ctx: WorkspaceCtx, db: DbSession) -> Message:
    ctx.require_admin()
    WorkspaceService(db).delete(ctx.workspace)
    db.commit()
    return Message(detail="Workspace deleted.")


# --- Membership -------------------------------------------------------------
@router.get("/{workspace_id}/members", response_model=list[MembershipRead])
def list_members(ctx: WorkspaceCtx, db: DbSession) -> list[MembershipRead]:
    members = WorkspaceService(db).list_members(ctx.workspace.id)
    return [MembershipRead.model_validate(m, from_attributes=True) for m in members]


@router.post(
    "/{workspace_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(payload: MemberInvite, ctx: WorkspaceCtx, db: DbSession) -> MembershipRead:
    ctx.require_admin()
    service = WorkspaceService(db)
    membership = service.add_member(ctx.workspace, payload.email, payload.role)
    db.commit()
    db.refresh(membership)
    return MembershipRead.model_validate(membership, from_attributes=True)


@router.patch("/{workspace_id}/members/{membership_id}", response_model=MembershipRead)
def update_member_role(
    membership_id: uuid.UUID, payload: MemberRoleUpdate, ctx: WorkspaceCtx, db: DbSession
) -> MembershipRead:
    ctx.require_admin()
    service = WorkspaceService(db)
    membership = service.update_member_role(ctx.workspace, membership_id, payload.role)
    db.commit()
    db.refresh(membership)
    return MembershipRead.model_validate(membership, from_attributes=True)


@router.delete("/{workspace_id}/members/{membership_id}", response_model=Message)
def remove_member(membership_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> Message:
    ctx.require_admin()
    WorkspaceService(db).remove_member(ctx.workspace, membership_id)
    db.commit()
    return Message(detail="Member removed.")
