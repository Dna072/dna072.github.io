"""Redis-backed priority queue.

Two sorted sets are used:

* `queue_key`   — ready-to-run job ids, scored so that BZPOPMIN always pops
                   the highest-priority, oldest-enqueued job next.
* `delayed_key` — jobs waiting out a retry backoff, scored by the epoch
                   timestamp (ms) at which they become eligible. A periodic
                   scheduler (see `app.scheduler`) promotes due entries from
                   `delayed_key` back onto `queue_key`.

Redis's `BZPOPMIN` gives us a blocking, race-free "pop the best job" primitive
without needing a separate lock service.
"""

import time

import redis

PRIORITY_WEIGHT = 10**13


def _priority_score(priority: int, enqueued_at_ms: int | None = None) -> float:
    ts = enqueued_at_ms if enqueued_at_ms is not None else int(time.time() * 1000)
    # Higher priority => lower score => popped first by BZPOPMIN/ZPOPMIN.
    return (10 - priority) * PRIORITY_WEIGHT + ts


def get_redis(url: str) -> redis.Redis:
    return redis.Redis.from_url(url, decode_responses=True)


def enqueue_job(client: redis.Redis, queue_key: str, job_id: str, priority: int) -> None:
    client.zadd(queue_key, {job_id: _priority_score(priority)})


def dequeue_job(client: redis.Redis, queue_key: str, timeout: int) -> str | None:
    """Block up to `timeout` seconds for the next job id, or return None."""
    result = client.bzpopmin(queue_key, timeout=timeout)
    if result is None:
        return None
    _key, member, _score = result
    return member


def schedule_retry(client: redis.Redis, delayed_key: str, job_id: str, ready_at_ms: int) -> None:
    client.zadd(delayed_key, {job_id: ready_at_ms})


def promote_due_retries(
    client: redis.Redis, delayed_key: str, queue_key: str, priority_lookup: dict[str, int]
) -> list[str]:
    """Move any delayed jobs whose backoff has elapsed onto the live queue.

    `priority_lookup` maps job_id -> priority so promoted jobs keep their
    priority ordering; callers pass a dict built from a DB query.
    """
    now_ms = int(time.time() * 1000)
    due = client.zrangebyscore(delayed_key, min=0, max=now_ms)
    promoted: list[str] = []
    for job_id in due:
        removed = client.zrem(delayed_key, job_id)
        if not removed:
            continue  # another scheduler replica already claimed it
        priority = priority_lookup.get(job_id, 5)
        enqueue_job(client, queue_key, job_id, priority)
        promoted.append(job_id)
    return promoted


def queue_depth(client: redis.Redis, queue_key: str) -> int:
    return int(client.zcard(queue_key))


def remove_job(client: redis.Redis, queue_key: str, delayed_key: str, job_id: str) -> None:
    """Best-effort removal from both sets (used when cancelling a job)."""
    client.zrem(queue_key, job_id)
    client.zrem(delayed_key, job_id)
