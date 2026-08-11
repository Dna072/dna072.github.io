"""Reusable FastAPI dependencies: DB session, current user, date-range params."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@dataclass
class ResolvedRange:
    start: date
    end: date
    start_dt: datetime
    end_dt: datetime
    compare_start: date | None
    compare_end: date | None
    compare_start_dt: datetime | None
    compare_end_dt: datetime | None
    video_id: int | None
    compare: bool


@dataclass
class ResolvedDateOnly:
    start: date
    end: date
    start_dt: datetime
    end_dt: datetime


def date_only_params(
    start: date | None = Query(None, description="Range start date (inclusive), defaults to 29 days ago"),
    end: date | None = Query(None, description="Range end date (inclusive), defaults to today"),
) -> ResolvedDateOnly:
    """Like date_range_params but without a video_id filter — for routes where
    the video is already identified by a path parameter (e.g. /videos/{video_id})."""
    today = datetime.utcnow().date()
    resolved_end = end or today
    resolved_start = start or (resolved_end - timedelta(days=29))
    if resolved_start > resolved_end:
        raise HTTPException(status_code=422, detail="start must be before or equal to end")
    return ResolvedDateOnly(
        start=resolved_start,
        end=resolved_end,
        start_dt=datetime.combine(resolved_start, time.min),
        end_dt=datetime.combine(resolved_end, time.max),
    )


def date_range_params(
    start: date | None = Query(None, description="Range start date (inclusive), defaults to 29 days ago"),
    end: date | None = Query(None, description="Range end date (inclusive), defaults to today"),
    video_id: int | None = Query(None, description="Restrict to a single video"),
    compare: bool = Query(False, description="Also compute the immediately preceding period of equal length"),
) -> ResolvedRange:
    today = datetime.utcnow().date()
    resolved_end = end or today
    resolved_start = start or (resolved_end - timedelta(days=29))

    if resolved_start > resolved_end:
        raise HTTPException(status_code=422, detail="start must be before or equal to end")

    span_days = (resolved_end - resolved_start).days + 1

    compare_start = compare_end = None
    compare_start_dt = compare_end_dt = None
    if compare:
        compare_end = resolved_start - timedelta(days=1)
        compare_start = compare_end - timedelta(days=span_days - 1)
        compare_start_dt = datetime.combine(compare_start, time.min)
        compare_end_dt = datetime.combine(compare_end, time.max)

    return ResolvedRange(
        start=resolved_start,
        end=resolved_end,
        start_dt=datetime.combine(resolved_start, time.min),
        end_dt=datetime.combine(resolved_end, time.max),
        compare_start=compare_start,
        compare_end=compare_end,
        compare_start_dt=compare_start_dt,
        compare_end_dt=compare_end_dt,
        video_id=video_id,
        compare=compare,
    )
