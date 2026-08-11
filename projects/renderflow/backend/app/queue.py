"""Priority + delayed job queue abstraction.

Two implementations:

* :class:`RedisQueue` — a Redis sorted set used as the shared work queue across
  API and worker processes. The score encodes *when* a job may run
  (``next_run_at``) with a tiny priority offset so higher-priority jobs win ties.
  Delayed retries fall out naturally: a job scheduled in the future simply isn't
  returned until ``now`` reaches its score.
* :class:`InMemoryQueue` — an in-process heap used for tests and single-node
  demos where standing up Redis is unnecessary.

The atomic "pop the earliest *ready* job" operation is done in Redis with a Lua
script so concurrent workers never claim the same job.
"""

from __future__ import annotations

import heapq
import threading
import time
from abc import ABC, abstractmethod

from .config import Settings, get_settings

# Priority is folded into the score as a sub-second offset so it only breaks
# ties between jobs scheduled at (roughly) the same instant, without letting a
# high priority job jump ahead of a genuinely earlier-scheduled one.
_PRIORITY_SCALE = 0.001

# KEYS[1] = queue key, ARGV[1] = now (epoch seconds)
# Pops the member with the smallest score iff that score <= now.
_POP_READY_LUA = """
local items = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, 1)
if #items == 0 then
    return nil
end
redis.call('ZREM', KEYS[1], items[1])
return items[1]
"""


def _score(priority: int, run_at: float) -> float:
    return run_at - (priority * _PRIORITY_SCALE)


class JobQueue(ABC):
    """Interface for enqueue/dequeue of job ids."""

    @abstractmethod
    def enqueue(self, job_id: str, priority: int = 0, delay_seconds: float = 0.0) -> None:
        ...

    @abstractmethod
    def dequeue(self) -> str | None:
        """Return the next ready job id, or None if none are ready."""

    @abstractmethod
    def size(self) -> int:
        ...

    @abstractmethod
    def remove(self, job_id: str) -> None:
        ...

    def ping(self) -> bool:  # pragma: no cover - trivial default
        return True


class InMemoryQueue(JobQueue):
    """Thread-safe in-process priority queue (tests / single node)."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, str]] = []
        self._counter = 0
        self._lock = threading.Lock()

    def enqueue(self, job_id: str, priority: int = 0, delay_seconds: float = 0.0) -> None:
        run_at = time.time() + max(0.0, delay_seconds)
        with self._lock:
            # Drop any stale copy so re-enqueue doesn't duplicate the job.
            self._heap = [item for item in self._heap if item[2] != job_id]
            heapq.heapify(self._heap)
            heapq.heappush(self._heap, (_score(priority, run_at), self._counter, job_id))
            self._counter += 1

    def dequeue(self) -> str | None:
        now = time.time()
        with self._lock:
            if self._heap and self._heap[0][0] <= now:
                return heapq.heappop(self._heap)[2]
        return None

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def remove(self, job_id: str) -> None:
        with self._lock:
            self._heap = [item for item in self._heap if item[2] != job_id]
            heapq.heapify(self._heap)


class RedisQueue(JobQueue):
    """Redis sorted-set backed queue shared across processes."""

    def __init__(self, redis_url: str, queue_key: str) -> None:
        import redis  # local import; only needed when Redis is configured

        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.queue_key = queue_key
        self._pop_ready = self.client.register_script(_POP_READY_LUA)

    def enqueue(self, job_id: str, priority: int = 0, delay_seconds: float = 0.0) -> None:
        run_at = time.time() + max(0.0, delay_seconds)
        self.client.zadd(self.queue_key, {job_id: _score(priority, run_at)})

    def dequeue(self) -> str | None:
        result = self._pop_ready(keys=[self.queue_key], args=[time.time()])
        return result if result else None

    def size(self) -> int:
        return int(self.client.zcard(self.queue_key))

    def remove(self, job_id: str) -> None:
        self.client.zrem(self.queue_key, job_id)

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:  # noqa: BLE001
            return False


# A process-wide singleton so the in-memory queue is actually shared between the
# API routes and (in single-process demos) any embedded worker.
_queue_singleton: JobQueue | None = None


def get_queue(settings: Settings | None = None) -> JobQueue:
    global _queue_singleton
    settings = settings or get_settings()
    if settings.redis_url:
        # Redis clients are cheap and connection-pooled; create per call is fine,
        # but we still cache for symmetry.
        if not isinstance(_queue_singleton, RedisQueue):
            _queue_singleton = RedisQueue(settings.redis_url, settings.queue_key)
        return _queue_singleton
    if not isinstance(_queue_singleton, InMemoryQueue):
        _queue_singleton = InMemoryQueue()
    return _queue_singleton


def reset_queue() -> None:
    """Testing helper to clear the singleton between tests."""
    global _queue_singleton
    _queue_singleton = None
