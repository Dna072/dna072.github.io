from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class Message(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    environment: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: bool
    redis: bool
    checked_at: datetime = Field(default_factory=datetime.utcnow)
