"""Video upload, validation, and lifecycle orchestration."""

from __future__ import annotations

from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.job import JobStatus, ProcessingJob
from app.models.video import Video, VideoStatus
from app.repositories.job import JobRepository
from app.repositories.video import VideoRepository
from app.schemas.video import VideoUpdate
from app.services.queue import JobQueue, get_queue
from app.services.storage import LocalStorage, storage
from app.services.workspace_service import WorkspaceService

logger = get_logger(__name__)

_PIPELINE_STEPS = ["metadata", "thumbnail", "audio", "transcript", "ai_insights"]


class UploadValidationError(ValidationError):
    pass


class VideoService:
    def __init__(
        self,
        db: Session,
        *,
        queue: JobQueue | None = None,
        store: LocalStorage | None = None,
    ) -> None:
        self.db = db
        self.videos = VideoRepository(db)
        self.jobs = JobRepository(db)
        self.workspaces = WorkspaceService(db)
        self.queue = queue or get_queue()
        self.storage = store or storage

    # --- validation ---------------------------------------------------------
    @staticmethod
    def validate_upload(filename: str, content_type: str, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise UploadValidationError("Uploaded file is empty")
        if size_bytes > settings.max_upload_bytes:
            mb = settings.max_upload_bytes // (1024 * 1024)
            raise UploadValidationError(f"File exceeds the maximum size of {mb} MB")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.allowed_video_extensions:
            allowed = ", ".join(settings.allowed_video_extensions)
            raise UploadValidationError(
                f"Unsupported file extension '.{ext}'. Allowed: {allowed}"
            )
        if content_type not in settings.allowed_video_mime_types:
            raise UploadValidationError(f"Unsupported content type '{content_type}'")

    # --- creation -----------------------------------------------------------
    def create_video(
        self,
        *,
        project_id: str,
        user_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        stream: BinaryIO,
        title: str | None = None,
    ) -> Video:
        project = self.workspaces.get_project(project_id, user_id)
        self.validate_upload(filename, content_type, size_bytes)

        video = Video(
            project_id=project.id,
            uploaded_by=user_id,
            title=title or filename.rsplit(".", 1)[0],
            original_filename=filename,
            storage_path="",  # set after we know the id
            content_type=content_type,
            size_bytes=size_bytes,
            status=VideoStatus.UPLOADED,
        )
        self.videos.add(video)

        key = f"videos/{video.id}/source.{filename.rsplit('.', 1)[-1].lower()}"
        written = self.storage.save_stream(key, stream)
        # Re-validate size against bytes actually written (defence in depth).
        if written > settings.max_upload_bytes:
            self.storage.delete_prefix(f"videos/{video.id}")
            raise UploadValidationError("File exceeds the maximum size")
        video.storage_path = key
        video.size_bytes = written
        self.db.commit()
        self.db.refresh(video)

        self.enqueue_processing(video)
        return video

    def enqueue_processing(self, video: Video) -> ProcessingJob:
        job = ProcessingJob(
            video_id=video.id,
            status=JobStatus.QUEUED,
            steps=[{"name": s, "status": "pending"} for s in _PIPELINE_STEPS],
        )
        self.jobs.add(job)
        video.status = VideoStatus.QUEUED
        video.error_message = None
        self.db.commit()
        self.db.refresh(job)

        self.queue.enqueue({"job_id": job.id, "video_id": video.id})
        logger.info("processing_enqueued", video_id=video.id, job_id=job.id)
        return job

    # --- reads --------------------------------------------------------------
    def get_video(self, video_id: str, user_id: str) -> Video:
        video = self.videos.get_for_user(video_id, user_id)
        if video is None:
            raise NotFoundError("Video not found")
        return video

    def get_latest_job(self, video_id: str, user_id: str) -> ProcessingJob | None:
        self.get_video(video_id, user_id)
        return self.jobs.latest_for_video(video_id)

    def update_video(self, video_id: str, user_id: str, data: VideoUpdate) -> Video:
        video = self.get_video(video_id, user_id)
        if data.title is not None:
            video.title = data.title
        self.db.commit()
        self.db.refresh(video)
        return video

    def delete_video(self, video_id: str, user_id: str) -> None:
        video = self.get_video(video_id, user_id)
        self.storage.delete_prefix(f"videos/{video.id}")
        self.videos.delete(video)
        self.db.commit()

    def reprocess(self, video_id: str, user_id: str) -> ProcessingJob:
        video = self.get_video(video_id, user_id)
        return self.enqueue_processing(video)
