"""Job submission, status, listing, and retry endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import service
from ..database import get_session
from ..queue import get_queue
from ..schemas import (
    JobCreate,
    JobList,
    JobRead,
    JobStatusCounts,
    MessageResponse,
)
from ..state_machine import InvalidTransition, JobStatus, JobType

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def submit_job(
    payload: JobCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> JobRead:
    """Submit a new job. Idempotent when an ``idempotency_key`` is supplied."""
    job, created = service.create_job(session, payload)
    if not created:
        # Return the existing job with 200 instead of 201 to signal dedupe.
        response.status_code = status.HTTP_200_OK
    return JobRead.model_validate(job)


@router.get("", response_model=JobList)
def list_jobs(
    session: Session = Depends(get_session),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    job_type: JobType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> JobList:
    items, total = service.list_jobs(
        session,
        status=status_filter,
        job_type=job_type.value if job_type else None,
        limit=limit,
        offset=offset,
    )
    return JobList(
        items=[JobRead.model_validate(j) for j in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=JobStatusCounts)
def job_stats(session: Session = Depends(get_session)) -> JobStatusCounts:
    counts = service.count_by_status(session)
    return JobStatusCounts(counts=counts, total=sum(counts.values()))


@router.get("/failed", response_model=JobList)
def list_failed_jobs(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> JobList:
    items, total = service.list_failed(session, limit=limit, offset=offset)
    return JobList(
        items=[JobRead.model_validate(j) for j in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobRead:
    try:
        job = service.get_job(session, job_id)
    except service.JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None
    return JobRead.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(
    job_id: str,
    session: Session = Depends(get_session),
    reset_retries: bool = Query(default=False),
) -> JobRead:
    """Re-queue a failed (or cancelled) job."""
    try:
        job = service.retry_job(session, job_id, reset_retries=reset_retries)
    except service.JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None
    except service.JobNotRetryable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return JobRead.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobRead)
def cancel_job(job_id: str, session: Session = Depends(get_session)) -> JobRead:
    try:
        job = service.cancel_job(session, job_id)
    except service.JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return JobRead.model_validate(job)


@router.delete("/{job_id}", response_model=MessageResponse)
def delete_job(job_id: str, session: Session = Depends(get_session)) -> MessageResponse:
    try:
        job = service.get_job(session, job_id)
    except service.JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None
    get_queue().remove(job.id)
    session.delete(job)
    session.commit()
    return MessageResponse(message=f"job {job_id} deleted")
