"""Database engine and session management (SQLAlchemy 2.0 style)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    connect_args: dict = {}
    # SQLite (used for local dev / tests) needs this flag when shared across
    # threads (the API + TestClient run in different threads).
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )


engine = _make_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def init_db() -> None:
    """Create tables. Real deployments use Alembic; this keeps demos simple."""
    from . import models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
