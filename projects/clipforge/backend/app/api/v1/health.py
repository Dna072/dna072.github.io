from __future__ import annotations

from sqlalchemy import text

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.core.deps import DbSession
from app.schemas.common import HealthResponse, ReadyResponse
from app.services.queue import get_queue

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe — process is up."""
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        version=__version__,
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(db: DbSession) -> ReadyResponse:
    """Readiness probe — dependencies (DB, Redis) are reachable."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = get_queue().ping()
    status = "ok" if db_ok else "degraded"
    return ReadyResponse(status=status, database=db_ok, redis=redis_ok)
