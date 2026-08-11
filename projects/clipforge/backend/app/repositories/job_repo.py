"""Processing job repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.enums import JobStatus
from app.models.job import ProcessingJob
from app.models.video import Video
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[ProcessingJob]):
    model = ProcessingJob

    def latest_for_video(self, video_id: str) -> ProcessingJob | None:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.video_id == video_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_for_owner(self, job_id: str, owner_id: str) -> ProcessingJob | None:
        stmt = (
            select(ProcessingJob)
            .join(Video, ProcessingJob.video_id == Video.id)
            .join(Workspace, Video.workspace_id == Workspace.id)
            .where(ProcessingJob.id == job_id, Workspace.owner_id == owner_id)
        )
        return self.db.scalar(stmt)

    def count_active_for_owner(self, owner_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ProcessingJob)
            .join(Video, ProcessingJob.video_id == Video.id)
            .join(Workspace, Video.workspace_id == Workspace.id)
            .where(
                Workspace.owner_id == owner_id,
                ProcessingJob.status.in_(
                    [JobStatus.PENDING, JobStatus.RUNNING]
                ),
            )
        )
        return int(self.db.scalar(stmt) or 0)
