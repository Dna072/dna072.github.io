from renderflow_common.config import Settings
from renderflow_common.enums import JobStatus, JobType
from renderflow_common.models import Job

from worker.main import _claim_job, _complete_job, _fail_job


def _settings(**overrides):
    defaults = dict(
        database_url="sqlite:///:memory:",
        delayed_queue_key="test:delayed",
        retry_backoff_base_seconds=1,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_claim_job_only_succeeds_from_queued_or_retrying(session_factory, db_session):
    job = Job(job_type=JobType.TRANSCODE, status=JobStatus.QUEUED, input_uri="x")
    db_session.add(job)
    db_session.commit()

    claimed = _claim_job(session_factory, job.id, "worker-1")
    assert claimed is not None
    assert claimed.status == JobStatus.PROCESSING
    assert claimed.worker_id == "worker-1"

    # A second claim attempt on the now-PROCESSING job must be rejected.
    second = _claim_job(session_factory, job.id, "worker-2")
    assert second is None


def test_complete_job_marks_completed(session_factory, db_session):
    job = Job(job_type=JobType.THUMBNAIL, status=JobStatus.PROCESSING, input_uri="x")
    db_session.add(job)
    db_session.commit()

    _complete_job(session_factory, job.id, "out/path.jpg", {"ok": True})

    db_session.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.output_uri == "out/path.jpg"
    assert job.result == {"ok": True}


def test_fail_job_retries_then_dead_letters(session_factory, db_session, fake_redis):
    settings = _settings()
    job = Job(job_type=JobType.TRANSCODE, status=JobStatus.PROCESSING, input_uri="x", max_retries=2)
    db_session.add(job)
    db_session.commit()

    status1 = _fail_job(session_factory, fake_redis, settings, job.id, "boom 1")
    db_session.refresh(job)
    assert status1 == JobStatus.RETRYING
    assert job.retries == 1
    assert fake_redis.zcard(settings.delayed_queue_key) == 1

    status2 = _fail_job(session_factory, fake_redis, settings, job.id, "boom 2")
    db_session.refresh(job)
    assert status2 == JobStatus.FAILED
    assert job.retries == 2
    assert job.error == "boom 2"
