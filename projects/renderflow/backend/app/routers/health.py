"""Liveness and readiness probes.

* ``GET /health`` — *liveness*: cheap, dependency-free. If this stops returning
  200 the process is wedged and the orchestrator should restart the pod.
* ``GET /ready`` — *readiness*: verifies the DB and queue are reachable. If this
  fails, Kubernetes removes the pod from the Service endpoints so no traffic is
  routed to it until dependencies recover — no restart, no dropped requests.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import __version__
from ..config import get_settings
from ..database import get_session
from ..queue import get_queue
from ..schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger("renderflow.health")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok", service=settings.service_name, version=__version__
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(response: Response, session: Session = Depends(get_session)) -> ReadyResponse:
    checks: dict[str, str] = {}
    ok = True

    try:
        session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        ok = False
        checks["database"] = f"error: {exc}"
        logger.error("readiness DB check failed", exc_info=True)

    try:
        checks["queue"] = "ok" if get_queue().ping() else "error: unreachable"
        ok = ok and checks["queue"] == "ok"
    except Exception as exc:  # noqa: BLE001
        ok = False
        checks["queue"] = f"error: {exc}"
        logger.error("readiness queue check failed", exc_info=True)

    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="ready" if ok else "not_ready", checks=checks)
