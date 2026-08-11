"""Job queue abstraction.

Primary backend is Redis (a simple reliable list-based queue). When Redis is
unavailable the queue falls back to running the pipeline inline on a background
thread so the product still works end-to-end in a minimal demo environment
(e.g. `uvicorn` with no separate worker/redis). The chosen mode is logged.
"""

from __future__ import annotations

import threading

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("clipforge.queue")


class JobQueue:
    """Enqueue processing jobs onto Redis with an inline fallback."""

    def __init__(self, redis_url: str | None = None, queue_name: str | None = None):
        self.redis_url = redis_url or settings.redis_url
        self.queue_name = queue_name or settings.job_queue_name
        self._redis = self._connect()

    def _connect(self):
        try:
            import redis  # noqa: PLC0415 - optional dependency

            client = redis.Redis.from_url(self.redis_url, socket_connect_timeout=1)
            client.ping()
            logger.info("queue_backend", extra={"backend": "redis"})
            return client
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning(
                "queue_redis_unavailable_inline_fallback",
                extra={"error": str(exc)},
            )
            return None

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "inline"

    def enqueue(self, job_id: str) -> None:
        """Enqueue a job id for processing."""
        if self._redis is not None:
            self._redis.lpush(self.queue_name, job_id)
            logger.info("job_enqueued", extra={"job_id": job_id, "backend": "redis"})
            return
        # Inline fallback: run on a daemon thread with its own DB session.
        logger.info("job_enqueued", extra={"job_id": job_id, "backend": "inline"})
        threading.Thread(
            target=_run_inline, args=(job_id,), daemon=True
        ).start()

    def dequeue(self, timeout: int = 5) -> str | None:
        """Block until a job id is available (Redis backend only)."""
        if self._redis is None:
            return None
        result = self._redis.brpop(self.queue_name, timeout=timeout)
        if result is None:
            return None
        _, job_id = result
        return job_id.decode() if isinstance(job_id, bytes) else str(job_id)


def _run_inline(job_id: str) -> None:
    """Execute the pipeline synchronously on a fresh session (fallback mode)."""
    from app.db.session import SessionLocal
    from app.workers.pipeline import run_pipeline

    db = SessionLocal()
    try:
        run_pipeline(db, job_id)
    except Exception:  # pragma: no cover - already logged in pipeline
        logger.exception("inline_job_failed", extra={"job_id": job_id})
    finally:
        db.close()


_queue: JobQueue | None = None


def get_queue() -> JobQueue:
    """Return a process-wide queue singleton."""
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue
