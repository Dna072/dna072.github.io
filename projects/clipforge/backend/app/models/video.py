"""Video ORM model and related processing artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONType
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import VideoStatus

if TYPE_CHECKING:
    from app.models.job import ProcessingJob
    from app.models.workspace import Workspace


class Video(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "videos"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workspace: Mapped["Workspace"] = relationship(back_populates="videos")

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        String(20), default=VideoStatus.UPLOADED, nullable=False, index=True
    )

    # Upload metadata
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Probed media metadata (populated by pipeline)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # AI + transcript outputs
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chapters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
