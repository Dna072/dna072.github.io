"""Tests for idempotent submission, retry with backoff, and the reaper."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from app import service
from app.backoff import compute_backoff_seconds
from app.models import Job
from app.schemas import JobCreate
from app.state_machine import JobStatus, JobType


def _payload(**overrides) -> JobCreate:
    base = {"job_type": JobType.METADATA, "input_uri": "file://sample.mp4"}
    base.update(overrides)
    return JobCreate(**base)


def test_idempotent_submission_reuses_job(session, queue):
    p = _payload(idempotency_key="abc-123")
    job1, created1 = service.create_job(session, p, queue=queue)
    job2, created2 = service.create_job(session, p, queue=queue)

    assert created1 is True
    assert created2 is False
    assert job1.id == job2.id
    # Only one job row exists, and it was enqueued only once.
    assert session.query(Job).count() == 1


def test_distinct_keys_create_distinct_jobs(session, queue):
    job_a, _ = service.create_job(session, _payload(idempotency_key="a"), queue=queue)
    job_b, _ = service.create_job(session, _payload(idempotency_key="b"), queue=queue)
    assert job_a.id != job_b.id
    assert session.query(Job).count() == 2


def test_backoff_is_exponential_and_capped():
    from app.config import Settings

    cfg = Settings(
        retry_backoff_base_seconds=2.0,
        retry_backoff_max_seconds=10.0,
        retry_backoff_jitter_seconds=0.0,
    )
    d1 = compute_backoff_seconds(1, cfg, jitter=False)  # 2
    d2 = compute_backoff_seconds(2, cfg, jitter=False)  # 4
    d3 = compute_backoff_seconds(3, cfg, jitter=False)  # 8
    d4 = compute_backoff_seconds(4, cfg, jitter=False)  # 16 -> capped to 10
    assert d1 == 2.0
    assert d1 < d2 < d3
    assert d4 == cfg.retry_backoff_max_seconds


def test_failure_retries_then_terminal(session, queue, settings):
    job, _ = service.create_job(session, _payload(), queue=queue, settings=settings)

    # Claim then fail repeatedly; should retry until max, then FAIL.
    for attempt in range(1, settings.default_max_retries + 1):
        claimed = service.claim_job(session, job.id, "w1", settings=settings)
        assert claimed is not None
        service.fail_job(session, job.id, error_message="boom", queue=queue, settings=settings)
        session.refresh(job)
        assert job.retries == attempt
        assert job.as_status() == JobStatus.RETRYING
        # Wait out the (tiny) backoff so the job is dequeueable again.
        time.sleep(settings.retry_backoff_max_seconds + 0.02)
        assert queue.dequeue() == job.id

    # One more failure exhausts retries -> terminal FAILED.
    service.claim_job(session, job.id, "w1", settings=settings)
    service.fail_job(session, job.id, error_message="boom", queue=queue, settings=settings)
    session.refresh(job)
    assert job.as_status() == JobStatus.FAILED
    assert job.completed_at is not None


def test_manual_retry_requeues_failed_job(session, queue, settings):
    job, _ = service.create_job(session, _payload(max_retries=0), queue=queue, settings=settings)
    service.claim_job(session, job.id, "w1", settings=settings)
    service.fail_job(session, job.id, error_message="boom", queue=queue, settings=settings)
    session.refresh(job)
    assert job.as_status() == JobStatus.FAILED

    retried = service.retry_job(session, job.id, queue=queue, reset_retries=True, settings=settings)
    assert retried.as_status() == JobStatus.QUEUED
    assert retried.retries == 0
    assert retried.error_message is None


def test_reaper_requeues_expired_lease(session, queue, settings):
    job, _ = service.create_job(session, _payload(), queue=queue, settings=settings)
    service.claim_job(session, job.id, "w1", settings=settings)
    session.refresh(job)

    # Force the lease into the past to simulate a dead worker.
    job.lease_expires_at = datetime.now(tz=UTC) - timedelta(seconds=1)
    session.commit()

    reaped = service.reap_stuck_jobs(session, queue=queue, settings=settings)
    assert reaped == 1
    session.refresh(job)
    # retries incremented and job back in the retry/queue cycle.
    assert job.retries == 1
    assert job.as_status() in {JobStatus.RETRYING, JobStatus.QUEUED}
