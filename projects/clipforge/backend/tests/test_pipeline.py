from __future__ import annotations

import io

from app.models.job import JobStatus, ProcessingJob
from app.models.project import Project
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.workspace import Workspace, WorkspaceMember
from app.services.ai.mock import MockAIProvider
from app.services.pipeline import ProcessingPipeline
from app.services.storage import LocalStorage


def _seed_video(db, store: LocalStorage) -> tuple[Video, ProcessingJob]:
    user = User(email="p@b.com", full_name="P", hashed_password="x")
    db.add(user)
    db.flush()
    ws = Workspace(name="W", slug="w", owner_id=user.id)
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))
    project = Project(name="Proj", workspace_id=ws.id)
    db.add(project)
    db.flush()

    video = Video(
        project_id=project.id,
        uploaded_by=user.id,
        title="Pipeline Test Clip",
        original_filename="clip.mp4",
        storage_path="videos/vid1/source.mp4",
        content_type="video/mp4",
        size_bytes=1234,
        status=VideoStatus.QUEUED,
    )
    db.add(video)
    db.flush()
    store.save_stream(video.storage_path, io.BytesIO(b"not-a-real-video" * 100))

    job = ProcessingJob(
        video_id=video.id,
        status=JobStatus.QUEUED,
        steps=[
            {"name": s, "status": "pending"}
            for s in ["metadata", "thumbnail", "audio", "transcript", "ai_insights"]
        ],
    )
    db.add(job)
    db.commit()
    return video, job


def test_pipeline_completes_with_mock_ai(db_session, tmp_path):
    store = LocalStorage(str(tmp_path))
    video, job = _seed_video(db_session, store)

    pipeline = ProcessingPipeline(db_session, ai=MockAIProvider(), store=store)
    result = pipeline.run(job.id)

    assert result.status == JobStatus.SUCCEEDED
    db_session.refresh(video)
    assert video.status == VideoStatus.COMPLETED
    assert video.transcript
    assert video.summary
    assert video.chapters and len(video.chapters) >= 1
    assert video.tags and len(video.tags) >= 1


def test_pipeline_records_step_progress(db_session, tmp_path):
    store = LocalStorage(str(tmp_path))
    _, job = _seed_video(db_session, store)
    pipeline = ProcessingPipeline(db_session, ai=MockAIProvider(), store=store)
    result = pipeline.run(job.id)

    names = {s["name"]: s["status"] for s in result.steps}
    assert names["transcript"] == "succeeded"
    assert names["ai_insights"] == "succeeded"
    # metadata always runs; thumbnail/audio may be 'skipped' on undecodable input
    assert names["metadata"] in {"succeeded", "skipped"}


def test_pipeline_failure_marks_failed(db_session, tmp_path):
    store = LocalStorage(str(tmp_path))
    video, job = _seed_video(db_session, store)

    class ExplodingAI(MockAIProvider):
        def analyze(self, *a, **k):  # type: ignore[override]
            raise RuntimeError("ai boom")

    pipeline = ProcessingPipeline(db_session, ai=ExplodingAI(), store=store)
    import pytest
    from app.services.pipeline import PipelineError

    with pytest.raises(PipelineError):
        pipeline.run(job.id)

    db_session.refresh(job)
    db_session.refresh(video)
    # First failure re-queues for retry (attempts < max_attempts).
    assert job.error_message is not None
    assert "ai boom" in job.error_message
