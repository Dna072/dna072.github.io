"""Redis queue worker.

Long-running process that consumes job messages from Redis and runs the
processing pipeline for each one. Each job gets a fresh DB session; failures are
logged and (when attempts remain) left re-queued by the pipeline for retry.

Run with: ``python -m app.workers.processor``
"""

from __future__ import annotations

import os
import signal
import socket
import sys
import time

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.services.pipeline import PipelineError, ProcessingPipeline
from app.services.queue import RedisQueue

configure_logging(json_logs=settings.is_production, level="DEBUG" if settings.debug else "INFO")
logger = get_logger("worker")

_shutdown = False


def _handle_signal(signum, _frame) -> None:  # pragma: no cover - signal handler
    global _shutdown
    logger.info("worker_shutdown_requested", signal=signum)
    _shutdown = True


def process_one(message: dict, worker_id: str) -> None:
    job_id = message.get("job_id")
    if not job_id:
        logger.warning("worker_bad_message", message=message)
        return

    db = SessionLocal()
    try:
        pipeline = ProcessingPipeline(db, worker_id=worker_id)
        pipeline.run(job_id)
    except PipelineError as exc:
        logger.error("worker_job_failed", job_id=job_id, error=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("worker_job_crashed", job_id=job_id, error=str(exc))
    finally:
        db.close()


def main() -> int:  # pragma: no cover - integration entrypoint
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    logger.info("worker_started", worker_id=worker_id, queue=settings.processing_queue)

    try:
        queue = RedisQueue()
        queue.ping()
    except Exception as exc:
        logger.error("worker_redis_unavailable", error=str(exc))
        return 1

    while not _shutdown:
        try:
            message = queue.dequeue(timeout=settings.worker_poll_timeout)
        except Exception as exc:
            logger.error("worker_dequeue_error", error=str(exc))
            time.sleep(2)
            continue

        if message is None:
            continue
        logger.info("worker_job_received", **message)
        process_one(message, worker_id)

    logger.info("worker_stopped", worker_id=worker_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
