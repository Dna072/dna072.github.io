import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#2f6f5e")

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not HEX_COLOR_RE.match(value):
            raise ValueError("color must be a hex string like #2f6f5e")
        return value


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str
    created_at: datetime
    asset_count: int = 0
