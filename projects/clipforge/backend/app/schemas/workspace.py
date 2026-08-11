from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspaceRead(ORMModel):
    id: str
    name: str
    slug: str
    owner_id: str
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(ORMModel):
    id: str
    name: str
    description: str | None
    workspace_id: str
    created_at: datetime
