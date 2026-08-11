from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Thin data-access wrapper around a SQLAlchemy model.

    Keeps ORM/query concerns out of the service layer so business logic stays
    testable and storage details can change independently.
    """

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: str) -> ModelT | None:
        return self.db.get(self.model, id_)

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
