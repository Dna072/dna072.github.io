"""Share-link management endpoints (nested under a workspace asset)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import DbSession, WorkspaceCtx
from app.models.enums import Role
from app.schemas.common import Message
from app.schemas.share import ShareCreate, ShareRead
from app.services.share import ShareService

router = APIRouter(prefix="/workspaces/{workspace_id}/assets/{asset_id}/shares", tags=["shares"])


@router.get("", response_model=list[ShareRead])
def list_shares(asset_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> list[ShareRead]:
    service = ShareService(db)
    # Ensure the asset belongs to this workspace before listing.
    service.assets.get_scoped(ctx.workspace.id, asset_id)
    return [ShareRead.model_validate(s) for s in service.list_for_asset(asset_id)]


@router.post("", response_model=ShareRead, status_code=status.HTTP_201_CREATED)
def create_share(
    asset_id: uuid.UUID, payload: ShareCreate, ctx: WorkspaceCtx, db: DbSession
) -> ShareRead:
    ctx.require(Role.MEMBER)
    share = ShareService(db).create(
        ctx.workspace.id,
        asset_id,
        ctx.user.id,
        expires_in_seconds=payload.expires_in_seconds,
        max_downloads=payload.max_downloads,
        allow_download=payload.allow_download,
    )
    db.commit()
    db.refresh(share)
    return ShareRead.model_validate(share)


@router.delete("/{share_id}", response_model=Message)
def revoke_share(
    asset_id: uuid.UUID, share_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession
) -> Message:
    ctx.require(Role.MEMBER)
    ShareService(db).revoke(ctx.workspace.id, share_id)
    db.commit()
    return Message(detail="Share revoked.")
