"""Shared pytest fixtures.

Configures the app for hermetic testing: a throwaway SQLite DB, the in-process
queue (no Redis needed), local storage in a temp dir, and forced mock
processing (no ffmpeg needed). Env vars are set *before* any app import so the
cached Settings pick them up.
"""

from __future__ import annotations

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="renderflow-tests-")
os.environ.update(
    {
        "RENDERFLOW_ENVIRONMENT": "test",
        "RENDERFLOW_DATABASE_URL": f"sqlite:///{_TMP}/test.db",
        "RENDERFLOW_REDIS_URL": "",
        "RENDERFLOW_STORAGE_BACKEND": "local",
        "RENDERFLOW_STORAGE_LOCAL_DIR": f"{_TMP}/storage",
        "RENDERFLOW_FORCE_MOCK_PROCESSING": "true",
        "RENDERFLOW_DEFAULT_MAX_RETRIES": "3",
        "RENDERFLOW_RETRY_BACKOFF_BASE_SECONDS": "0.01",
        "RENDERFLOW_RETRY_BACKOFF_MAX_SECONDS": "0.05",
        "RENDERFLOW_RETRY_BACKOFF_JITTER_SECONDS": "0",
        "RENDERFLOW_JOB_LEASE_SECONDS": "1",
        "RENDERFLOW_WORKER_STALE_AFTER_SECONDS": "2",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.queue import get_queue, reset_queue  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset DB tables and the in-memory queue before each test."""
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_queue()
    yield
    reset_queue()


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def queue():
    return get_queue()


@pytest.fixture
def client():
    # Import here so the app is created after env + DB are ready.
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
