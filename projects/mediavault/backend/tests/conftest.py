"""Pytest fixtures: isolated SQLite database and authenticated API clients."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Configure a throwaway SQLite database + local storage *before* importing app.
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db")
_STORAGE_DIR = tempfile.mkdtemp(prefix="mediavault-storage-")
os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL=f"sqlite:///{_DB_PATH}",
    STORAGE_BACKEND="local",
    STORAGE_LOCAL_DIR=_STORAGE_DIR,
    SECRET_KEY="test-secret-key",
    SIGNED_URL_SECRET="test-signed-secret",
    LOG_JSON="false",
    RATE_LIMIT_ENABLED="false",
)

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_schema() -> Iterator[None]:
    """Recreate all tables for every test for full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str, password: str = "Password123!") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict:
    data = _register(client, email, password)
    return {"Authorization": f"Bearer {data['tokens']['access_token']}"}


@pytest.fixture
def admin_headers(client: TestClient) -> dict:
    return auth_headers(client, "admin@example.com")


@pytest.fixture
def workspace(client: TestClient, admin_headers: dict) -> dict:
    resp = client.post(
        "/api/v1/workspaces",
        json={"name": "Creative Team", "description": "Test workspace"},
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
