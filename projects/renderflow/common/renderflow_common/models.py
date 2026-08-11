import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .db_types import GUID
from .enums import JobStatus, JobType, WorkerStatus


def utcnow() -> datetime:
    return datetime.now(UTC)


def _pg_enum(enum_cls, name: str) -> Enum:
    """SQLAlchemy `Enum` that stores the lowercase `.value` (e.g. "queued")
    rather than the Python member name (e.g. "QUEUED"), so the raw DB rows
    match the JSON the API returns and are easy to read/filter by hand."""
    return Enum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class Base(DeclarativeBase):
    pass


class Job(Base):
    """A single unit of media-processing work.

    The state machine documented in `enums.JobStatus` is enforced in
    `app.services.job_service` / `worker.processor`, not at the DB layer,
    so it stays easy to unit test without a live database.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    job_type: Mapped[JobType] = mapped_column(_pg_enum(JobType, "job_type"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        _pg_enum(JobStatus, "job_status"), nullable=False, default=JobStatus.PENDING, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, index=True)

    input_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    output_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )

    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Job {self.id} {self.job_type} {self.status}>"


class Worker(Base):
    """Registry row updated by heartbeats; powers the ops UI worker list."""

    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkerStatus] = mapped_column(
        _pg_enum(WorkerStatus, "worker_status"), nullable=False, default=WorkerStatus.IDLE
    )
    current_job_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    jobs_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    current_job: Mapped[Job | None] = relationship("Job", lazy="joined", viewonly=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Worker {self.id} {self.status}>"
