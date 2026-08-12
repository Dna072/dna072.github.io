"""Asset management endpoints (nested under a workspace)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.deps import DbSession, Pagination, WorkspaceCtx
from app.models.enums import AssetKind, Role
from app.repositories.asset import AssetFilter
from app.schemas.asset import AssetRead, AssetTagsUpdate, AssetUpdate, SignedUrlResponse
from app.schemas.common import Message, Page
from app.services.asset import AssetService
from app.services.folder import FolderService

router = APIRouter(prefix="/workspaces/{workspace_id}/assets", tags=["assets"])


@router.get("", response_model=Page[AssetRead])
def list_assets(
    ctx: WorkspaceCtx,
    db: DbSession,
    pagination: Pagination,
    folder_id: Annotated[uuid.UUID | None, Query()] = None,
    include_subfolders: Annotated[bool, Query()] = False,
    kind: Annotated[AssetKind | None, Query()] = None,
    tag_ids: Annotated[list[uuid.UUID] | None, Query()] = None,
    q: Annotated[str | None, Query(description="Full-text query")] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[AssetRead]:
    subfolder_ids: list[uuid.UUID] = []
    if folder_id is not None and include_subfolders:
        subfolder_ids = FolderService(db).descendant_ids(ctx.workspace.id, folder_id)

    f = AssetFilter(
        workspace_id=ctx.workspace.id,
        folder_id=folder_id,
        include_subfolders=include_subfolders,
        subfolder_ids=subfolder_ids,
        kind=kind,
        tag_ids=tag_ids or [],
        query=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    items, total = AssetService(db).list(f, offset=pagination.offset, limit=pagination.page_size)
    return Page[AssetRead].build(
        [AssetRead.model_validate(a) for a in items],
        total,
        pagination.page,
        pagination.page_size,
    )


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def upload_asset(
    ctx: WorkspaceCtx,
    db: DbSession,
    file: Annotated[UploadFile, File()],
    name: Annotated[str | None, Form()] = None,
    description: Annotated[str, Form()] = "",
    folder_id: Annotated[uuid.UUID | None, Form()] = None,
) -> AssetRead:
    ctx.require(Role.MEMBER)
    asset = AssetService(db).upload(
        ctx.workspace.id,
        ctx.user,
        fileobj=file.file,
        filename=file.filename or "upload.bin",
        # Browsers often omit or mislabel Content-Type; the service normalizes
        # and re-detects from magic bytes after reading the stream.
        content_type=file.content_type or "application/octet-stream",
        name=name,
        description=description,
        folder_id=folder_id,
    )
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> AssetRead:
    asset = AssetService(db).get(ctx.workspace.id, asset_id)
    return AssetRead.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: uuid.UUID, payload: AssetUpdate, ctx: WorkspaceCtx, db: DbSession
) -> AssetRead:
    ctx.require(Role.MEMBER)
    service = AssetService(db)
    asset = service.get(ctx.workspace.id, asset_id)
    asset = service.update(
        asset,
        name=payload.name,
        description=payload.description,
        folder_id=payload.folder_id,
        folder_provided="folder_id" in payload.model_fields_set,
    )
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.put("/{asset_id}/tags", response_model=AssetRead)
def set_asset_tags(
    asset_id: uuid.UUID, payload: AssetTagsUpdate, ctx: WorkspaceCtx, db: DbSession
) -> AssetRead:
    ctx.require(Role.MEMBER)
    service = AssetService(db)
    asset = service.get(ctx.workspace.id, asset_id)
    asset = service.set_tags(asset, payload.tag_ids)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.get("/{asset_id}/signed-url", response_model=SignedUrlResponse)
def get_signed_url(
    asset_id: uuid.UUID,
    ctx: WorkspaceCtx,
    db: DbSession,
    expires_in: Annotated[int | None, Query(ge=60, le=86400)] = None,
) -> SignedUrlResponse:
    service = AssetService(db)
    asset = service.get(ctx.workspace.id, asset_id)
    return service.signed_url(asset, expires_in)


@router.delete("/{asset_id}", response_model=Message)
def delete_asset(asset_id: uuid.UUID, ctx: WorkspaceCtx, db: DbSession) -> Message:
    ctx.require(Role.MEMBER)
    service = AssetService(db)
    asset = service.get(ctx.workspace.id, asset_id)
    service.delete(asset)
    db.commit()
    return Message(detail="Asset deleted.")
