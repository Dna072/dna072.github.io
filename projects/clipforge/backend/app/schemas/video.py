from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.video import VideoStatus
from app.schemas.common import ORMModel


class Chapter(BaseModel):
    start: float = Field(ge=0, description="Chapter start time in seconds")
    title: str


class VideoMetadata(BaseModel):
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    frame_rate: float | None = None
    bitrate: int | None = None


class VideoRead(ORMModel):
    id: str
    project_id: str
    title: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: VideoStatus
    error_message: str | None

    duration_seconds: float | None
    width: int | None
    height: int | None
    codec: str | None
    frame_rate: float | None
    bitrate: int | None

    thumbnail_path: str | None
    audio_path: str | None

    transcript: str | None
    summary: str | None
    chapters: list[Chapter] | None
    tags: list[str] | None

    created_at: datetime
    updated_at: datetime


class VideoListItem(ORMModel):
    """Lightweight projection for library/list views."""

    id: str
    project_id: str
    title: str
    status: VideoStatus
    duration_seconds: float | None
    thumbnail_path: str | None
    tags: list[str] | None
    created_at: datetime


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
