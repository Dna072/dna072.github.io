import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.deps import WorkspaceContext, require_member, require_viewer
from app.db.session import get_db
from app.models.asset import Asset, AssetStatus
from app.models.folder import Folder
from app.models.tag import Tag
from app.schemas.asset import AssetRead, AssetUpdate, SignedUrlResponse
from app.schemas.common import Message, Page
from app.services.rbac import can_manage_resource
from app.services.storage import (
    generate_signed_download_token,
    get_storage,
    verify_signed_download_token,
)

router = APIRouter(prefix="/assets", tags=["assets"])

ALLOWED_CONTENT_PREFIXES = ("video/", "image/", "audio/")
SORTABLE_FIELDS = {
    "created_at": Asset.created_at,
    "updated_at": Asset.updated_at,
    "filename": Asset.filename,
    "size_bytes": Asset.size_bytes,
}


def _get_asset_or_404(db: Session, workspace_id: uuid.UUID, asset_id: uuid.UUID) -> Asset:
    asset = (
        db.query(Asset)
        .options(selectinload(Asset.tags))
        .filter(Asset.id == asset_id, Asset.workspace_id == workspace_id)
        .first()
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


def _assert_can_manage(ctx: WorkspaceContext, asset: Asset) -> None:
    is_owner = asset.owner_id == ctx.user.id
    if not can_manage_resource(ctx.role, is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this asset",
        )


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile,
    folder_id: uuid.UUID | None = None,
    description: str | None = None,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> AssetRead:
    if not file.content_type or not file.content_type.startswith(ALLOWED_CONTENT_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only video, image, and audio uploads are supported",
        )
    if folder_id is not None:
        folder = (
            db.query(Folder)
            .filter(Folder.id == folder_id, Folder.workspace_id == ctx.workspace_id)
            .first()
        )
        if folder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    storage = get_storage()
    key = storage.build_key(ctx.workspace_id, file.filename or "untitled")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size, checksum = storage.save(key, file.file)
    if size > max_bytes:
        storage.delete(key)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    if size == 0:
        storage.delete(key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )

    asset = Asset(
        workspace_id=ctx.workspace_id,
        folder_id=folder_id,
        owner_id=ctx.user.id,
        filename=file.filename or "untitled",
        original_filename=file.filename or "untitled",
        description=description,
        content_type=file.content_type,
        size_bytes=size,
        storage_key=key,
        checksum_sha256=checksum,
        status=AssetStatus.READY,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.get("", response_model=Page[AssetRead])
def list_assets(
    folder_id: uuid.UUID | None = Query(default=None),
    content_type: str | None = Query(default=None, description="Prefix match, e.g. 'video/'"),
    status_filter: AssetStatus | None = Query(default=None, alias="status"),
    tag: list[str] = Query(default=[]),
    owner_id: uuid.UUID | None = Query(default=None),
    sort_by: Literal["created_at", "updated_at", "filename", "size_bytes"] = Query(
        default="created_at"
    ),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> Page[AssetRead]:
    query = db.query(Asset).options(selectinload(Asset.tags)).filter(
        Asset.workspace_id == ctx.workspace_id
    )
    if folder_id is not None:
        query = query.filter(Asset.folder_id == folder_id)
    if content_type is not None:
        query = query.filter(Asset.content_type.like(f"{content_type}%"))
    if status_filter is not None:
        query = query.filter(Asset.status == status_filter)
    if owner_id is not None:
        query = query.filter(Asset.owner_id == owner_id)
    if tag:
        query = query.join(Asset.tags).filter(Tag.name.in_(tag)).distinct()

    total = query.count()
    order_col = SORTABLE_FIELDS[sort_by]
    order_expr = asc(order_col) if sort_dir == "asc" else desc(order_col)
    items = (
        query.order_by(order_expr).offset((page - 1) * page_size).limit(page_size).all()
    )
    return Page.create(
        items=[AssetRead.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> AssetRead:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    return AssetRead.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> AssetRead:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    _assert_can_manage(ctx, asset)
    if payload.filename is not None:
        asset.filename = payload.filename
    if payload.description is not None:
        asset.description = payload.description
    if "folder_id" in payload.model_fields_set:
        if payload.folder_id is not None:
            folder = (
                db.query(Folder)
                .filter(Folder.id == payload.folder_id, Folder.workspace_id == ctx.workspace_id)
                .first()
            )
            if folder is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
                )
        asset.folder_id = payload.folder_id
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.delete("/{asset_id}", response_model=Message)
def delete_asset(
    asset_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> Message:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    _assert_can_manage(ctx, asset)
    storage = get_storage()
    storage.delete(asset.storage_key)
    db.delete(asset)
    db.commit()
    return Message(message="Asset deleted")


@router.post("/{asset_id}/tags/{tag_id}", response_model=AssetRead)
def attach_tag(
    asset_id: uuid.UUID,
    tag_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> AssetRead:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    _assert_can_manage(ctx, asset)
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.workspace_id == ctx.workspace_id).first()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    if tag not in asset.tags:
        asset.tags.append(tag)
        db.add(asset)
        db.commit()
        db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.delete("/{asset_id}/tags/{tag_id}", response_model=AssetRead)
def detach_tag(
    asset_id: uuid.UUID,
    tag_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> AssetRead:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    _assert_can_manage(ctx, asset)
    asset.tags = [t for t in asset.tags if t.id != tag_id]
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.get("/{asset_id}/download-url", response_model=SignedUrlResponse)
def get_download_url(
    asset_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> SignedUrlResponse:
    asset = _get_asset_or_404(db, ctx.workspace_id, asset_id)
    token, expires_at = generate_signed_download_token(asset.id)
    url = f"{settings.API_V1_PREFIX}/workspaces/{ctx.workspace_id}/assets/download/{token}"
    return SignedUrlResponse(url=url, expires_at=expires_at)


@router.get("/download/{token}")
def download_by_token(
    workspace_id: uuid.UUID, token: str, db: Session = Depends(get_db)
) -> StreamingResponse:
    """Streams the underlying file for a previously-issued signed URL.

    Intentionally has no workspace-membership dependency: the signed token
    itself (HMAC'd, time-limited, scoped to one asset id) is the
    authorization, mirroring how S3 presigned URLs work. The `workspace_id`
    path segment exists only so the URL groups naturally under the asset's
    workspace; it is not re-validated here.
    """
    asset_id = verify_signed_download_token(token)
    if asset_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired download link"
        )
    asset = db.get(Asset, asset_id)
    if asset is None or asset.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    storage = get_storage()
    if not storage.exists(asset.storage_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing in storage")
    stream = storage.open_stream(asset.storage_key)
    return StreamingResponse(
        stream,
        media_type=asset.content_type,
        headers={"Content-Disposition": f'inline; filename="{asset.filename}"'},
    )
