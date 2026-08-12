"""Workspace and membership schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Role
from app.schemas.user import UserRead


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = Field(default="", max_length=2000)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str
    owner_id: uuid.UUID
    created_at: datetime


class WorkspaceWithRole(WorkspaceRead):
    role: Role


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user: UserRead
    role: Role
    created_at: datetime


class MemberInvite(BaseModel):
    email: str
    role: Role = Role.MEMBER


class MemberRoleUpdate(BaseModel):
    role: Role
