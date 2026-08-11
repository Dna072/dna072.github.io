"""Common/shared Pydantic schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Message(BaseModel):
    message: str


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str


class ReadinessStatus(BaseModel):
    status: str
    checks: dict[str, str]


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
