import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.share import SharePermission
from app.schemas.asset import AssetRead


class ShareCreate(BaseModel):
    permission: SharePermission = SharePermission.VIEW
    # None -> use the server default expiry window. 0 -> never expires.
    expires_in_hours: int | None = Field(default=None, ge=0, le=24 * 365)


class ShareRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    created_by: uuid.UUID
    token: str
    permission: SharePermission
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    is_active: bool = True


class SharePublicRead(BaseModel):
    asset: AssetRead
    permission: SharePermission
    download_url: str | None = None
