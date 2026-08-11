"""Shared enumerations used by models and schemas."""

from __future__ import annotations

from enum import Enum


class VideoStatus(str, Enum):
    """Lifecycle of an uploaded video."""

    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class JobStatus(str, Enum):
    """Lifecycle of a processing job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(str, Enum):
    """Discrete stages of the processing pipeline (for observability)."""

    QUEUED = "queued"
    PROBE = "probe"
    THUMBNAIL = "thumbnail"
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    AI_ANALYSIS = "ai_analysis"
    PERSIST = "persist"
    DONE = "done"


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
