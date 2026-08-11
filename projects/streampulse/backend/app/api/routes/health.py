"""Liveness and readiness probes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    """Process is up. Does not touch dependencies."""
    return {"status": "ok", "version": __version__}


@router.get("/ready", summary="Readiness probe")
def ready(response: Response, db: Session = Depends(get_db)) -> dict:
    """Ready to serve traffic — verifies the database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:  # noqa: BLE001 - report degraded rather than crash the probe
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "unreachable"}
