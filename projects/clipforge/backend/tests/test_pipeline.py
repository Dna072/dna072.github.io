"""Processing pipeline tests using the mock AI provider."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.security import hash_password
from app.models.enums import JobStage, JobStatus, VideoStatus
from app.models.job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.models.workspace import Workspace
from app.services.ai.mock_provider import MockAIProvider
from app.utils.files import video_dir
from app.workers.pipeline import PipelineError, run_pipeline


def _make_video(db) -> tuple[Video, ProcessingJob]:
    user = User(
        email="pipe@example.com",
        full_name="Pipe",
        hashed_password=hash_password("password123"),
    )
    db.add(user)
    db.flush()
    workspace = Workspace(name="WS", slug="ws", owner_id=user.id)
    db.add(workspace)
    db.flush()
    video = Video(
        workspace_id=workspace.id,
        title="Clip",
        status=VideoStatus.QUEUED,
        original_filename="clip.mp4",
        content_type="video/mp4",
        storage_path="",
        size_bytes=0,
    )
    db.add(video)
    db.flush()
    # Write a placeholder source so file paths resolve (ffmpeg falls back to mock).
    source = video_dir(video.id) / "source.mp4"
    source.write_bytes(b"PLACEHOLDER" * 32)
    video.storage_path = str(source)
    video.size_bytes = source.stat().st_size
    job = ProcessingJob(video_id=video.id, status=JobStatus.PENDING)
    db.add(job)
    db.commit()
    return video, job


def test_pipeline_completes_and_populates_outputs(db):
    video, job = _make_video(db)

    run_pipeline(db, job.id, ai=MockAIProvider())

    db.refresh(video)
    db.refresh(job)

    assert job.status == JobStatus.COMPLETED
    assert job.stage == JobStage.DONE
    assert job.progress == 100
    assert job.started_at is not None
    assert job.finished_at is not None

    assert video.status == VideoStatus.READY
    assert video.duration_seconds and video.duration_seconds > 0
    assert video.transcript
    assert video.summary
    assert video.chapters and len(video.chapters) >= 3
    assert video.tags and len(video.tags) >= 3
    assert video.thumbnail_path and Path(video.thumbnail_path).exists()


def test_pipeline_records_stage_history(db):
    _, job = _make_video(db)
    run_pipeline(db, job.id, ai=MockAIProvider())
    db.refresh(job)

    stages = [entry["stage"] for entry in job.stage_history]
    for expected in ["probe", "thumbnail", "audio", "transcript", "ai_analysis", "done"]:
        assert expected in stages


def test_pipeline_missing_job_raises(db):
    with pytest.raises(PipelineError):
        run_pipeline(db, "nonexistent-job-id", ai=MockAIProvider())


def test_mock_provider_is_deterministic():
    provider = MockAIProvider()
    a = provider.analyze("Hello world. This is a test.", duration=120)
    b = provider.analyze("Hello world. This is a test.", duration=120)
    assert a.summary == b.summary
    assert a.tags == b.tags
