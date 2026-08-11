"""Processing job schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobStage, JobStatus


class JobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    video_id: str
    status: JobStatus
    stage: JobStage
    progress: int
    attempts: int
    stage_history: list[dict[str, Any]] | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
