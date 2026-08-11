import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import JobStatus, JobType, WorkerStatus


class JobCreate(BaseModel):
    job_type: JobType
    input_uri: str = Field(..., min_length=1, max_length=2048)
    params: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=0, le=10)
    max_retries: int = Field(default=3, ge=0, le=10)
    idempotency_key: str | None = Field(default=None, max_length=255)

    @field_validator("idempotency_key")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        return v or None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    priority: int
    input_uri: str
    output_uri: str | None
    params: dict[str, Any]
    result: dict[str, Any] | None
    idempotency_key: str | None
    retries: int
    max_retries: int
    error: str | None
    worker_id: str | None
    heartbeat_at: datetime | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class JobList(BaseModel):
    items: list[JobRead]
    total: int
    limit: int
    offset: int


class JobStats(BaseModel):
    by_status: dict[str, int]
    by_type: dict[str, int]
    total: int


class WorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hostname: str
    pid: int
    status: WorkerStatus
    current_job_id: uuid.UUID | None
    jobs_processed: int
    jobs_failed: int
    started_at: datetime
    last_heartbeat: datetime


class WorkerList(BaseModel):
    items: list[WorkerRead]
    total: int


class ErrorResponse(BaseModel):
    detail: str
