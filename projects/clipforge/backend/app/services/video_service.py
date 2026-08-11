"""Video service: upload validation, storage, CRUD, and job orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.enums import JobStatus, VideoStatus
from app.models.job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.repositories.job_repo import JobRepository
from app.repositories.video_repo import VideoRepository
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.video import VideoUpdate
from app.utils.files import safe_extension, video_dir
from app.utils.text import title_from_filename
from app.workers.queue import get_queue

logger = get_logger("clipforge.video")


class VideoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.videos = VideoRepository(db)
        self.jobs = JobRepository(db)
        self.workspaces = WorkspaceRepository(db)

    # --- Validation ------------------------------------------------------
    def _validate_upload(
        self, filename: str, content_type: str, size_bytes: int
    ) -> None:
        ext = safe_extension(filename)
        if ext not in settings.allowed_video_extensions:
            raise ValidationError(
                f"Unsupported file extension '.{ext}'. Allowed: "
                + ", ".join(settings.allowed_video_extensions)
            )
        if content_type not in settings.allowed_video_mime_types:
            raise ValidationError(f"Unsupported content type '{content_type}'.")
        if size_bytes <= 0:
            raise ValidationError("Uploaded file is empty.")
        if size_bytes > settings.max_upload_bytes:
            raise ValidationError(
                f"File too large ({size_bytes} bytes). Max allowed is "
                f"{settings.max_upload_bytes} bytes."
            )

    def _stream_to_disk(self, video_id: str, filename: str, source: BinaryIO) -> tuple[Path, int]:
        """Persist an upload stream to disk, enforcing the size limit."""
        ext = safe_extension(filename)
        dest = video_dir(video_id) / f"source.{ext}"
        size = 0
        chunk_size = 1024 * 1024
        with open(dest, "wb") as out:
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    out.close()
                    shutil.rmtree(dest.parent, ignore_errors=True)
                    raise ValidationError(
                        f"File exceeds max upload size of "
                        f"{settings.max_upload_bytes} bytes."
                    )
                out.write(chunk)
        return dest, size

    # --- Commands --------------------------------------------------------
    def create_from_upload(
        self,
        user: User,
        workspace_id: str,
        *,
        filename: str,
        content_type: str,
        file: BinaryIO,
        declared_size: int | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> tuple[Video, ProcessingJob]:
        workspace = self.workspaces.get_for_owner(workspace_id, user.id)
        if not workspace:
            raise NotFoundError("Workspace not found.")

        # Cheap pre-check on the declared size (final check happens while streaming).
        if declared_size is not None:
            self._validate_upload(filename, content_type, declared_size)
        else:
            # Still validate extension/mime before writing bytes.
            self._validate_upload(filename, content_type, 1)

        video = Video(
            workspace_id=workspace.id,
            title=title or title_from_filename(filename),
            description=description,
            status=VideoStatus.UPLOADED,
            original_filename=filename,
            content_type=content_type,
            storage_path="",
            size_bytes=0,
        )
        self.videos.add(video)
        self.db.flush()

        dest, size = self._stream_to_disk(video.id, filename, file)
        # Final validation now that the true size is known.
        self._validate_upload(filename, content_type, size)
        video.storage_path = str(dest)
        video.size_bytes = size

        job = ProcessingJob(video_id=video.id, status=JobStatus.PENDING)
        self.jobs.add(job)

        video.status = VideoStatus.QUEUED
        self.db.commit()
        self.db.refresh(video)
        self.db.refresh(job)

        get_queue().enqueue(job.id)
        logger.info(
            "video_uploaded",
            extra={"video_id": video.id, "job_id": job.id, "size_bytes": size},
        )
        return video, job

    def update(self, user: User, video_id: str, payload: VideoUpdate) -> Video:
        video = self.get(user, video_id)
        if payload.title is not None:
            video.title = payload.title
        if payload.description is not None:
            video.description = payload.description
        if payload.tags is not None:
            video.tags = payload.tags
        self.db.commit()
        self.db.refresh(video)
        return video

    def delete(self, user: User, video_id: str) -> None:
        video = self.get(user, video_id)
        shutil.rmtree(video_dir(video.id), ignore_errors=True)
        self.videos.delete(video)
        self.db.commit()

    def reprocess(self, user: User, video_id: str) -> ProcessingJob:
        video = self.get(user, video_id)
        job = ProcessingJob(video_id=video.id, status=JobStatus.PENDING)
        self.jobs.add(job)
        video.status = VideoStatus.QUEUED
        video.error_message = None
        self.db.commit()
        self.db.refresh(job)
        get_queue().enqueue(job.id)
        return job

    # --- Queries ---------------------------------------------------------
    def get(self, user: User, video_id: str) -> Video:
        video = self.videos.get_for_owner(video_id, user.id)
        if not video:
            raise NotFoundError("Video not found.")
        return video

    def search(self, user: User, **kwargs) -> tuple[list[Video], int]:
        return self.videos.search(user.id, **kwargs)

    def latest_job(self, video_id: str) -> ProcessingJob | None:
        return self.jobs.latest_for_video(video_id)
