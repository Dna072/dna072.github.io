"""Video schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VideoStatus


class VideoCreate(BaseModel):
    """Metadata accompanying an upload (multipart form fields)."""

    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    tags: list[str] | None = None


class Chapter(BaseModel):
    title: str
    start: float
    end: float


class VideoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    title: str
    description: str | None
    status: VideoStatus
    original_filename: str
    content_type: str
    size_bytes: int
    duration_seconds: float | None
    width: int | None
    height: int | None
    thumbnail_path: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


class VideoDetail(VideoPublic):
    transcript: str | None
    summary: str | None
    chapters: list[dict[str, Any]] | None
    error_message: str | None


class VideoUploadResponse(BaseModel):
    video: VideoPublic
    job_id: str
