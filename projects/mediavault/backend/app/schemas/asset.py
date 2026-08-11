"""Asset schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssetKind, AssetStatus
from app.schemas.tag import TagRead


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=5000)
    folder_id: uuid.UUID | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    description: str
    original_filename: str
    content_type: str
    kind: AssetKind
    size_bytes: int
    status: AssetStatus
    width: int | None
    height: int | None
    duration_seconds: float | None
    checksum_sha256: str | None
    uploaded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = []


class SignedUrlResponse(BaseModel):
    url: str
    expires_at: int
    method: str = "GET"


class AssetTagsUpdate(BaseModel):
    tag_ids: list[uuid.UUID]
