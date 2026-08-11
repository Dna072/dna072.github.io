"""Seed the database with a demo user, workspace, project, and a completed video.

Idempotent: safe to run multiple times. The sample video is populated with
realistic AI metadata (via MockAIProvider) and marked ``completed`` so the UI has
content to show immediately after ``docker compose up``.

Usage: ``python -m scripts.seed``
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.database import Base, SessionLocal, engine
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.models.job import JobStatus, ProcessingJob
from app.models.project import Project
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.workspace import Workspace, WorkspaceMember
from app.services.ai.mock import MockAIProvider

configure_logging(json_logs=False)
logger = get_logger("seed")

DEMO_EMAIL = "demo@clipforge.dev"
DEMO_PASSWORD = "demo12345"


def seed() -> None:
    # Ensure tables exist even if migrations have not been run (dev convenience).
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).one_or_none()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                full_name="Demo User",
                hashed_password=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            db.flush()
            logger.info("created_user", email=DEMO_EMAIL)

        workspace = (
            db.query(Workspace).filter(Workspace.owner_id == user.id).first()
        )
        if workspace is None:
            workspace = Workspace(name="Demo Workspace", slug="demo-workspace", owner_id=user.id)
            db.add(workspace)
            db.flush()
            db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
            db.flush()

        project = (
            db.query(Project).filter(Project.workspace_id == workspace.id).first()
        )
        if project is None:
            project = Project(
                name="Product Marketing",
                description="Launch videos, tutorials, and demos.",
                workspace_id=workspace.id,
            )
            db.add(project)
            db.flush()

        existing = db.query(Video).filter(Video.project_id == project.id).count()
        if existing == 0:
            ai = MockAIProvider()
            samples = [
                ("Q3 Product Launch Keynote", 372.0, 1920, 1080, "h264", 30.0),
                ("Onboarding Tutorial — Getting Started", 154.0, 1280, 720, "h264", 30.0),
                ("Engineering Deep Dive: Async Pipelines", 641.0, 1920, 1080, "vp9", 24.0),
            ]
            for title, duration, w, h, codec, fps in samples:
                transcript = ai.transcribe("", duration_seconds=duration)
                insights = ai.analyze(transcript.text, title=title, duration_seconds=duration)
                video = Video(
                    project_id=project.id,
                    uploaded_by=user.id,
                    title=title,
                    original_filename=f"{title.lower().replace(' ', '_')}.mp4",
                    storage_path=f"videos/sample/{title[:8]}.mp4",
                    content_type="video/mp4",
                    size_bytes=int(duration * 1_250_000),
                    status=VideoStatus.COMPLETED,
                    duration_seconds=duration,
                    width=w,
                    height=h,
                    codec=codec,
                    frame_rate=fps,
                    bitrate=5_000_000,
                    transcript=transcript.text,
                    summary=insights.summary,
                    chapters=[{"start": c.start, "title": c.title} for c in insights.chapters],
                    tags=insights.tags,
                )
                db.add(video)
                db.flush()
                db.add(
                    ProcessingJob(
                        video_id=video.id,
                        status=JobStatus.SUCCEEDED,
                        attempts=1,
                        steps=[
                            {"name": s, "status": "succeeded"}
                            for s in ["metadata", "thumbnail", "audio", "transcript", "ai_insights"]
                        ],
                        started_at=datetime.now(UTC),
                        finished_at=datetime.now(UTC),
                    )
                )
            logger.info("created_sample_videos", count=len(samples))

        db.commit()
        logger.info(
            "seed_complete",
            login_email=DEMO_EMAIL,
            login_password=DEMO_PASSWORD,
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
