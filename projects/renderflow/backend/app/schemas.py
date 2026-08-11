"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .state_machine import JobStatus, JobType


class JobCreate(BaseModel):
    """Payload for submitting a new job."""

    job_type: JobType
    input_uri: str = Field(
        ...,
        min_length=1,
        description="Source media URI (local path, http, or s3://).",
    )
    params: dict = Field(
        default_factory=dict,
        description="Processor-specific parameters (e.g. {'height': 720}).",
    )
    priority: int = Field(default=0, ge=0, le=10)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    idempotency_key: str | None = Field(default=None, max_length=128)


class JobRead(BaseModel):
    """Full job representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: JobType
    status: JobStatus
    priority: int
    input_uri: str
    params: dict
    output_uri: str | None
    result: dict | None
    retries: int
    max_retries: int
    error_message: str | None
    idempotency_key: str | None
    worker_id: str | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobList(BaseModel):
    items: list[JobRead]
    total: int
    limit: int
    offset: int


class JobStatusCounts(BaseModel):
    counts: dict[str, int]
    total: int


class WorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    hostname: str | None
    status: str
    current_job_id: str | None
    jobs_processed: int
    jobs_failed: int
    started_at: datetime
    last_heartbeat_at: datetime
    # Derived field: whether the worker is considered alive.
    healthy: bool = True
    seconds_since_heartbeat: float = 0.0


class WorkerList(BaseModel):
    items: list[WorkerRead]
    total: int
    online: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


class MessageResponse(BaseModel):
    message: str
