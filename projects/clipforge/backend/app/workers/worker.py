"""Standalone worker process.

Consumes job ids from the Redis queue and runs each through the processing
pipeline. Designed to run as its own container/process (see docker-compose).
"""

from __future__ import annotations

import signal
import sys

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.workers.pipeline import run_pipeline
from app.workers.queue import JobQueue

logger = get_logger("clipforge.worker")

_shutdown = False


def _handle_signal(signum, _frame):  # pragma: no cover - signal path
    global _shutdown
    logger.info("worker_shutdown_requested", extra={"signal": signum})
    _shutdown = True


def main() -> int:
    configure_logging(settings.log_level, settings.log_json)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    queue = JobQueue()
    if queue.backend != "redis":
        logger.error("worker_requires_redis")
        return 1

    logger.info("worker_started", extra={"queue": settings.job_queue_name})
    while not _shutdown:
        job_id = queue.dequeue(timeout=5)
        if job_id is None:
            continue
        db = SessionLocal()
        try:
            run_pipeline(db, job_id)
        except Exception:  # noqa: BLE001 - keep worker alive on failures
            logger.exception("worker_job_failed", extra={"job_id": job_id})
        finally:
            db.close()

    logger.info("worker_stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
