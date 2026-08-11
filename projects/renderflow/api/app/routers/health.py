import redis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..deps import get_db, get_redis_client

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness():
    """Process is up and able to handle requests. Never checks dependencies
    so a slow/degraded Postgres or Redis doesn't cause Kubernetes to kill a
    perfectly healthy pod (that's what readiness is for)."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(
    response: Response,
    db: Session = Depends(get_db),
    rds: redis.Redis = Depends(get_redis_client),
):
    """Dependency check used by the k8s readiness probe and the LB: only
    route traffic here once Postgres and Redis are both reachable."""
    checks = {"database": False, "redis": False}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        rds.ping()
        checks["redis"] = True
    except Exception:
        pass

    ok = all(checks.values())
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "unavailable", "checks": checks}
