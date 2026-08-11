"""Shared pytest fixtures.

Environment variables are configured *before* application modules are imported
so the cached Settings pick up a throwaway SQLite database and the mock AI
provider. The job queue is stubbed so uploads do not spawn background workers
during API tests; pipeline behaviour is exercised directly in test_pipeline.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

# --- Configure environment before importing the app ------------------------
_TMP = tempfile.mkdtemp(prefix="clipforge-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["STORAGE_DIR"] = f"{_TMP}/storage"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["AI_PROVIDER"] = "mock"
os.environ["BCRYPT_ROUNDS"] = "4"  # faster hashing in tests
os.environ["LOG_JSON"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


class _StubQueue:
    """Records enqueued job ids without running any work."""

    backend = "stub"

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)


@pytest.fixture(autouse=True)
def _reset_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Path(os.environ["STORAGE_DIR"]).mkdir(parents=True, exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _stub_queue(monkeypatch) -> _StubQueue:
    """Replace the real queue everywhere it is used during tests."""
    stub = _StubQueue()
    monkeypatch.setattr("app.workers.queue.get_queue", lambda: stub)
    monkeypatch.setattr("app.services.video_service.get_queue", lambda: stub)
    return stub


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A TestClient with an authenticated demo user + default workspace."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tester@example.com",
            "password": "supersecret1",
            "full_name": "Tester",
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()["tokens"]
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    return client
