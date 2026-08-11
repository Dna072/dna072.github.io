from __future__ import annotations

from sqlalchemy import select

from app.models.job import ProcessingJob
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
