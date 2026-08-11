import uuid

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from renderflow_common.config import Settings
from renderflow_common.enums import JobStatus, JobType
from renderflow_common.schemas import JobCreate, JobList, JobRead, JobStats
from sqlalchemy.orm import Session

from ..deps import get_db, get_redis_client, get_settings
from ..services import job_service

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    rds: redis.Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings),
):
    """Submit a new job.

    Idempotent when `idempotency_key` is supplied: a repeat request with the
    same key returns the original job with a 200 instead of creating a
    duplicate (which the route would otherwise default to 201 for).
    """
    job, created = job_service.create_job(db, rds, settings, payload)
    if not created:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=JobRead.model_validate(job).model_dump(mode="json"),
        )
    return job


@router.get("", response_model=JobList)
def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    job_type: JobType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = job_service.list_jobs(
        db, status=status_filter, job_type=job_type, limit=limit, offset=offset
    )
    return JobList(items=items, total=total, limit=limit, offset=offset)


@router.get("/stats", response_model=JobStats)
def job_stats(db: Session = Depends(get_db)):
    return job_service.get_stats(db)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return job_service.get_job(db, job_id)
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    rds: redis.Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings),
):
    """Re-queue a job that is in the `failed` (dead-letter) state."""
    try:
        return job_service.retry_job(db, rds, settings, job_id)
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except job_service.InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{job_id}/cancel", response_model=JobRead)
def cancel_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    rds: redis.Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings),
):
    try:
        return job_service.cancel_job(db, rds, settings, job_id)
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except job_service.InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
