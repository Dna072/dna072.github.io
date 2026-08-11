from datetime import UTC, datetime, timedelta

import pytest
from renderflow_common.enums import JobStatus, JobType
from renderflow_common.models import Job
from renderflow_common.schemas import JobCreate

from app.scheduler import reap_stale_jobs
from app.services import job_service


def _settings(**overrides):
    from renderflow_common.config import Settings

    defaults = dict(
        database_url="sqlite:///:memory:",
        queue_key="test:queue",
        delayed_queue_key="test:delayed",
        heartbeat_timeout_seconds=30,
        retry_backoff_base_seconds=1,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_create_job_transitions_pending_to_queued(db_session, fake_redis):
    settings = _settings()
    payload = JobCreate(job_type=JobType.TRANSCODE, input_uri="s3://bucket/in.mp4")

    job, created = job_service.create_job(db_session, fake_redis, settings, payload)

    assert created is True
    assert job.status == JobStatus.QUEUED
    assert job.queued_at is not None
    assert fake_redis.zcard(settings.queue_key) == 1


def test_retry_only_allowed_from_failed(db_session, fake_redis):
    settings = _settings()
    job, _ = job_service.create_job(
        db_session, fake_redis, settings, JobCreate(job_type=JobType.THUMBNAIL, input_uri="x")
    )

    with pytest.raises(job_service.InvalidTransitionError):
        job_service.retry_job(db_session, fake_redis, settings, job.id)

    job.status = JobStatus.FAILED
    job.error = "boom"
    job.retries = 3
    db_session.commit()

    retried = job_service.retry_job(db_session, fake_redis, settings, job.id)
    assert retried.status == JobStatus.QUEUED
    assert retried.retries == 0
    assert retried.error is None
    assert fake_redis.zcard(settings.queue_key) == 1


def test_cancel_rejected_once_processing(db_session, fake_redis):
    settings = _settings()
    job, _ = job_service.create_job(
        db_session, fake_redis, settings, JobCreate(job_type=JobType.METADATA, input_uri="x")
    )

    job.status = JobStatus.PROCESSING
    db_session.commit()

    with pytest.raises(job_service.InvalidTransitionError):
        job_service.cancel_job(db_session, fake_redis, settings, job.id)


def test_cancel_removes_from_queue(db_session, fake_redis):
    settings = _settings()
    job, _ = job_service.create_job(
        db_session, fake_redis, settings, JobCreate(job_type=JobType.AUDIO_EXTRACT, input_uri="x")
    )
    assert fake_redis.zcard(settings.queue_key) == 1

    cancelled = job_service.cancel_job(db_session, fake_redis, settings, job.id)
    assert cancelled.status == JobStatus.CANCELLED
    assert fake_redis.zcard(settings.queue_key) == 0


def test_reap_stale_jobs_requeues_with_backoff(db_session, fake_redis):
    settings = _settings(heartbeat_timeout_seconds=1)
    job = Job(
        job_type=JobType.TRANSCODE,
        status=JobStatus.PROCESSING,
        input_uri="x",
        worker_id="worker-1",
        heartbeat_at=datetime.now(UTC) - timedelta(seconds=10),
        retries=0,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    reaped = reap_stale_jobs(db_session, fake_redis, settings)

    db_session.refresh(job)
    assert reaped == 1
    assert job.status == JobStatus.RETRYING
    assert job.retries == 1
    assert job.worker_id is None
    assert fake_redis.zcard(settings.delayed_queue_key) == 1


def test_reap_stale_jobs_dead_letters_after_max_retries(db_session, fake_redis):
    settings = _settings(heartbeat_timeout_seconds=1)
    job = Job(
        job_type=JobType.TRANSCODE,
        status=JobStatus.PROCESSING,
        input_uri="x",
        worker_id="worker-1",
        heartbeat_at=datetime.now(UTC) - timedelta(seconds=10),
        retries=2,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    reap_stale_jobs(db_session, fake_redis, settings)

    db_session.refresh(job)
    assert job.status == JobStatus.FAILED
    assert job.retries == 3
    assert job.error is not None
