from __future__ import annotations

from datetime import datetime

from app.models.job import JobStatus
from app.schemas.common import ORMModel


class JobStep(ORMModel):
    name: str
    status: str  # pending|running|succeeded|failed|skipped
    detail: str | None = None


class JobRead(ORMModel):
    id: str
    video_id: str
    status: JobStatus
    attempts: int
    max_attempts: int
    steps: list[JobStep] | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
