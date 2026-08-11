"""Job state-machine operations shared by the API routes.

Kept free of FastAPI imports so it can be unit tested directly against a
SQLAlchemy `Session` (see `api/tests/test_state_machine.py`).
"""

import uuid
from datetime import UTC, datetime

import redis
from renderflow_common.config import Settings
from renderflow_common.enums import JobStatus
from renderflow_common.models import Job
from renderflow_common.queue import enqueue_job, remove_job
from renderflow_common.schemas import JobCreate, JobStats
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class JobNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def create_job(
    db: Session, rds: redis.Redis, settings: Settings, payload: JobCreate
) -> tuple[Job, bool]:
    """Create a job, or return the existing one if `idempotency_key` matches.

    Returns `(job, created)` where `created` is False when an existing job
    with the same idempotency key was returned instead of creating a new row.
    """
    if payload.idempotency_key:
        existing = db.scalar(
            select(Job).where(Job.idempotency_key == payload.idempotency_key)
        )
        if existing is not None:
            return existing, False

    job = Job(
        id=uuid.uuid4(),
        job_type=payload.job_type,
        status=JobStatus.PENDING,
        priority=payload.priority,
        input_uri=payload.input_uri,
        params=payload.params,
        max_retries=payload.max_retries,
        idempotency_key=payload.idempotency_key,
    )
    db.add(job)
    try:
        db.flush()
    except IntegrityError:
        # Lost a race on the idempotency key's unique constraint: another
        # request created it first. Return that one instead (still idempotent).
        db.rollback()
        existing = db.scalar(
            select(Job).where(Job.idempotency_key == payload.idempotency_key)
        )
        if existing is not None:
            return existing, False
        raise

    job.status = JobStatus.QUEUED
    job.queued_at = _now()
    db.commit()
    db.refresh(job)

    enqueue_job(rds, settings.queue_key, str(job.id), job.priority)
    return job, True


def get_job(db: Session, job_id: uuid.UUID) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise JobNotFoundError(str(job_id))
    return job


def list_jobs(
    db: Session,
    *,
    status: JobStatus | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Job], int]:
    stmt = select(Job)
    count_stmt = select(func.count()).select_from(Job)
    if status is not None:
        stmt = stmt.where(Job.status == status)
        count_stmt = count_stmt.where(Job.status == status)
    if job_type is not None:
        stmt = stmt.where(Job.job_type == job_type)
        count_stmt = count_stmt.where(Job.job_type == job_type)

    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Job.priority.desc(), Job.created_at.asc()).limit(limit).offset(offset)
    items = list(db.scalars(stmt).all())
    return items, total


RETRYABLE_STATUSES = {JobStatus.FAILED}
CANCELLABLE_STATUSES = {JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RETRYING}


def retry_job(db: Session, rds: redis.Redis, settings: Settings, job_id: uuid.UUID) -> Job:
    """Manually re-queue a job that has exhausted its retries (dead letter).

    This is the operator-facing "failed job retry" endpoint: it resets the
    retry counter and error, and pushes the job straight back onto the live
    queue (no backoff delay, since a human explicitly asked for it now).
    """
    job = get_job(db, job_id)
    if job.status not in RETRYABLE_STATUSES:
        raise InvalidTransitionError(
            f"job {job_id} is {job.status.value}; only failed jobs can be retried"
        )

    job.status = JobStatus.QUEUED
    job.retries = 0
    job.error = None
    job.worker_id = None
    job.heartbeat_at = None
    job.next_retry_at = None
    job.queued_at = _now()
    db.commit()
    db.refresh(job)

    enqueue_job(rds, settings.queue_key, str(job.id), job.priority)
    return job


def cancel_job(db: Session, rds: redis.Redis, settings: Settings, job_id: uuid.UUID) -> Job:
    job = get_job(db, job_id)
    if job.status not in CANCELLABLE_STATUSES:
        raise InvalidTransitionError(
            f"job {job_id} is {job.status.value}; only pending/queued/retrying jobs can be cancelled"
        )

    job.status = JobStatus.CANCELLED
    job.completed_at = _now()
    db.commit()
    db.refresh(job)

    remove_job(rds, settings.queue_key, settings.delayed_queue_key, str(job.id))
    return job


def get_stats(db: Session) -> JobStats:
    by_status_rows = db.execute(select(Job.status, func.count()).group_by(Job.status)).all()
    by_type_rows = db.execute(select(Job.job_type, func.count()).group_by(Job.job_type)).all()
    by_status = {status.value: count for status, count in by_status_rows}
    by_type = {jtype.value: count for jtype, count in by_type_rows}
    total = sum(by_status.values())
    return JobStats(by_status=by_status, by_type=by_type, total=total)
