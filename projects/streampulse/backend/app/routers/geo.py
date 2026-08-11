"""Geographic breakdown endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedRange, date_range_params, get_current_user
from app.core.metrics import compute_geo
from app.models import User
from app.schemas import DateRange, GeoResponse

router = APIRouter(prefix="/api/geo", tags=["geo"])


@router.get("", response_model=GeoResponse)
def get_geo(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> GeoResponse:
    items = compute_geo(db, rng.start_dt, rng.end_dt, rng.video_id)
    return GeoResponse(range=DateRange(start=rng.start, end=rng.end), items=items)
