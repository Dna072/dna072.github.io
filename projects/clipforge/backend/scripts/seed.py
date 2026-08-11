"""Seed the database with a demo user, workspace, and processed videos.

Idempotent: running it repeatedly will not create duplicate demo data. Sample
videos are pushed through the real pipeline synchronously (in mock media/AI
mode) so the demo account has fully-processed content immediately.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package is importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.enums import JobStatus, VideoStatus  # noqa: E402
from app.models.job import ProcessingJob  # noqa: E402
from app.models.video import Video  # noqa: E402
from app.schemas.auth import UserRegister  # noqa: E402
from app.schemas.workspace import WorkspaceCreate  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.workspace_service import WorkspaceService  # noqa: E402
from app.utils.files import video_dir  # noqa: E402
from app.workers.pipeline import run_pipeline  # noqa: E402

logger = get_logger("clipforge.seed")

DEMO_EMAIL = "demo@clipforge.dev"
DEMO_PASSWORD = "clipforge123"
DEMO_NAME = "Demo Creator"

SAMPLE_VIDEOS = [
    ("Product Launch Keynote", "Highlights from the Q3 product launch event."),
    ("Engineering Deep Dive", "How we built the async processing pipeline."),
    ("Onboarding Tutorial", "A walkthrough for new team members."),
    ("Customer Interview", "Conversation about workflows and pain points."),
]


def _create_placeholder_source(video: Video) -> str:
    """Write a small placeholder source file so pipeline paths resolve."""
    dest = video_dir(video.id) / "source.mp4"
    dest.write_bytes(b"CLIPFORGE_DEMO_PLACEHOLDER" * 64)
    return str(dest)


def seed() -> None:
    configure_logging("INFO", json_output=False)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        auth = AuthService(db)
        existing = auth.users.get_by_email(DEMO_EMAIL)
        if existing:
            logger.info("demo_user_exists", extra={"email": DEMO_EMAIL})
            print(f"Demo user already exists: {DEMO_EMAIL} / {DEMO_PASSWORD}")
            return

        user = auth.register(
            UserRegister(
                email=DEMO_EMAIL, password=DEMO_PASSWORD, full_name=DEMO_NAME
            )
        )
        workspace = WorkspaceService(db).create(
            user, WorkspaceCreate(name="Demo Studio", description="Sample content")
        )

        for title, description in SAMPLE_VIDEOS:
            video = Video(
                workspace_id=workspace.id,
                title=title,
                description=description,
                status=VideoStatus.QUEUED,
                original_filename=f"{title.lower().replace(' ', '_')}.mp4",
                content_type="video/mp4",
                storage_path="",
                size_bytes=0,
            )
            db.add(video)
            db.flush()
            video.storage_path = _create_placeholder_source(video)
            video.size_bytes = Path(video.storage_path).stat().st_size
            job = ProcessingJob(video_id=video.id, status=JobStatus.PENDING)
            db.add(job)
            db.commit()

            # Process synchronously so seeded content is immediately "ready".
            run_pipeline(db, job.id)

        print("Seed complete.")
        print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Workspace: {workspace.name}")
        print(f"  Videos: {len(SAMPLE_VIDEOS)} (processed)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
