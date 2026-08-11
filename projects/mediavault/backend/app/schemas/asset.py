import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetStatus
from app.schemas.tag import TagRead


class AssetUpdate(BaseModel):
    filename: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    folder_id: uuid.UUID | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    owner_id: uuid.UUID | None
    filename: str
    original_filename: str
    description: str | None
    content_type: str
    size_bytes: int
    status: AssetStatus
    duration_seconds: float | None
    width: int | None
    height: int | None
    checksum_sha256: str | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = []


class AssetSearchResult(AssetRead):
    rank: float | None = None


class SignedUrlResponse(BaseModel):
    url: str
    expires_at: datetime
