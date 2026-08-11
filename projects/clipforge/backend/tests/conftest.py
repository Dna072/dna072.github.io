"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database and an in-memory job
queue, so no PostgreSQL, Redis, or network access is required. AI defaults to the
MockAIProvider.
"""

from __future__ import annotations

import io
from collections.abc import Generator

import pytest
from app.core.database import Base, get_db
from app.main import create_app
from app.services.queue import InMemoryQueue, set_queue
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    import app.models  # noqa: F401 -- register models

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def memory_queue() -> InMemoryQueue:
    q = InMemoryQueue()
    set_queue(q)
    yield q
    set_queue(None)


@pytest.fixture
def client(engine, memory_queue) -> Generator[TestClient, None, None]:
    """A TestClient sharing the in-memory engine via a dependency override."""
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    app = create_app()

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    payload = {
        "email": "tester@example.com",
        "full_name": "Test Person",
        "password": "supersecret1",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    return {"user": resp.json(), "tokens": tokens, "password": payload["password"]}


@pytest.fixture
def auth_client(client: TestClient, registered_user: dict) -> TestClient:
    token = registered_user["tokens"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def sample_video_bytes() -> io.BytesIO:
    # A tiny non-empty payload; MockAI/pipeline don't require valid video content
    # (ffprobe/ffmpeg stages degrade gracefully on undecodable input).
    return io.BytesIO(b"\x00\x00\x00\x18ftypmp42" + b"clipforge-test" * 64)
