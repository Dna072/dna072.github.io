"""Worker status and heartbeat endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import service
from ..database import get_session
from ..schemas import WorkerList, WorkerRead

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


class HeartbeatIn(BaseModel):
    worker_id: str
    hostname: str | None = None
    status: str = "idle"
    current_job_id: str | None = None
    jobs_processed: int | None = None
    jobs_failed: int | None = None


@router.get("", response_model=WorkerList)
def list_workers(session: Session = Depends(get_session)) -> WorkerList:
    enriched, online = service.list_workers(session)
    items = []
    for worker, healthy, age in enriched:
        read = WorkerRead.model_validate(worker)
        read.healthy = healthy
        read.seconds_since_heartbeat = age
        items.append(read)
    return WorkerList(items=items, total=len(items), online=online)


@router.post("/heartbeat", response_model=WorkerRead)
def heartbeat(payload: HeartbeatIn, session: Session = Depends(get_session)) -> WorkerRead:
    """Record a worker heartbeat.

    Workers primarily write heartbeats directly to the DB, but this endpoint
    lets sidecar-less or remote workers report liveness over HTTP too.
    """
    hb = service.record_heartbeat(
        session,
        payload.worker_id,
        hostname=payload.hostname,
        status=payload.status,
        current_job_id=payload.current_job_id,
        jobs_processed=payload.jobs_processed,
        jobs_failed=payload.jobs_failed,
    )
    read = WorkerRead.model_validate(hb)
    read.healthy = True
    read.seconds_since_heartbeat = 0.0
    return read
