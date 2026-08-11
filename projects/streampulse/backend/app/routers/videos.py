"""Video catalogue, ranked performance table, and per-video detail."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedDateOnly, ResolvedRange, date_only_params, date_range_params, get_current_user
from app.core.metrics import compute_kpis, compute_video_performance
from app.models import User, Video
from app.schemas import DateRange, VideoDetailResponse, VideoPerformanceResponse, VideoRead

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("", response_model=list[VideoRead])
def list_videos(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[VideoRead]:
    """Full video catalogue, used to populate the video filter dropdown."""
    videos = db.query(Video).order_by(Video.published_at.desc()).all()
    return [VideoRead.model_validate(v) for v in videos]


@router.get("/performance", response_model=VideoPerformanceResponse)
def video_performance(
    sort: str = Query("views", description="views | watch_time_hours | avg_watch_percent | completion_rate | unique_viewers"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> VideoPerformanceResponse:
    total, items = compute_video_performance(
        db, rng.start_dt, rng.end_dt, sort=sort, descending=(order == "desc"), limit=limit, offset=offset
    )
    return VideoPerformanceResponse(
        range=DateRange(start=rng.start, end=rng.end),
        total=total,
        items=items,
    )


@router.get("/{video_id}", response_model=VideoDetailResponse)
def video_detail(
    video_id: int,
    rng: ResolvedDateOnly = Depends(date_only_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> VideoDetailResponse:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    metrics = compute_kpis(db, rng.start_dt, rng.end_dt, video_id)
    return VideoDetailResponse(
        video=VideoRead.model_validate(video),
        range=DateRange(start=rng.start, end=rng.end),
        metrics=metrics,
    )
