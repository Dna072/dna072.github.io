"""Dashboard / analytics schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.video import VideoPublic


class StatusBreakdown(BaseModel):
    uploaded: int = 0
    queued: int = 0
    processing: int = 0
    ready: int = 0
    failed: int = 0


class DashboardStats(BaseModel):
    total_videos: int
    total_workspaces: int
    total_duration_seconds: float
    total_storage_bytes: int
    status_breakdown: StatusBreakdown
    active_jobs: int
    recent_videos: list[VideoPublic]
    top_tags: list[dict[str, int | str]]
