"""RenderFlow worker entrypoint.

Run several of these (docker-compose `--scale worker=N`, or the k8s
Deployment's `replicas`/HPA) to process jobs in parallel. Each instance:

1. Registers itself in the `workers` table and starts a heartbeat thread.
2. Blocks on the Redis priority queue (`BZPOPMIN`) for the next job id.
3. Atomically claims it in Postgres (status QUEUED/RETRYING -> PROCESSING).
4. Processes it (real FFmpeg or the mock fallback), then marks it
   COMPLETED, or RETRYING/FAILED with the error recorded.
"""

import logging
import os
import signal
import socket
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from renderflow_common.config import get_settings
from renderflow_common.db import make_engine, make_session_factory
from renderflow_common.enums import JobStatus
from renderflow_common.models import Job
from renderflow_common.queue import dequeue_job, get_redis

from .ffmpeg_adapter import ProcessingError
from .heartbeat import HeartbeatReporter, WorkerState
from .processor import process_job

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("renderflow.worker")


class GracefulShutdown:
    def __init__(self):
        self.stop = False
        signal.signal(signal.SIGTERM, self._handle)
        signal.signal(signal.SIGINT, self._handle)

    def _handle(self, signum, frame):
        logger.info("received signal %s, shutting down after current job", signum)
        self.stop = True


def _claim_job(session_factory, job_id: uuid.UUID, worker_id: str) -> Job | None:
    db = session_factory()
    try:
        job = db.get(Job, job_id)
        if job is None:
            logger.warning("job %s not found (may have been deleted)", job_id)
            return None
        if job.status not in (JobStatus.QUEUED, JobStatus.RETRYING):
            logger.info("job %s is %s, not claimable (skipping)", job_id, job.status.value)
            return None

        job.status = JobStatus.PROCESSING
        job.worker_id = worker_id
        job.started_at = datetime.now(UTC)
        job.heartbeat_at = datetime.now(UTC)
        db.commit()
        db.refresh(job)
        db.expunge(job)
        return job
    finally:
        db.close()


def _complete_job(session_factory, job_id: uuid.UUID, output_uri: str | None, result: dict) -> None:
    db = session_factory()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        job.status = JobStatus.COMPLETED
        job.output_uri = output_uri
        job.result = result
        job.error = None
        job.completed_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


def _fail_job(session_factory, rds, settings, job_id: uuid.UUID, error: str) -> JobStatus:
    db = session_factory()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return JobStatus.FAILED
        job.retries += 1
        job.error = error
        job.worker_id = None
        job.heartbeat_at = None

        if job.retries >= job.max_retries:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(UTC)
            logger.warning("job %s dead-lettered after %d retries: %s", job_id, job.retries, error)
        else:
            backoff = settings.retry_backoff_base_seconds * (2**job.retries)
            ready_at = datetime.now(UTC) + timedelta(seconds=backoff)
            job.status = JobStatus.RETRYING
            job.next_retry_at = ready_at
            rds.zadd(settings.delayed_queue_key, {str(job.id): int(ready_at.timestamp() * 1000)})
            logger.info("job %s failed, retry %d/%d scheduled in %.0fs: %s",
                        job_id, job.retries, job.max_retries, backoff, error)

        status = job.status
        db.commit()
        return status
    finally:
        db.close()


def run() -> None:
    settings = get_settings()
    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    rds = get_redis(settings.redis_url)

    worker_id = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    storage_root = Path(settings.media_storage_path)
    storage_root.mkdir(parents=True, exist_ok=True)

    state = WorkerState(worker_id=worker_id, hostname=socket.gethostname(), pid=os.getpid())
    reporter = HeartbeatReporter(session_factory, state, settings.heartbeat_interval_seconds)
    reporter.start()
    logger.info("worker %s started (poll_timeout=%ss, force_mock_ffmpeg=%s)",
                worker_id, settings.worker_poll_timeout_seconds, settings.force_mock_ffmpeg)

    shutdown = GracefulShutdown()

    try:
        while not shutdown.stop:
            job_id_str = dequeue_job(rds, settings.queue_key, timeout=settings.worker_poll_timeout_seconds)
            if job_id_str is None:
                continue

            try:
                job_id = uuid.UUID(job_id_str)
            except ValueError:
                logger.warning("dropping malformed queue entry: %r", job_id_str)
                continue

            job = _claim_job(session_factory, job_id, worker_id)
            if job is None:
                continue

            reporter.set_busy(job.id)
            logger.info("job %s claimed (type=%s priority=%d)", job.id, job.job_type.value, job.priority)

            try:
                outcome = process_job(job, storage_root, settings.force_mock_ffmpeg)
                _complete_job(session_factory, job.id, outcome.output_uri, outcome.result)
                reporter.set_idle(success=True)
                logger.info("job %s completed", job.id)
            except ProcessingError as exc:
                _fail_job(session_factory, rds, settings, job.id, str(exc))
                reporter.set_idle(success=False)
            except Exception as exc:  # pragma: no cover - defensive catch-all
                logger.exception("job %s crashed unexpectedly", job.id)
                _fail_job(session_factory, rds, settings, job.id, f"unexpected error: {exc}")
                reporter.set_idle(success=False)
    finally:
        reporter.stop()
        logger.info("worker %s stopped", worker_id)


if __name__ == "__main__":
    run()
