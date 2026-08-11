"""Job service layer: the single place that mutates job state.

All status changes flow through :func:`_transition`, which validates the change
against the state machine before persisting. This keeps the queue, retry, and
reaper logic consistent and auditable.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .backoff import compute_backoff_seconds
from .config import Settings, get_settings
from .models import Job, WorkerHeartbeat
from .queue import JobQueue, get_queue
from .schemas import JobCreate
from .state_machine import (
    ACTIVE_STATES,
    InvalidTransition,
    JobStatus,
    assert_transition,
    is_retryable,
)

logger = logging.getLogger("renderflow.service")


def _now() -> datetime:
    return datetime.now(tz=UTC)


class JobNotFound(Exception):
    pass


class JobNotRetryable(Exception):
    pass


def _transition(job: Job, target: JobStatus) -> None:
    """Validate and apply a status transition on ``job`` (no commit)."""
    current = job.as_status()
    assert_transition(current, target)
    job.status = target.value


# --------------------------------------------------------------------------- #
# Submission / idempotency
# --------------------------------------------------------------------------- #
def create_job(
    session: Session,
    payload: JobCreate,
    *,
    queue: JobQueue | None = None,
    settings: Settings | None = None,
) -> tuple[Job, bool]:
    """Create and enqueue a job.

    Returns ``(job, created)``. If ``idempotency_key`` matches an existing job,
    the existing job is returned with ``created=False`` and nothing is enqueued
    twice — so a client retrying a submission never spawns duplicate work.
    """
    settings = settings or get_settings()
    queue = queue or get_queue(settings)

    if payload.idempotency_key:
        existing = session.scalar(
            select(Job).where(Job.idempotency_key == payload.idempotency_key)
        )
        if existing is not None:
            logger.info(
                "idempotent submission reused existing job",
                extra={"job_id": existing.id, "idempotency_key": payload.idempotency_key},
            )
            return existing, False

    job = Job(
        job_type=payload.job_type.value,
        status=JobStatus.PENDING.value,
        priority=payload.priority,
        input_uri=payload.input_uri,
        params=payload.params or {},
        max_retries=(
            payload.max_retries
            if payload.max_retries is not None
            else settings.default_max_retries
        ),
        idempotency_key=payload.idempotency_key,
        next_run_at=_now(),
    )
    session.add(job)
    try:
        session.flush()
    except IntegrityError:
        # A concurrent request inserted the same idempotency key first; return
        # that winner instead of failing the client.
        session.rollback()
        existing = session.scalar(
            select(Job).where(Job.idempotency_key == payload.idempotency_key)
        )
        if existing is not None:
            return existing, False
        raise

    _transition(job, JobStatus.QUEUED)
    session.commit()

    queue.enqueue(job.id, priority=job.priority, delay_seconds=0.0)
    logger.info(
        "job created and queued",
        extra={"job_id": job.id, "job_type": job.job_type, "priority": job.priority},
    )
    return job, True


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
def get_job(session: Session, job_id: str) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise JobNotFound(job_id)
    return job


def list_jobs(
    session: Session,
    *,
    status: JobStatus | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Job], int]:
    stmt = select(Job)
    count_stmt = select(func.count()).select_from(Job)
    if status is not None:
        stmt = stmt.where(Job.status == status.value)
        count_stmt = count_stmt.where(Job.status == status.value)
    if job_type is not None:
        stmt = stmt.where(Job.job_type == job_type)
        count_stmt = count_stmt.where(Job.job_type == job_type)

    stmt = stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)
    items = list(session.scalars(stmt))
    total = int(session.scalar(count_stmt) or 0)
    return items, total


def count_by_status(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(Job.status, func.count()).group_by(Job.status)
    ).all()
    return dict(rows)


def list_failed(session: Session, *, limit: int = 50, offset: int = 0):
    return list_jobs(session, status=JobStatus.FAILED, limit=limit, offset=offset)


# --------------------------------------------------------------------------- #
# Operator retry
# --------------------------------------------------------------------------- #
def retry_job(
    session: Session,
    job_id: str,
    *,
    queue: JobQueue | None = None,
    reset_retries: bool = False,
    settings: Settings | None = None,
) -> Job:
    """Re-queue a FAILED or CANCELLED job (manual operator action)."""
    settings = settings or get_settings()
    queue = queue or get_queue(settings)

    job = get_job(session, job_id)
    if not is_retryable(job.as_status()):
        raise JobNotRetryable(
            f"job {job_id} in status {job.status} cannot be retried"
        )

    if reset_retries:
        job.retries = 0
    job.error_message = None
    job.worker_id = None
    job.lease_expires_at = None
    job.next_run_at = _now()
    _transition(job, JobStatus.QUEUED)
    session.commit()

    queue.enqueue(job.id, priority=job.priority, delay_seconds=0.0)
    logger.info("job manually re-queued", extra={"job_id": job.id})
    return job


def cancel_job(session: Session, job_id: str, *, queue: JobQueue | None = None) -> Job:
    queue = queue or get_queue()
    job = get_job(session, job_id)
    if job.as_status() not in ACTIVE_STATES:
        raise InvalidTransition(job.as_status(), JobStatus.CANCELLED)
    _transition(job, JobStatus.CANCELLED)
    job.completed_at = _now()
    session.commit()
    queue.remove(job.id)
    logger.info("job cancelled", extra={"job_id": job.id})
    return job


# --------------------------------------------------------------------------- #
# Worker-side transitions
# --------------------------------------------------------------------------- #
def claim_job(
    session: Session,
    job_id: str,
    worker_id: str,
    *,
    settings: Settings | None = None,
) -> Job | None:
    """Mark a queued job as RUNNING under ``worker_id``'s lease.

    Returns None if the job is no longer claimable (e.g. cancelled, or already
    picked up by another worker) so the caller can simply skip it.
    """
    settings = settings or get_settings()
    job = session.get(Job, job_id)
    if job is None:
        return None
    if job.as_status() not in {JobStatus.QUEUED, JobStatus.RETRYING}:
        return None

    if job.as_status() == JobStatus.RETRYING:
        _transition(job, JobStatus.QUEUED)
    _transition(job, JobStatus.RUNNING)
    job.worker_id = worker_id
    job.started_at = job.started_at or _now()
    job.lease_expires_at = _now() + timedelta(seconds=settings.job_lease_seconds)
    session.commit()
    logger.info(
        "job claimed", extra={"job_id": job.id, "worker_id": worker_id}
    )
    return job


def complete_job(session: Session, job_id: str, *, output_uri: str | None, result: dict | None) -> Job:
    job = get_job(session, job_id)
    _transition(job, JobStatus.SUCCEEDED)
    job.output_uri = output_uri
    job.result = result
    job.error_message = None
    job.completed_at = _now()
    job.lease_expires_at = None
    session.commit()
    logger.info("job succeeded", extra={"job_id": job.id})
    return job


def fail_job(
    session: Session,
    job_id: str,
    *,
    error_message: str,
    queue: JobQueue | None = None,
    settings: Settings | None = None,
) -> Job:
    """Handle a processing failure with retry + backoff.

    If retries remain the job goes to RETRYING and is re-queued with an
    exponential-backoff delay. Otherwise it becomes terminally FAILED and shows
    up in the failed-jobs list for manual inspection/retry.
    """
    settings = settings or get_settings()
    queue = queue or get_queue(settings)

    job = get_job(session, job_id)
    job.retries += 1
    job.error_message = error_message[:4000]
    job.worker_id = None
    job.lease_expires_at = None

    if job.retries <= job.max_retries:
        delay = compute_backoff_seconds(job.retries, settings)
        job.next_run_at = _now() + timedelta(seconds=delay)
        _transition(job, JobStatus.RETRYING)
        session.commit()
        queue.enqueue(job.id, priority=job.priority, delay_seconds=delay)
        logger.warning(
            "job failed; scheduled retry",
            extra={
                "job_id": job.id,
                "retries": job.retries,
                "max_retries": job.max_retries,
                "backoff_seconds": delay,
            },
        )
    else:
        _transition(job, JobStatus.FAILED)
        job.completed_at = _now()
        session.commit()
        logger.error(
            "job failed permanently",
            extra={"job_id": job.id, "retries": job.retries},
        )
    return job


# --------------------------------------------------------------------------- #
# Reaper: recover jobs whose worker died mid-flight
# --------------------------------------------------------------------------- #
def reap_stuck_jobs(
    session: Session,
    *,
    queue: JobQueue | None = None,
    settings: Settings | None = None,
) -> int:
    """Requeue RUNNING jobs whose lease has expired (worker crashed/lost).

    Returns the number of jobs reaped. Treated as a failure so normal retry and
    backoff rules apply.
    """
    settings = settings or get_settings()
    queue = queue or get_queue(settings)

    now = _now()
    stmt = select(Job).where(
        Job.status == JobStatus.RUNNING.value,
        Job.lease_expires_at.is_not(None),
        Job.lease_expires_at < now,
    )
    stuck = list(session.scalars(stmt))
    for job in stuck:
        fail_job(
            session,
            job.id,
            error_message="worker lease expired (worker presumed dead)",
            queue=queue,
            settings=settings,
        )
    if stuck:
        logger.warning("reaped stuck jobs", extra={"count": len(stuck)})
    return len(stuck)


# --------------------------------------------------------------------------- #
# Worker heartbeats
# --------------------------------------------------------------------------- #
def record_heartbeat(
    session: Session,
    worker_id: str,
    *,
    hostname: str | None = None,
    status: str = "idle",
    current_job_id: str | None = None,
    jobs_processed: int | None = None,
    jobs_failed: int | None = None,
) -> WorkerHeartbeat:
    hb = session.get(WorkerHeartbeat, worker_id)
    if hb is None:
        hb = WorkerHeartbeat(worker_id=worker_id, hostname=hostname)
        session.add(hb)
    hb.status = status
    hb.current_job_id = current_job_id
    if hostname is not None:
        hb.hostname = hostname
    if jobs_processed is not None:
        hb.jobs_processed = jobs_processed
    if jobs_failed is not None:
        hb.jobs_failed = jobs_failed
    hb.last_heartbeat_at = _now()
    session.commit()
    return hb


def list_workers(
    session: Session, *, settings: Settings | None = None
) -> tuple[list[tuple[WorkerHeartbeat, bool, float]], int]:
    """Return workers with derived (healthy, seconds_since_heartbeat)."""
    settings = settings or get_settings()
    now = _now()
    workers = list(session.scalars(select(WorkerHeartbeat)))
    enriched: list[tuple[WorkerHeartbeat, bool, float]] = []
    online = 0
    for w in workers:
        last = w.last_heartbeat_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        age = (now - last).total_seconds()
        healthy = age <= settings.worker_stale_after_seconds
        if healthy:
            online += 1
        enriched.append((w, healthy, round(age, 2)))
    return enriched, online
