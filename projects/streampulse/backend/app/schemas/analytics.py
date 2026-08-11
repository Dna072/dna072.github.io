"""Analytics response/request schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Shared
# --------------------------------------------------------------------------- #
class MetricDelta(BaseModel):
    """A metric value plus its comparison against the previous period."""

    value: float
    previous: float | None = None
    delta_pct: float | None = Field(
        default=None,
        description="Percentage change vs previous period; null when comparison off.",
    )


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    duration_seconds: int
    published_at: datetime
    thumbnail_url: str | None = None


# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
class OverviewMetrics(BaseModel):
    total_views: MetricDelta
    unique_viewers: MetricDelta
    total_watch_hours: MetricDelta
    avg_view_duration_seconds: MetricDelta
    engagement_rate: MetricDelta = Field(
        description="Share of views with a like, comment or share (0..1)."
    )
    completion_rate: MetricDelta = Field(
        description="Share of views that reached 100% (0..1)."
    )
    comparison_enabled: bool


# --------------------------------------------------------------------------- #
# Time series
# --------------------------------------------------------------------------- #
class TimeSeriesPoint(BaseModel):
    bucket: date
    views: int
    watch_hours: float
    unique_viewers: int


class TimeSeriesResponse(BaseModel):
    granularity: str
    points: list[TimeSeriesPoint]
    previous_points: list[TimeSeriesPoint] | None = None


# --------------------------------------------------------------------------- #
# Video performance
# --------------------------------------------------------------------------- #
class VideoPerformance(BaseModel):
    video_id: int
    title: str
    category: str
    views: int
    watch_hours: float
    avg_view_duration_seconds: float
    engagement_rate: float
    completion_rate: float


class VideoPerformancePage(BaseModel):
    items: list[VideoPerformance]
    total: int
    limit: int
    offset: int


# --------------------------------------------------------------------------- #
# Audience / breakdowns
# --------------------------------------------------------------------------- #
class BreakdownRow(BaseModel):
    key: str
    label: str
    views: int
    watch_hours: float
    share: float = Field(description="Fraction of total views in period (0..1).")


class BreakdownResponse(BaseModel):
    dimension: str
    rows: list[BreakdownRow]


# --------------------------------------------------------------------------- #
# Engagement funnel
# --------------------------------------------------------------------------- #
class FunnelStage(BaseModel):
    stage: str
    count: int
    pct_of_top: float = Field(description="Fraction relative to impressions (0..1).")


class FunnelResponse(BaseModel):
    stages: list[FunnelStage]
