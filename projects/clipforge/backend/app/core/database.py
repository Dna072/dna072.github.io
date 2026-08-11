"""SQLAlchemy engine and session management."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _make_engine(url: str):
    connect_args: dict = {}
    engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        # Used by the test-suite for a fast, isolated in-memory database.
        from sqlalchemy.pool import StaticPool

        connect_args["check_same_thread"] = False
        engine_kwargs["poolclass"] = StaticPool
    return create_engine(url, connect_args=connect_args, **engine_kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
