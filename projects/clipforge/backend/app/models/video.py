from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.json_type import JSONType
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import ProcessingJob
    from app.models.project import Project


class VideoStatus(str, enum.Enum):
    """Lifecycle of a video through the processing pipeline."""

    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "videos"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uploaded_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(300), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(700), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus, native_enum=False, length=20),
        default=VideoStatus.UPLOADED,
        index=True,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Extracted media metadata (populated by the worker via ffprobe) ---
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    codec: Mapped[str | None] = mapped_column(String(60), nullable=True)
    frame_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    bitrate: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # --- Derived assets ---
    thumbnail_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(700), nullable=True)

    # --- AI / transcript outputs ---
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chapters: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONType, nullable=True)

    project: Mapped[Project] = relationship(back_populates="videos")
    jobs: Mapped[list[ProcessingJob]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )

    @property
    def searchable_text(self) -> str:
        parts = [self.title, self.summary or "", " ".join(self.tags or [])]
        return " ".join(parts).lower()
