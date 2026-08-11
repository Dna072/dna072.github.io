"""Daily time-series endpoint powering the trend chart."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedRange, date_range_params, get_current_user
from app.core.metrics import compute_timeseries
from app.models import User
from app.schemas import DateRange, TimeSeriesResponse

router = APIRouter(prefix="/api/metrics", tags=["timeseries"])


@router.get("/timeseries", response_model=TimeSeriesResponse)
def get_timeseries(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TimeSeriesResponse:
    points = compute_timeseries(db, rng.start, rng.end, rng.start_dt, rng.end_dt, rng.video_id)

    compare_points = None
    if rng.compare and rng.compare_start and rng.compare_end and rng.compare_start_dt and rng.compare_end_dt:
        compare_points = compute_timeseries(
            db, rng.compare_start, rng.compare_end, rng.compare_start_dt, rng.compare_end_dt, rng.video_id
        )

    return TimeSeriesResponse(
        range=DateRange(
            start=rng.start,
            end=rng.end,
            compare_start=rng.compare_start,
            compare_end=rng.compare_end,
        ),
        points=points,
        compare_points=compare_points,
    )
