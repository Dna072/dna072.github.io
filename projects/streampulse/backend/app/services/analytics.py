"""Analytics query service.

All functions build aggregate queries directly against the fact tables. We lean
on PostgreSQL for the heavy lifting (``date_trunc``, ``count(distinct)``,
conditional aggregation with ``FILTER``) so the API only ships small, already
reduced result sets to the client. Every query is bounded by an
``event_time`` range so the composite indexes on the fact tables are used.
"""

from datetime import date, datetime

from sqlalchemy import Float, and_, case, cast, distinct, func, select
from sqlalchemy.orm import Session

from app.models.analytics import ImpressionEvent, Video, ViewEvent
from app.schemas.analytics import (
    BreakdownResponse,
    BreakdownRow,
    FunnelResponse,
    FunnelStage,
    MetricDelta,
    OverviewMetrics,
    TimeSeriesPoint,
    TimeSeriesResponse,
    VideoPerformance,
    VideoPerformancePage,
)

# ISO country code -> display label for the common demo countries.
COUNTRY_LABELS = {
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "GH": "Ghana",
    "NG": "Nigeria",
    "IN": "India",
    "BR": "Brazil",
    "CA": "Canada",
    "JP": "Japan",
    "AU": "Australia",
    "ZA": "South Africa",
}


def _window(start: datetime, end: datetime):
    """Common WHERE clause: [start, end) on the view fact table."""
    return and_(ViewEvent.event_time >= start, ViewEvent.event_time < end)


def _delta_pct(current: float, previous: float | None) -> float | None:
    if previous is None:
        return None
    if previous == 0:
        return None if current == 0 else 100.0
    return round((current - previous) / previous * 100.0, 2)


# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
def _overview_raw(
    db: Session, start: datetime, end: datetime, video_id: int | None
) -> dict:
    engaged = case(
        (
            (ViewEvent.liked.is_(True))
            | (ViewEvent.commented.is_(True))
            | (ViewEvent.shared.is_(True)),
            1,
        ),
        else_=0,
    )
    completed = case((ViewEvent.quartile_reached == 4, 1), else_=0)

    stmt = select(
        func.count(ViewEvent.id).label("views"),
        func.count(distinct(ViewEvent.viewer_id)).label("unique_viewers"),
        func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
        func.coalesce(func.avg(cast(ViewEvent.watch_seconds, Float)), 0.0).label(
            "avg_duration"
        ),
        func.coalesce(func.avg(cast(engaged, Float)), 0.0).label("engagement_rate"),
        func.coalesce(func.avg(cast(completed, Float)), 0.0).label("completion_rate"),
    ).where(_window(start, end))
    if video_id is not None:
        stmt = stmt.where(ViewEvent.video_id == video_id)

    row = db.execute(stmt).one()
    return {
        "total_views": float(row.views),
        "unique_viewers": float(row.unique_viewers),
        "total_watch_hours": round(row.watch_seconds / 3600.0, 2),
        "avg_view_duration_seconds": round(float(row.avg_duration), 1),
        "engagement_rate": round(float(row.engagement_rate), 4),
        "completion_rate": round(float(row.completion_rate), 4),
    }


def get_overview(
    db: Session,
    start: datetime,
    end: datetime,
    prev_start: datetime,
    prev_end: datetime,
    compare: bool,
    video_id: int | None = None,
) -> OverviewMetrics:
    cur = _overview_raw(db, start, end, video_id)
    prev = _overview_raw(db, prev_start, prev_end, video_id) if compare else None

    def metric(key: str) -> MetricDelta:
        p = prev[key] if prev else None
        return MetricDelta(value=cur[key], previous=p, delta_pct=_delta_pct(cur[key], p))

    return OverviewMetrics(
        total_views=metric("total_views"),
        unique_viewers=metric("unique_viewers"),
        total_watch_hours=metric("total_watch_hours"),
        avg_view_duration_seconds=metric("avg_view_duration_seconds"),
        engagement_rate=metric("engagement_rate"),
        completion_rate=metric("completion_rate"),
        comparison_enabled=compare,
    )


# --------------------------------------------------------------------------- #
# Time series
# --------------------------------------------------------------------------- #
def _resolve_granularity(start: datetime, end: datetime, requested: str) -> str:
    if requested != "auto":
        return requested
    span_days = (end - start).days
    if span_days <= 31:
        return "day"
    if span_days <= 120:
        return "week"
    return "month"


