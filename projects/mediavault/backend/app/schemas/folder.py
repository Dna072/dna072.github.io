"""Folder schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: uuid.UUID | None = None


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: uuid.UUID | None = None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    path: str
    created_at: datetime


class FolderTree(FolderRead):
    children: list[FolderTree] = []
    asset_count: int = 0


FolderTree.model_rebuild()


class Breadcrumb(BaseModel):
    id: uuid.UUID
    name: str
