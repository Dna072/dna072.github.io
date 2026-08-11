"""Share-link schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShareCreate(BaseModel):
    expires_in_seconds: int | None = Field(default=None, ge=60, le=60 * 60 * 24 * 30)
    max_downloads: int | None = Field(default=None, ge=1, le=100000)
    allow_download: bool = True


class ShareRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    token: str
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    allow_download: bool
    revoked: bool
    created_at: datetime


class SharePublicView(BaseModel):
    asset_id: uuid.UUID
    name: str
    content_type: str
    size_bytes: int
    kind: str
    allow_download: bool
    download_url: str | None = None
