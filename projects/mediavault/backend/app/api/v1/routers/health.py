"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    """Always returns 200 while the process is up (used by container liveness)."""
    return {"status": "ok", "version": __version__}


@router.get("/ready", summary="Readiness probe")
def ready(db: DbSession) -> dict:
    """Verifies dependencies (database) before signalling readiness for traffic."""
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc.__class__.__name__}"

    ready_state = all(v == "ok" for v in checks.values())
    return {"status": "ready" if ready_state else "degraded", "checks": checks}
