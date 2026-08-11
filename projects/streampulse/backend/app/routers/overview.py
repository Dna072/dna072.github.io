"""Overview KPI endpoint: headline numbers with optional comparison period."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedRange, date_range_params, get_current_user
from app.core.metrics import compute_kpis
from app.models import User
from app.schemas import DateRange, KPIDelta, OverviewResponse

router = APIRouter(prefix="/api/metrics", tags=["overview"])


def _delta(current: float, previous: float) -> KPIDelta:
    absolute = round(current - previous, 2)
    percent = round((absolute / previous) * 100, 2) if previous else None
    return KPIDelta(absolute=absolute, percent=percent)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OverviewResponse:
    current = compute_kpis(db, rng.start_dt, rng.end_dt, rng.video_id)

    previous = None
    deltas = None
    if rng.compare and rng.compare_start_dt and rng.compare_end_dt:
        previous = compute_kpis(db, rng.compare_start_dt, rng.compare_end_dt, rng.video_id)
        deltas = {
            field: _delta(getattr(current, field), getattr(previous, field))
            for field in current.model_fields
        }

    return OverviewResponse(
        range=DateRange(
            start=rng.start,
            end=rng.end,
            compare_start=rng.compare_start,
            compare_end=rng.compare_end,
        ),
        current=current,
        previous=previous,
        deltas=deltas,
    )
