"""Background loop owned by the API process.

Two responsibilities, both safe to run from multiple API replicas because
every mutation is a conditional DB update or an atomic Redis ZREM:

1. Reap "processing" jobs whose worker stopped sending heartbeats (crash,
   OOM kill, node loss) and requeue them for retry, or dead-letter them once
   retries are exhausted.
2. Promote delayed retries whose backoff has elapsed back onto the live
   queue.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import redis
from renderflow_common.config import Settings
from renderflow_common.enums import JobStatus
from renderflow_common.models import Job
from renderflow_common.queue import promote_due_retries
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger("renderflow.scheduler")


def reap_stale_jobs(db: Session, rds: redis.Redis, settings: Settings) -> int:
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.heartbeat_timeout_seconds)
    stale = db.scalars(
        select(Job).where(
            Job.status == JobStatus.PROCESSING,
            Job.heartbeat_at.is_not(None),
            Job.heartbeat_at < cutoff,
        )
    ).all()

    for job in stale:
        job.retries += 1
        job.worker_id = None
        job.heartbeat_at = None
        if job.retries >= job.max_retries:
            job.status = JobStatus.FAILED
            job.error = "worker heartbeat timeout: job abandoned after crash/kill"
            job.completed_at = datetime.now(UTC)
            logger.warning("job %s dead-lettered after heartbeat timeout", job.id)
        else:
            backoff = settings.retry_backoff_base_seconds * (2**job.retries)
            ready_at = datetime.now(UTC) + timedelta(seconds=backoff)
            job.status = JobStatus.RETRYING
            job.next_retry_at = ready_at
            job.error = "worker heartbeat timeout: requeued for retry"
            rds.zadd(settings.delayed_queue_key, {str(job.id): int(ready_at.timestamp() * 1000)})
            logger.info("job %s requeued for retry after heartbeat timeout", job.id)

    if stale:
        db.commit()
    return len(stale)


def promote_delayed(db: Session, rds: redis.Redis, settings: Settings) -> int:
    now_ms = int(time.time() * 1000)
    due_ids = rds.zrangebyscore(settings.delayed_queue_key, min=0, max=now_ms)
    if not due_ids:
        return 0

    ids_as_uuid = due_ids
    jobs = db.scalars(select(Job).where(Job.id.in_(ids_as_uuid))).all()
    priority_lookup = {str(j.id): j.priority for j in jobs}
    jobs_by_id = {str(j.id): j for j in jobs}

    promoted = promote_due_retries(rds, settings.delayed_queue_key, settings.queue_key, priority_lookup)

    for job_id in promoted:
        job = jobs_by_id.get(job_id)
        if job is None or job.status != JobStatus.RETRYING:
            continue
        job.status = JobStatus.QUEUED
        job.queued_at = datetime.now(UTC)
        job.next_retry_at = None

    if promoted:
        db.commit()
    return len(promoted)


async def scheduler_loop(session_factory: sessionmaker[Session], rds: redis.Redis, settings: Settings):
    logger.info(
        "scheduler started (interval=%ss heartbeat_timeout=%ss)",
        settings.scheduler_interval_seconds,
        settings.heartbeat_timeout_seconds,
    )
    while True:
        try:
            db = session_factory()
            try:
                reaped = reap_stale_jobs(db, rds, settings)
                promoted = promote_delayed(db, rds, settings)
                if reaped or promoted:
                    logger.info("scheduler tick: reaped=%d promoted=%d", reaped, promoted)
            finally:
                db.close()
        except Exception:  # pragma: no cover - defensive: keep the loop alive
            logger.exception("scheduler tick failed")
        await asyncio.sleep(settings.scheduler_interval_seconds)
