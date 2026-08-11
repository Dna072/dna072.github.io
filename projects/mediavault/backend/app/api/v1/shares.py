import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.deps import WorkspaceContext, require_member
from app.db.session import get_db
from app.models.asset import Asset
from app.models.share import Share, SharePermission
from app.schemas.asset import AssetRead
from app.schemas.common import Message
from app.schemas.share import ShareCreate, SharePublicRead, ShareRead
from app.services.rbac import can_manage_resource
from app.services.storage import get_storage

router = APIRouter(tags=["shares"])


def _to_share_read(share: Share) -> ShareRead:
    is_active = share.revoked_at is None and (
        share.expires_at is None or share.expires_at > datetime.now(UTC)
    )
    data = ShareRead.model_validate(share)
    data.is_active = is_active
    return data


@router.post(
    "/workspaces/{workspace_id}/assets/{asset_id}/shares",
    response_model=ShareRead,
    status_code=status.HTTP_201_CREATED,
)
def create_share(
    asset_id: uuid.UUID,
    payload: ShareCreate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> ShareRead:
    asset = (
        db.query(Asset).filter(Asset.id == asset_id, Asset.workspace_id == ctx.workspace_id).first()
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if not can_manage_resource(ctx.role, asset.owner_id == ctx.user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot share this asset"
        )
    hours = payload.expires_in_hours
    if hours is None:
        hours = settings.SHARE_LINK_DEFAULT_EXPIRE_HOURS
    # A value of 0 means "no expiry" (a permanent link); anything positive
    # sets a concrete expiry timestamp.
    expires_at = datetime.now(UTC) + timedelta(hours=hours) if hours > 0 else None
    share = Share(
        asset_id=asset.id,
        created_by=ctx.user.id,
        permission=payload.permission,
        expires_at=expires_at,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return _to_share_read(share)


@router.get(
    "/workspaces/{workspace_id}/assets/{asset_id}/shares", response_model=list[ShareRead]
)
def list_shares(
    asset_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> list[ShareRead]:
    asset = (
        db.query(Asset).filter(Asset.id == asset_id, Asset.workspace_id == ctx.workspace_id).first()
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    shares = db.query(Share).filter(Share.asset_id == asset_id).order_by(
        Share.created_at.desc()
    ).all()
    return [_to_share_read(s) for s in shares]


@router.delete("/workspaces/{workspace_id}/shares/{share_id}", response_model=Message)
def revoke_share(
    share_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> Message:
    share = (
        db.query(Share)
        .join(Asset, Asset.id == Share.asset_id)
        .filter(Share.id == share_id, Asset.workspace_id == ctx.workspace_id)
        .first()
    )
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
    if not can_manage_resource(ctx.role, share.created_by == ctx.user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot revoke this share"
        )
    share.revoked_at = datetime.now(UTC)
    db.add(share)
    db.commit()
    return Message(message="Share revoked")


def _get_active_share_or_404(db: Session, token: str) -> Share:
    share = (
        db.query(Share)
        .options(selectinload(Share.asset).selectinload(Asset.tags))
        .filter(Share.token == token)
        .first()
    )
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
    if share.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link revoked")
    if share.expires_at is not None and share.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link expired")
    return share


@router.get("/shares/public/{token}", response_model=SharePublicRead)
def get_public_share(token: str, db: Session = Depends(get_db)) -> SharePublicRead:
    share = _get_active_share_or_404(db, token)
    download_url = None
    if share.permission == SharePermission.DOWNLOAD:
        download_url = f"{settings.API_V1_PREFIX}/shares/public/{token}/download"
    return SharePublicRead(
        asset=AssetRead.model_validate(share.asset),
        permission=share.permission,
        download_url=download_url,
    )


@router.get("/shares/public/{token}/download")
def download_public_share(token: str, db: Session = Depends(get_db)) -> StreamingResponse:
    share = _get_active_share_or_404(db, token)
    if share.permission != SharePermission.DOWNLOAD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This share link is view-only"
        )
    storage = get_storage()
    if not storage.exists(share.asset.storage_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing in storage")
    stream = storage.open_stream(share.asset.storage_key)
    return StreamingResponse(
        stream,
        media_type=share.asset.content_type,
        headers={"Content-Disposition": f'attachment; filename="{share.asset.filename}"'},
    )
