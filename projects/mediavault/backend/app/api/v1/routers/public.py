"""Unauthenticated endpoints: signed downloads and public share links."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession
from app.core.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.security import verify_asset_signature
from app.models.asset import Asset
from app.schemas.share import SharePublicView
from app.services.asset import AssetService
from app.services.share import ShareService

router = APIRouter(tags=["public"])


def _stream(asset: Asset, service: AssetService) -> StreamingResponse:
    stream = service.open_stream(asset)
    headers = {
        "Content-Disposition": f'inline; filename="{asset.original_filename}"',
        "Cache-Control": "private, max-age=300",
    }
    return StreamingResponse(stream, media_type=asset.content_type, headers=headers)


@router.get("/assets/{asset_id}/download", summary="Signed asset download")
def download_signed(
    asset_id: uuid.UUID,
    db: DbSession,
    expires: int = Query(...),
    signature: str = Query(...),
) -> StreamingResponse:
    """Stream an asset if the HMAC signature and expiry validate.

    This endpoint intentionally does not require a bearer token: authorization
    is carried entirely by the tamper-proof, time-limited signature, mirroring
    the S3/CloudFront signed-URL access model.
    """
    if not verify_asset_signature(str(asset_id), expires, signature):
        raise PermissionDeniedError("Invalid or expired signed URL.")
    service = AssetService(db)
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise NotFoundError("Asset not found.")
    return _stream(asset, service)


@router.get("/shares/{token}", response_model=SharePublicView, summary="Public share metadata")
def view_share(token: str, db: DbSession) -> SharePublicView:
    service = ShareService(db)
    share, asset = service.resolve_public(token)
    download_url = None
    if share.allow_download:
        signed = AssetService(db).signed_url(asset, settings.SIGNED_URL_EXPIRE_SECONDS)
        download_url = signed.url
    return SharePublicView(
        asset_id=asset.id,
        name=asset.name,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        kind=asset.kind.value,
        allow_download=share.allow_download,
        download_url=download_url,
    )


@router.get("/shares/{token}/download", summary="Download a shared asset")
def download_share(token: str, db: DbSession) -> StreamingResponse:
    service = ShareService(db)
    share, asset = service.resolve_public(token)
    if not share.allow_download:
        raise PermissionDeniedError("Downloads are disabled for this share link.")
    service.register_download(share)
    db.commit()
    return _stream(asset, AssetService(db))