def _timeseries_raw(
    db: Session, start: datetime, end: datetime, granularity: str, video_id: int | None
) -> list[TimeSeriesPoint]:
    bucket = func.date_trunc(granularity, ViewEvent.event_time).label("bucket")
    stmt = (
        select(
            bucket,
            func.count(ViewEvent.id).label("views"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
            func.count(distinct(ViewEvent.viewer_id)).label("unique_viewers"),
        )
        .where(_window(start, end))
        .group_by(bucket)
        .order_by(bucket)
    )
    if video_id is not None:
        stmt = stmt.where(ViewEvent.video_id == video_id)

    points: list[TimeSeriesPoint] = []
    for r in db.execute(stmt):
        b = r.bucket
        points.append(
            TimeSeriesPoint(
                bucket=b.date() if isinstance(b, datetime) else b,
                views=r.views,
                watch_hours=round(r.watch_seconds / 3600.0, 2),
                unique_viewers=r.unique_viewers,
            )
        )
    return points


def get_timeseries(
    db: Session,
    start: datetime,
    end: datetime,
    prev_start: datetime,
    prev_end: datetime,
    compare: bool,
    granularity: str = "auto",
    video_id: int | None = None,
) -> TimeSeriesResponse:
    gran = _resolve_granularity(start, end, granularity)
    points = _timeseries_raw(db, start, end, gran, video_id)
    prev_points = (
        _timeseries_raw(db, prev_start, prev_end, gran, video_id) if compare else None
    )
    return TimeSeriesResponse(
        granularity=gran, points=points, previous_points=prev_points
    )


# --------------------------------------------------------------------------- #
# Video performance
# --------------------------------------------------------------------------- #
def get_video_performance(
    db: Session,
    start: datetime,
    end: datetime,
    limit: int,
    offset: int,
    sort_by: str = "views",
    video_id: int | None = None,
    category: str | None = None,
) -> VideoPerformancePage:
    engaged = case(
        (
            (ViewEvent.liked.is_(True))
            | (ViewEvent.commented.is_(True))
            | (ViewEvent.shared.is_(True)),
            1,
        ),
        else_=0,
    )
    completed = case((ViewEvent.quartile_reached == 4, 1), else_=0)

    base = (
        select(
            Video.id.label("video_id"),
            Video.title,
            Video.category,
            func.count(ViewEvent.id).label("views"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
            func.coalesce(func.avg(cast(ViewEvent.watch_seconds, Float)), 0.0).label(
                "avg_duration"
            ),
            func.coalesce(func.avg(cast(engaged, Float)), 0.0).label("engagement_rate"),
            func.coalesce(func.avg(cast(completed, Float)), 0.0).label("completion_rate"),
        )
        .join(ViewEvent, ViewEvent.video_id == Video.id)
        .where(_window(start, end))
        .group_by(Video.id, Video.title, Video.category)
    )
    if video_id is not None:
        base = base.where(Video.id == video_id)
    if category is not None:
        base = base.where(Video.category == category)

    sort_map = {
        "views": func.count(ViewEvent.id),
        "watch_hours": func.sum(ViewEvent.watch_seconds),
        "engagement_rate": func.avg(cast(engaged, Float)),
        "completion_rate": func.avg(cast(completed, Float)),
    }
    order_col = sort_map.get(sort_by, func.count(ViewEvent.id))
    stmt = base.order_by(order_col.desc()).limit(limit).offset(offset)

    items = [
        VideoPerformance(
            video_id=r.video_id,
            title=r.title,
            category=r.category,
            views=r.views,
            watch_hours=round(r.watch_seconds / 3600.0, 2),
            avg_view_duration_seconds=round(float(r.avg_duration), 1),
            engagement_rate=round(float(r.engagement_rate), 4),
            completion_rate=round(float(r.completion_rate), 4),
        )
        for r in db.execute(stmt)
    ]

    # Total number of videos that had at least one view in the window.
    count_stmt = (
        select(func.count(distinct(ViewEvent.video_id)))
        .select_from(ViewEvent)
        .where(_window(start, end))
    )
    if video_id is not None:
        count_stmt = count_stmt.where(ViewEvent.video_id == video_id)
    if category is not None:
        count_stmt = count_stmt.join(Video, Video.id == ViewEvent.video_id).where(
            Video.category == category
        )
    total = db.execute(count_stmt).scalar_one()

    return VideoPerformancePage(
        items=items, total=total, limit=limit, offset=offset
    )


# --------------------------------------------------------------------------- #
# Breakdowns (geo / device)
# --------------------------------------------------------------------------- #
def get_breakdown(
    db: Session,
    dimension: str,
    start: datetime,
    end: datetime,
    video_id: int | None = None,
    limit: int = 50,
) -> BreakdownResponse:
    if dimension == "geo":
        col = ViewEvent.country_code
    elif dimension == "device":
        col = ViewEvent.device_type
    else:  # pragma: no cover - guarded by the route
        raise ValueError(f"Unknown dimension: {dimension}")

    stmt = (
        select(
            col.label("key"),
            func.count(ViewEvent.id).label("views"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
        )
        .where(_window(start, end))
        .group_by(col)
        .order_by(func.count(ViewEvent.id).desc())
        .limit(limit)
    )
    if video_id is not None:
        stmt = stmt.where(ViewEvent.video_id == video_id)

    rows = db.execute(stmt).all()

    # Share is relative to ALL views in the window, not just the (possibly
    # truncated) top rows we return.
    total_stmt = select(func.count(ViewEvent.id)).where(_window(start, end))
    if video_id is not None:
        total_stmt = total_stmt.where(ViewEvent.video_id == video_id)
    total = db.execute(total_stmt).scalar_one() or 1
    result = [
        BreakdownRow(
            key=r.key,
            label=COUNTRY_LABELS.get(r.key, r.key) if dimension == "geo" else r.key.title(),
            views=r.views,
            watch_hours=round(r.watch_seconds / 3600.0, 2),
            share=round(r.views / total, 4),
        )
        for r in rows
    ]
    return BreakdownResponse(dimension=dimension, rows=result)


# --------------------------------------------------------------------------- #
# Engagement funnel
# --------------------------------------------------------------------------- #
def get_funnel(
    db: Session,
    start: datetime,
    end: datetime,
    video_id: int | None = None,
) -> FunnelResponse:
    # Top of funnel: impressions.
    imp_stmt = select(func.count(ImpressionEvent.id)).where(
        and_(
            ImpressionEvent.event_time >= start,
            ImpressionEvent.event_time < end,
        )
    )
    if video_id is not None:
        imp_stmt = imp_stmt.where(ImpressionEvent.video_id == video_id)
    impressions = db.execute(imp_stmt).scalar_one()

    # Views + quartile retention in a single scan using conditional aggregation.
    q_stmt = select(
        func.count(ViewEvent.id).label("views"),
        func.coalesce(
            func.sum(case((ViewEvent.quartile_reached >= 1, 1), else_=0)), 0
        ).label("q25"),
        func.coalesce(
            func.sum(case((ViewEvent.quartile_reached >= 2, 1), else_=0)), 0
        ).label("q50"),
        func.coalesce(
            func.sum(case((ViewEvent.quartile_reached >= 3, 1), else_=0)), 0
        ).label("q75"),
        func.coalesce(
            func.sum(case((ViewEvent.quartile_reached >= 4, 1), else_=0)), 0
        ).label("q100"),
    ).where(_window(start, end))
    if video_id is not None:
        q_stmt = q_stmt.where(ViewEvent.video_id == video_id)
    r = db.execute(q_stmt).one()

    top = impressions or 1
    ordered = [
        ("Impressions", impressions),
        ("Views", r.views),
        ("Watched 25%", r.q25),
        ("Watched 50%", r.q50),
        ("Watched 75%", r.q75),
        ("Completed", r.q100),
    ]
    stages = [
        FunnelStage(stage=name, count=count, pct_of_top=round(count / top, 4))
        for name, count in ordered
    ]
    return FunnelResponse(stages=stages)


# --------------------------------------------------------------------------- #
# Catalog helpers
# --------------------------------------------------------------------------- #
def list_categories(db: Session) -> list[str]:
    rows = db.execute(select(distinct(Video.category)).order_by(Video.category)).all()
    return [r[0] for r in rows]


def data_bounds(db: Session) -> dict[str, date | None]:
    """Earliest/latest event timestamps — used by the UI to seed the date picker."""
    row = db.execute(
        select(func.min(ViewEvent.event_time), func.max(ViewEvent.event_time))
    ).one()
    return {
        "min_date": row[0].date() if row[0] else None,
        "max_date": row[1].date() if row[1] else None,
    }
