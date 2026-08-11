"""Shared FastAPI dependencies."""

from datetime import UTC, date, datetime, time, timedelta

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = decode_access_token(token)
    if email is None:
        raise credentials_exc
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


class DateRange:
    """Resolved, timezone-aware analysis window plus its comparison period."""

    def __init__(self, start: datetime, end: datetime, compare: bool):
        self.start = start
        self.end = end
        self.compare = compare
        span = end - start
        # Previous period is the immediately preceding, equal-length window.
        self.prev_end = start
        self.prev_start = start - span

    @property
    def days(self) -> int:
        return max((self.end - self.start).days, 1)


def get_date_range(
    start_date: date | None = Query(
        None, description="Inclusive start date (UTC). Defaults to 30 days ago."
    ),
    end_date: date | None = Query(
        None, description="Exclusive end date (UTC). Defaults to today."
    ),
    compare: bool = Query(
        False, description="Enable comparison against the previous equal-length period."
    ),
) -> DateRange:
    today = datetime.now(UTC).date()
    resolved_end = end_date or today
    resolved_start = start_date or (resolved_end - timedelta(days=30))
    if resolved_start >= resolved_end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be strictly before end_date",
        )
    start_dt = datetime.combine(resolved_start, time.min, tzinfo=UTC)
    end_dt = datetime.combine(resolved_end, time.min, tzinfo=UTC)
    return DateRange(start_dt, end_dt, compare)
