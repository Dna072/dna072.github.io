import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.membership import WorkspaceRole

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = value.lower().strip()
        if not SLUG_RE.match(value):
            raise ValueError(
                "slug must be lowercase alphanumeric with single hyphens (e.g. 'my-team')"
            )
        return value


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    created_at: datetime
    my_role: WorkspaceRole | None = None
    member_count: int = 0
    asset_count: int = 0


class MembershipCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: WorkspaceRole = WorkspaceRole.MEMBER


class MembershipUpdate(BaseModel):
    role: WorkspaceRole


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    created_at: datetime
    user_email: str
    user_full_name: str
