"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------
class VideoRead(BaseModel):
    id: int
    title: str
    category: str
    duration_seconds: int
    thumbnail_url: str | None
    published_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Overview / KPIs
# ---------------------------------------------------------------------------
class KPISet(BaseModel):
    views: int
    unique_viewers: int
    watch_time_hours: float
    avg_watch_percent: float
    completion_rate: float
    likes: int
    comments: int
    shares: int
    engagement_rate: float


class KPIDelta(BaseModel):
    absolute: float
    percent: float | None


class OverviewResponse(BaseModel):
    range: "DateRange"
    current: KPISet
    previous: KPISet | None = None
    deltas: dict[str, KPIDelta] | None = None


class DateRange(BaseModel):
    start: date
    end: date
    compare_start: date | None = None
    compare_end: date | None = None


# ---------------------------------------------------------------------------
# Time series
# ---------------------------------------------------------------------------
class TimeSeriesPoint(BaseModel):
    date: date
    views: int
    unique_viewers: int
    watch_time_hours: float
    avg_watch_percent: float
    completion_rate: float


class TimeSeriesResponse(BaseModel):
    range: DateRange
    points: list[TimeSeriesPoint]
    compare_points: list[TimeSeriesPoint] | None = None


# ---------------------------------------------------------------------------
# Video performance
# ---------------------------------------------------------------------------
class VideoPerformance(BaseModel):
    video_id: int
    title: str
    category: str
    thumbnail_url: str | None
    published_at: datetime
    views: int
    unique_viewers: int
    watch_time_hours: float
    avg_watch_percent: float
    completion_rate: float
    likes: int
    comments: int
    shares: int


class VideoPerformanceResponse(BaseModel):
    range: DateRange
    total: int
    items: list[VideoPerformance]


class VideoDetailResponse(BaseModel):
    video: VideoRead
    range: DateRange
    metrics: KPISet


# ---------------------------------------------------------------------------
# Funnel
# ---------------------------------------------------------------------------
class FunnelStage(BaseModel):
    stage: str
    label: str
    count: int
    percent_of_plays: float


class FunnelResponse(BaseModel):
    range: DateRange
    video_id: int | None
    stages: list[FunnelStage]


# ---------------------------------------------------------------------------
# Audience
# ---------------------------------------------------------------------------
class DeviceBreakdown(BaseModel):
    device_type: str
    views: int
    watch_time_hours: float
    share_percent: float


class ReferrerBreakdown(BaseModel):
    referrer_source: str
    views: int
    share_percent: float


class AudienceResponse(BaseModel):
    range: DateRange
    devices: list[DeviceBreakdown]
    referrers: list[ReferrerBreakdown]


# ---------------------------------------------------------------------------
# Geo
# ---------------------------------------------------------------------------
class GeoBreakdown(BaseModel):
    country_code: str
    country_name: str
    views: int
    unique_viewers: int
    watch_time_hours: float
    share_percent: float


class GeoResponse(BaseModel):
    range: DateRange
    items: list[GeoBreakdown]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    database: str
