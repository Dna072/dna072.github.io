"""SQL aggregation helpers backing every analytics endpoint.

Keeping this logic centralised (rather than duplicated per router) means the
overview, time-series and video-performance endpoints all reuse the exact
same aggregation semantics for "views", "watch time", "completion rate", etc.
All heavy lifting (COUNT/SUM/AVG/GROUP BY) happens in PostgreSQL; the API
layer only shapes the already-aggregated rows into response schemas.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.reference_data import COUNTRY_NAME_BY_CODE, FUNNEL_STAGES
from app.models import EngagementEvent, EngagementType, Video, ViewEvent
from app.schemas import (
    DeviceBreakdown,
    FunnelStage,
    GeoBreakdown,
    KPISet,
    ReferrerBreakdown,
    TimeSeriesPoint,
    VideoPerformance,
)


def _view_filters(start_dt: datetime, end_dt: datetime, video_id: int | None):
    filters = [ViewEvent.occurred_at.between(start_dt, end_dt)]
    if video_id is not None:
        filters.append(ViewEvent.video_id == video_id)
    return filters


def _engagement_filters(start_dt: datetime, end_dt: datetime, video_id: int | None):
    filters = [EngagementEvent.occurred_at.between(start_dt, end_dt)]
    if video_id is not None:
        filters.append(EngagementEvent.video_id == video_id)
    return filters


def _engagement_counts(
    db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None
) -> dict[str, int]:
    rows = (
        db.query(EngagementEvent.event_type, func.count(EngagementEvent.id))
        .filter(*_engagement_filters(start_dt, end_dt, video_id))
        .group_by(EngagementEvent.event_type)
        .all()
    )
    return {event_type.value: count for event_type, count in rows}


def compute_kpis(db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None) -> KPISet:
    row = (
        db.query(
            func.count(ViewEvent.id).label("views"),
            func.count(func.distinct(ViewEvent.viewer_id)).label("unique_viewers"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
            func.coalesce(func.avg(ViewEvent.watch_percent), 0.0).label("avg_watch_percent"),
            func.coalesce(func.sum(case((ViewEvent.completed.is_(True), 1), else_=0)), 0).label(
                "completed"
            ),
        )
        .filter(*_view_filters(start_dt, end_dt, video_id))
        .one()
    )

    engagement = _engagement_counts(db, start_dt, end_dt, video_id)
    likes = engagement.get(EngagementType.like.value, 0)
    comments = engagement.get(EngagementType.comment.value, 0)
    shares = engagement.get(EngagementType.share.value, 0)

    views = row.views or 0
    completion_rate = (row.completed / views * 100) if views else 0.0
    engagement_rate = ((likes + comments + shares) / views * 100) if views else 0.0

    return KPISet(
        views=views,
        unique_viewers=row.unique_viewers or 0,
        watch_time_hours=round((row.watch_seconds or 0) / 3600, 2),
        avg_watch_percent=round(float(row.avg_watch_percent or 0), 2),
        completion_rate=round(completion_rate, 2),
        likes=likes,
        comments=comments,
        shares=shares,
        engagement_rate=round(engagement_rate, 2),
    )


def compute_timeseries(
    db: Session, start: date, end: date, start_dt: datetime, end_dt: datetime, video_id: int | None
) -> list[TimeSeriesPoint]:
    day_col = func.date(ViewEvent.occurred_at)
    rows = (
        db.query(
            day_col.label("day"),
            func.count(ViewEvent.id).label("views"),
            func.count(func.distinct(ViewEvent.viewer_id)).label("unique_viewers"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
            func.coalesce(func.avg(ViewEvent.watch_percent), 0.0).label("avg_watch_percent"),
            func.coalesce(func.sum(case((ViewEvent.completed.is_(True), 1), else_=0)), 0).label(
                "completed"
            ),
        )
        .filter(*_view_filters(start_dt, end_dt, video_id))
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )

    by_day = {row.day: row for row in rows}

    points: list[TimeSeriesPoint] = []
    cursor = start
    while cursor <= end:
        row = by_day.get(cursor)
        if row is None:
            points.append(
                TimeSeriesPoint(
                    date=cursor,
                    views=0,
                    unique_viewers=0,
                    watch_time_hours=0.0,
                    avg_watch_percent=0.0,
                    completion_rate=0.0,
                )
            )
        else:
            completion_rate = (row.completed / row.views * 100) if row.views else 0.0
            points.append(
                TimeSeriesPoint(
                    date=cursor,
                    views=row.views,
                    unique_viewers=row.unique_viewers,
                    watch_time_hours=round(row.watch_seconds / 3600, 2),
                    avg_watch_percent=round(float(row.avg_watch_percent or 0), 2),
                    completion_rate=round(completion_rate, 2),
                )
            )
        cursor += timedelta(days=1)
    return points


SORTABLE_FIELDS = {
    "views": "views",
    "watch_time_hours": "watch_seconds",
    "avg_watch_percent": "avg_watch_percent",
    "completion_rate": "completed",
    "unique_viewers": "unique_viewers",
}


def compute_video_performance(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
    sort: str,
    descending: bool,
    limit: int,
    offset: int,
) -> tuple[int, list[VideoPerformance]]:
    view_agg = (
        db.query(
            ViewEvent.video_id.label("video_id"),
            func.count(ViewEvent.id).label("views"),
            func.count(func.distinct(ViewEvent.viewer_id)).label("unique_viewers"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
            func.coalesce(func.avg(ViewEvent.watch_percent), 0.0).label("avg_watch_percent"),
            func.coalesce(func.sum(case((ViewEvent.completed.is_(True), 1), else_=0)), 0).label(
                "completed"
            ),
        )
        .filter(ViewEvent.occurred_at.between(start_dt, end_dt))
        .group_by(ViewEvent.video_id)
        .subquery()
    )

    engagement_agg = (
        db.query(
            EngagementEvent.video_id.label("video_id"),
            func.coalesce(
                func.sum(case((EngagementEvent.event_type == EngagementType.like, 1), else_=0)), 0
            ).label("likes"),
            func.coalesce(
                func.sum(case((EngagementEvent.event_type == EngagementType.comment, 1), else_=0)), 0
            ).label("comments"),
            func.coalesce(
                func.sum(case((EngagementEvent.event_type == EngagementType.share, 1), else_=0)), 0
            ).label("shares"),
        )
        .filter(EngagementEvent.occurred_at.between(start_dt, end_dt))
        .group_by(EngagementEvent.video_id)
        .subquery()
    )

    query = (
        db.query(
            Video.id,
            Video.title,
            Video.category,
            Video.thumbnail_url,
            Video.published_at,
            view_agg.c.views,
            view_agg.c.unique_viewers,
            view_agg.c.watch_seconds,
            view_agg.c.avg_watch_percent,
            view_agg.c.completed,
            func.coalesce(engagement_agg.c.likes, 0).label("likes"),
            func.coalesce(engagement_agg.c.comments, 0).label("comments"),
            func.coalesce(engagement_agg.c.shares, 0).label("shares"),
        )
        .join(view_agg, view_agg.c.video_id == Video.id)
        .outerjoin(engagement_agg, engagement_agg.c.video_id == Video.id)
    )

    total = query.count()

    sort_column_name = SORTABLE_FIELDS.get(sort, "views")
    sort_column = view_agg.c[sort_column_name]
    query = query.order_by(sort_column.desc() if descending else sort_column.asc())
    query = query.offset(offset).limit(limit)

    items: list[VideoPerformance] = []
    for row in query.all():
        completion_rate = (row.completed / row.views * 100) if row.views else 0.0
        items.append(
            VideoPerformance(
                video_id=row.id,
                title=row.title,
                category=row.category,
                thumbnail_url=row.thumbnail_url,
                published_at=row.published_at,
                views=row.views,
                unique_viewers=row.unique_viewers,
                watch_time_hours=round(row.watch_seconds / 3600, 2),
                avg_watch_percent=round(float(row.avg_watch_percent or 0), 2),
                completion_rate=round(completion_rate, 2),
                likes=row.likes,
                comments=row.comments,
                shares=row.shares,
            )
        )
    return total, items


def compute_funnel(
    db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None
) -> list[FunnelStage]:
    counts = _engagement_counts(db, start_dt, end_dt, video_id)
    play_count = counts.get("play", 0)
    stages: list[FunnelStage] = []
    for stage_key, label in FUNNEL_STAGES:
        count = counts.get(stage_key, 0)
        percent = (count / play_count * 100) if play_count else 0.0
        stages.append(FunnelStage(stage=stage_key, label=label, count=count, percent_of_plays=round(percent, 2)))
    return stages


def compute_devices(
    db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None
) -> list[DeviceBreakdown]:
    rows = (
        db.query(
            ViewEvent.device_type,
            func.count(ViewEvent.id).label("views"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
        )
        .filter(*_view_filters(start_dt, end_dt, video_id))
        .group_by(ViewEvent.device_type)
        .order_by(func.count(ViewEvent.id).desc())
        .all()
    )
    total_views = sum(r.views for r in rows) or 1
    return [
        DeviceBreakdown(
            device_type=device_type.value,
            views=views,
            watch_time_hours=round(watch_seconds / 3600, 2),
            share_percent=round(views / total_views * 100, 2),
        )
        for device_type, views, watch_seconds in rows
    ]


def compute_referrers(
    db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None
) -> list[ReferrerBreakdown]:
    rows = (
        db.query(ViewEvent.referrer_source, func.count(ViewEvent.id).label("views"))
        .filter(*_view_filters(start_dt, end_dt, video_id))
        .group_by(ViewEvent.referrer_source)
        .order_by(func.count(ViewEvent.id).desc())
        .all()
    )
    total_views = sum(r.views for r in rows) or 1
    return [
        ReferrerBreakdown(
            referrer_source=source,
            views=views,
            share_percent=round(views / total_views * 100, 2),
        )
        for source, views in rows
    ]


def compute_geo(db: Session, start_dt: datetime, end_dt: datetime, video_id: int | None) -> list[GeoBreakdown]:
    rows = (
        db.query(
            ViewEvent.country_code,
            func.count(ViewEvent.id).label("views"),
            func.count(func.distinct(ViewEvent.viewer_id)).label("unique_viewers"),
            func.coalesce(func.sum(ViewEvent.watch_seconds), 0).label("watch_seconds"),
        )
        .filter(*_view_filters(start_dt, end_dt, video_id))
        .group_by(ViewEvent.country_code)
        .order_by(func.count(ViewEvent.id).desc())
        .all()
    )
    total_views = sum(r.views for r in rows) or 1
    return [
        GeoBreakdown(
            country_code=code,
            country_name=COUNTRY_NAME_BY_CODE.get(code, code),
            views=views,
            unique_viewers=uniques,
            watch_time_hours=round(watch_seconds / 3600, 2),
            share_percent=round(views / total_views * 100, 2),
        )
        for code, views, uniques, watch_seconds in rows
    ]
