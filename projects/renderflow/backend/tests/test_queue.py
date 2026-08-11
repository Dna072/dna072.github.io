"""Queue tests.

The in-memory queue is always tested. The Redis-backed queue (including its Lua
"pop earliest ready" script) is tested against fakeredis when available, so the
priority + delayed-retry semantics are verified without a real Redis server.
"""

from __future__ import annotations

import time

import pytest

import app.queue as queue_mod
from app.queue import InMemoryQueue, RedisQueue


def test_in_memory_priority_and_delay():
    q = InMemoryQueue()
    q.enqueue("low", priority=0)
    q.enqueue("high", priority=9)
    q.enqueue("delayed", priority=5, delay_seconds=0.3)

    assert q.size() == 3
    assert q.dequeue() == "high"  # priority tiebreak
    assert q.dequeue() == "low"
    assert q.dequeue() is None  # delayed not yet ready
    time.sleep(0.35)
    assert q.dequeue() == "delayed"
    assert q.size() == 0


def test_in_memory_reenqueue_dedupes():
    q = InMemoryQueue()
    q.enqueue("job-1", priority=1)
    q.enqueue("job-1", priority=5)  # re-enqueue should not duplicate
    assert q.size() == 1
    assert q.dequeue() == "job-1"
    assert q.dequeue() is None


def _fake_redis_queue(key: str):
    fakeredis = pytest.importorskip("fakeredis")
    client = fakeredis.FakeStrictRedis(decode_responses=True)

    q = RedisQueue.__new__(RedisQueue)
    q.client = client
    q.queue_key = key
    q._pop_ready = client.register_script(queue_mod._POP_READY_LUA)
    return q


def test_redis_queue_priority_and_delay():
    q = _fake_redis_queue("test:queue")
    q.enqueue("low", priority=0)
    q.enqueue("high", priority=9)
    q.enqueue("delayed", priority=5, delay_seconds=0.3)

    assert q.size() == 3
    assert q.dequeue() == "high"
    assert q.dequeue() == "low"
    assert q.dequeue() is None
    time.sleep(0.35)
    assert q.dequeue() == "delayed"
    assert q.size() == 0


def test_redis_queue_remove():
    q = _fake_redis_queue("test:queue2")
    q.enqueue("a")
    q.enqueue("b")
    q.remove("a")
    assert q.size() == 1
    assert q.dequeue() == "b"
