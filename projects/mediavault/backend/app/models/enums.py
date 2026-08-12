"""Enumerations shared across models and schemas."""

from __future__ import annotations

import enum


class Role(str, enum.Enum):
    """Workspace-scoped role governing what a member may do."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"

    @property
    def rank(self) -> int:
        return {"VIEWER": 0, "MEMBER": 1, "ADMIN": 2}[self.value]

    def at_least(self, other: Role) -> bool:
        return self.rank >= other.rank


class AssetStatus(str, enum.Enum):
    """Lifecycle state of an uploaded asset."""

    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class AssetKind(str, enum.Enum):
    """Coarse asset category derived from content type."""

    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"

    @classmethod
    def from_content_type(cls, content_type: str) -> AssetKind:
        if content_type.startswith("video/"):
            return cls.VIDEO
        if content_type.startswith("image/"):
            return cls.IMAGE
        if content_type in {"application/pdf"} or content_type.startswith("text/"):
            return cls.DOCUMENT
        return cls.OTHER
