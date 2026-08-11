from renderflow_common.config import Settings
from renderflow_common.enums import JobType
from renderflow_common.schemas import JobCreate

from app.services import job_service


def _settings():
    return Settings(
        database_url="sqlite:///:memory:",
        queue_key="test:queue",
        delayed_queue_key="test:delayed",
    )


def test_duplicate_idempotency_key_returns_same_job(db_session, fake_redis):
    settings = _settings()
    payload = JobCreate(
        job_type=JobType.TRANSCODE,
        input_uri="s3://bucket/in.mp4",
        idempotency_key="req-123",
    )

    job1, created1 = job_service.create_job(db_session, fake_redis, settings, payload)
    job2, created2 = job_service.create_job(db_session, fake_redis, settings, payload)

    assert created1 is True
    assert created2 is False
    assert job1.id == job2.id
    # Only enqueued once, not twice.
    assert fake_redis.zcard(settings.queue_key) == 1


def test_different_idempotency_keys_create_distinct_jobs(db_session, fake_redis):
    settings = _settings()
    job1, _ = job_service.create_job(
        db_session,
        fake_redis,
        settings,
        JobCreate(job_type=JobType.THUMBNAIL, input_uri="a", idempotency_key="k1"),
    )
    job2, _ = job_service.create_job(
        db_session,
        fake_redis,
        settings,
        JobCreate(job_type=JobType.THUMBNAIL, input_uri="b", idempotency_key="k2"),
    )

    assert job1.id != job2.id
    assert fake_redis.zcard(settings.queue_key) == 2


def test_no_idempotency_key_always_creates_new_job(db_session, fake_redis):
    settings = _settings()
    payload = JobCreate(job_type=JobType.METADATA, input_uri="a")

    job1, created1 = job_service.create_job(db_session, fake_redis, settings, payload)
    job2, created2 = job_service.create_job(db_session, fake_redis, settings, payload)

    assert created1 is True and created2 is True
    assert job1.id != job2.id
