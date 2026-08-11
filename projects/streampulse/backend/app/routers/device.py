"""Device-type breakdown endpoint (desktop / mobile / tablet / tv)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ResolvedRange, date_range_params, get_current_user
from pydantic import BaseModel

from app.core.metrics import compute_devices
from app.models import User
from app.schemas import DateRange, DeviceBreakdown

router = APIRouter(prefix="/api/device", tags=["device"])


class DeviceResponse(BaseModel):
    range: DateRange
    items: list[DeviceBreakdown]


@router.get("", response_model=DeviceResponse)
def get_devices(
    rng: ResolvedRange = Depends(date_range_params),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DeviceResponse:
    items = compute_devices(db, rng.start_dt, rng.end_dt, rng.video_id)
    return DeviceResponse(range=DateRange(start=rng.start, end=rng.end), items=items)
