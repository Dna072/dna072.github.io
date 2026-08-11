"""SQLAlchemy ORM models for jobs and worker heartbeats."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .state_machine import JobStatus, JobType


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=UTC)


class Job(Base):
    """A single media processing job."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=JobStatus.PENDING.value, index=True
    )
    # Higher number == higher priority. 0 = normal, 10 = urgent.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Input descriptor + processing parameters (e.g. target resolution).
    input_uri: Mapped[str] = mapped_column(Text, nullable=False)
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Result descriptor written by the worker on success.
    output_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Retry bookkeeping.
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Idempotency: a client-supplied key that dedupes submissions.
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )

    # Which worker currently holds the lease, and until when.
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # When the job becomes eligible to run again (for backoff scheduling).
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # Idempotency key is unique when present (enforces dedupe at the DB).
        UniqueConstraint("idempotency_key", name="uq_jobs_idempotency_key"),
        Index("ix_jobs_status_priority", "status", "priority"),
        Index("ix_jobs_created_at", "created_at"),
    )

    def as_type(self) -> JobType:
        return JobType(self.job_type)

    def as_status(self) -> JobStatus:
        return JobStatus(self.status)


class WorkerHeartbeat(Base):
    """Liveness record for a worker process."""

    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="idle")
    current_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    jobs_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    jobs_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
