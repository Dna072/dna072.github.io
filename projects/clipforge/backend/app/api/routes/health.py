"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.common import HealthStatus, ReadinessStatus
from app.workers.queue import get_queue

router = APIRouter(tags=["health"])

VERSION = "1.0.0"


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    """Liveness probe: process is up."""
    return HealthStatus(status="ok", service=settings.app_name, version=VERSION)


@router.get("/ready", response_model=ReadinessStatus)
def ready(db: DbSession) -> ReadinessStatus:
    """Readiness probe: dependencies (DB, queue) are reachable."""
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # pragma: no cover - failure path
        checks["database"] = f"error: {exc}"

    checks["queue"] = get_queue().backend

    overall = "ok" if checks.get("database") == "ok" else "degraded"
    return ReadinessStatus(status=overall, checks=checks)
