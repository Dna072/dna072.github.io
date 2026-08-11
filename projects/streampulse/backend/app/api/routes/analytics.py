"""Analytics API endpoints.

Every endpoint requires authentication and accepts a shared date-range /
comparison filter (see :func:`app.api.deps.get_date_range`) plus an optional
``video_id`` filter. Chart data is always computed server-side from the fact
tables — the frontend never hardcodes series.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DateRange, get_current_user, get_date_range
from app.db.session import get_db
from app.models.analytics import Video
from app.models.user import User
from app.schemas.analytics import (
    BreakdownResponse,
    FunnelResponse,
    OverviewMetrics,
    TimeSeriesResponse,
    VideoOut,
    VideoPerformancePage,
)
from app.services import analytics as svc

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/overview", response_model=OverviewMetrics, summary="Headline KPI metrics")
def overview(
    dr: DateRange = Depends(get_date_range),
    video_id: int | None = Query(None, description="Restrict to a single video."),
    db: Session = Depends(get_db),
) -> OverviewMetrics:
    return svc.get_overview(
        db, dr.start, dr.end, dr.prev_start, dr.prev_end, dr.compare, video_id
    )


@router.get("/timeseries", response_model=TimeSeriesResponse, summary="Views over time")
def timeseries(
    dr: DateRange = Depends(get_date_range),
    granularity: str = Query("auto", pattern="^(auto|day|week|month)$"),
    video_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> TimeSeriesResponse:
    return svc.get_timeseries(
        db,
        dr.start,
        dr.end,
        dr.prev_start,
        dr.prev_end,
        dr.compare,
        granularity,
        video_id,
    )


@router.get(
    "/videos",
    response_model=VideoPerformancePage,
    summary="Per-video performance (paginated, sortable)",
)
def video_performance(
    dr: DateRange = Depends(get_date_range),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query(
        "views", pattern="^(views|watch_hours|engagement_rate|completion_rate)$"
    ),
    video_id: int | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
) -> VideoPerformancePage:
    return svc.get_video_performance(
        db, dr.start, dr.end, limit, offset, sort_by, video_id, category
    )


@router.get(
    "/audience/geo",
    response_model=BreakdownResponse,
    summary="Views broken down by country",
)
def audience_geo(
    dr: DateRange = Depends(get_date_range),
    video_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=250),
    db: Session = Depends(get_db),
) -> BreakdownResponse:
    return svc.get_breakdown(db, "geo", dr.start, dr.end, video_id, limit)


@router.get(
    "/audience/device",
    response_model=BreakdownResponse,
    summary="Views broken down by device type",
)
def audience_device(
    dr: DateRange = Depends(get_date_range),
    video_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> BreakdownResponse:
    return svc.get_breakdown(db, "device", dr.start, dr.end, video_id)


@router.get(
    "/funnel",
    response_model=FunnelResponse,
    summary="Engagement funnel: impressions → views → retention → completion",
)
def funnel(
    dr: DateRange = Depends(get_date_range),
    video_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> FunnelResponse:
    return svc.get_funnel(db, dr.start, dr.end, video_id)


# --------------------------------------------------------------------------- #
# Catalog / metadata (used to populate filters in the UI)
# --------------------------------------------------------------------------- #
@router.get("/videos/catalog", response_model=list[VideoOut], summary="All videos")
def videos_catalog(db: Session = Depends(get_db)) -> list[Video]:
    return list(db.execute(select(Video).order_by(Video.published_at.desc())).scalars())


@router.get("/categories", response_model=list[str], summary="Distinct categories")
def categories(db: Session = Depends(get_db)) -> list[str]:
    return svc.list_categories(db)


@router.get("/meta/bounds", summary="Earliest/latest available data dates")
def bounds(
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return svc.data_bounds(db)
