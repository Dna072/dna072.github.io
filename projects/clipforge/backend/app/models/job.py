"""Processing job ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONType
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import JobStage, JobStatus

if TYPE_CHECKING:
    from app.models.video import Video


class ProcessingJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "processing_jobs"

    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    video: Mapped["Video"] = relationship(back_populates="jobs")

    status: Mapped[JobStatus] = mapped_column(
        String(20), default=JobStatus.PENDING, nullable=False, index=True
    )
    stage: Mapped[JobStage] = mapped_column(
        String(20), default=JobStage.QUEUED, nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Human-readable stage log for observability / UI timeline.
    stage_history: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONType, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
