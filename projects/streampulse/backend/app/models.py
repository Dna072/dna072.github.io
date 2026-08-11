"""SQLAlchemy ORM models.

Schema overview
---------------
users
    Dashboard operators who can log in and view analytics.
videos
    Catalogue of published videos.
view_events
    One row per playback session. This is the primary fact table behind
    overview / time-series / geo / device metrics.
engagement_events
    One row per funnel/engagement milestone (play, 25/50/75% reached,
    completed, like, comment, share) tied to a playback session. Backs the
    engagement funnel and the "likes/comments/shares" KPIs.

See README.md "Database indexes" for the rationale behind each index below.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeviceType(str, enum.Enum):
    desktop = "desktop"
    mobile = "mobile"
    tablet = "tablet"
    tv = "tv"


class EngagementType(str, enum.Enum):
    play = "play"
    reach_25 = "reach_25"
    reach_50 = "reach_50"
    reach_75 = "reach_75"
    complete = "complete"
    like = "like"
    comment = "comment"
    share = "share"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    view_events: Mapped[list["ViewEvent"]] = relationship(back_populates="video")
    engagement_events: Mapped[list["EngagementEvent"]] = relationship(back_populates="video")

    __table_args__ = (Index("ix_videos_published_at", "published_at"),)


class ViewEvent(Base):
    """A single playback session for a video."""

    __tablename__ = "view_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    viewer_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    watch_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    watch_percent: Mapped[float] = mapped_column(Float, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType, name="device_type"), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    referrer_source: Mapped[str] = mapped_column(String(50), nullable=False)

    video: Mapped["Video"] = relationship(back_populates="view_events")

    __table_args__ = (
        Index("ix_view_events_video_occurred", "video_id", "occurred_at"),
        Index("ix_view_events_occurred", "occurred_at"),
        Index("ix_view_events_device", "device_type"),
        Index("ix_view_events_country", "country_code"),
    )


class EngagementEvent(Base):
    """A funnel/engagement milestone tied to a playback session."""

    __tablename__ = "engagement_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    viewer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[EngagementType] = mapped_column(
        Enum(EngagementType, name="engagement_type"), nullable=False
    )

    video: Mapped["Video"] = relationship(back_populates="engagement_events")

    __table_args__ = (
        Index("ix_engagement_events_video_occurred", "video_id", "occurred_at"),
        Index("ix_engagement_events_type_occurred", "event_type", "occurred_at"),
    )
