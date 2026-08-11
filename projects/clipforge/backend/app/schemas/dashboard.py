from __future__ import annotations

from pydantic import BaseModel

from app.schemas.video import VideoListItem


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardStats(BaseModel):
    total_videos: int
    total_projects: int
    total_duration_seconds: float
    total_storage_bytes: int
    status_breakdown: list[StatusCount]
    recent_videos: list[VideoListItem]
