"""Redis-backed job queue.

Uses a Redis list as a simple, reliable FIFO queue (``LPUSH`` producer /
``BRPOP`` consumer). The abstraction exposes ``enqueue`` and ``dequeue`` so the
API and worker never touch Redis directly, and tests can substitute an in-memory
fake.
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any, Protocol, cast

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobQueue(Protocol):
    def enqueue(self, payload: dict[str, Any]) -> None: ...

    def dequeue(self, timeout: int = 5) -> dict[str, Any] | None: ...

    def ping(self) -> bool: ...


class RedisQueue:
    def __init__(self, redis_url: str | None = None, queue_name: str | None = None) -> None:
        import redis

        self._redis = redis.Redis.from_url(
            redis_url or settings.redis_url, decode_responses=True
        )
        self._queue = queue_name or settings.processing_queue

    def enqueue(self, payload: dict[str, Any]) -> None:
        self._redis.lpush(self._queue, json.dumps(payload))
        logger.info("job_enqueued", queue=self._queue, **payload)

    def dequeue(self, timeout: int = 5) -> dict[str, Any] | None:
        result = cast(
            "tuple[str, str] | None",
            self._redis.brpop([self._queue], timeout=timeout),
        )
        if result is None:
            return None
        _, raw = result
        return json.loads(raw)

    def ping(self) -> bool:
        try:
            return bool(self._redis.ping())
        except Exception:  # pragma: no cover - network dependent
            return False


class InMemoryQueue:
    """A synchronous, in-process queue for tests and single-node dev runs."""

    def __init__(self) -> None:
        self._items: deque[dict[str, Any]] = deque()

    def enqueue(self, payload: dict[str, Any]) -> None:
        self._items.appendleft(payload)

    def dequeue(self, timeout: int = 5) -> dict[str, Any] | None:
        if self._items:
            return self._items.pop()
        return None

    def ping(self) -> bool:
        return True


_queue: JobQueue | None = None


def get_queue() -> JobQueue:
    """Return the process-wide queue, constructing it lazily.

    Falls back to the in-memory queue when Redis is unavailable so the API keeps
    functioning (jobs still persist in the DB and can be reprocessed).
    """
    global _queue
    if _queue is not None:
        return _queue
    try:
        q: JobQueue = RedisQueue()
        q.ping()
        _queue = q
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.warning("redis_unavailable_using_memory_queue", error=str(exc))
        _queue = InMemoryQueue()
    return _queue


def set_queue(queue: JobQueue | None) -> None:
    """Override the global queue (used by tests)."""
    global _queue
    _queue = queue
