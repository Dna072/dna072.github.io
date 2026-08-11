"""Audience behaviour endpoints: engagement funnel and traffic sources."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedRange, date_range_params, get_current_user
from app.core.metrics import compute_devices, compute_funnel, compute_referrers
from app.models import User
from app.schemas import AudienceResponse, DateRange, FunnelResponse

router = APIRouter(prefix="/api/audience", tags=["audience"])


@router.get("/funnel", response_model=FunnelResponse)
def get_funnel(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FunnelResponse:
    stages = compute_funnel(db, rng.start_dt, rng.end_dt, rng.video_id)
    return FunnelResponse(
        range=DateRange(start=rng.start, end=rng.end),
        video_id=rng.video_id,
        stages=stages,
    )


@router.get("", response_model=AudienceResponse)
def get_audience(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AudienceResponse:
    devices = compute_devices(db, rng.start_dt, rng.end_dt, rng.video_id)
    referrers = compute_referrers(db, rng.start_dt, rng.end_dt, rng.video_id)
    return AudienceResponse(
        range=DateRange(start=rng.start, end=rng.end),
        devices=devices,
        referrers=referrers,
    )
