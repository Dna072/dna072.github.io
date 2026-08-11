"""Database engine and session management (synchronous SQLAlchemy 2.0)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine(url: str):
    """Create an engine with driver-appropriate connect args."""
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Needed so SQLite connections can be shared across FastAPI threads.
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )


engine = _build_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
