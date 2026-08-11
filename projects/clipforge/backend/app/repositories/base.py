"""Generic repository base implementing common CRUD operations."""

from __future__ import annotations

from typing import Generic, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Thin data-access layer over a SQLAlchemy model.

    Repositories intentionally do not commit; the service layer owns the
    transaction boundary so multiple operations can be committed atomically.
    """

    model: Type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> ModelT | None:
        return self.db.get(self.model, id_)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(self.model)) or 0)
