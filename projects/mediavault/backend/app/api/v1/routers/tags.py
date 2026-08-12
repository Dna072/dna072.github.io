"""Tag endpoints (nested under a workspace)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import DbSession, WorkspaceCtx
from app.models.enums import Role
from app.schemas.common import Message
from app.schemas.tag import TagCreate, TagRead, TagUpdate
from app.services.tag import TagService

router = APIRouter(prefix="/workspaces/{workspace_id}/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
def list_tags(ctx: WorkspaceCtx, db: DbSession) -> list[TagRead]:
    return [TagRead.model_validate(t) for t in TagService(db).list(ctx.workspace.id)]


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, ctx: WorkspaceCtx, db: DbSession) -> TagRead:
    ctx.require(Role.MEMBER)
    tag = TagService(db).create(ctx.workspace.id, payload.name, payload.color)
    db.commit()
    db.refresh(tag)
    return TagRead.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(tag_id: uuid.UUID, payload: TagUpdate, ctx: WorkspaceCtx, db: DbSession) -> TagRead:
    ctx.require(Role.MEMBER)
    service = TagService(db)
    tag = service.get(ctx.workspace.id, tag_id)
    tag = service.update(tag, payload.name, payload.color)
    db.commit()
    db.refresh(tag)
    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", response_model=Message)
def delete_tag(tag_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> Message:
    ctx.require(Role.MEMBER)
    service = TagService(db)
    tag = service.get(ctx.workspace.id, tag_id)
    service.delete(tag)
    db.commit()
    return Message(detail="Tag deleted.")
