"""Pytest fixtures.

Sets test-only environment variables (a dedicated Postgres database and an
isolated storage directory) *before* importing any `app.*` module, since
`app.db.session` creates its engine at import time from `Settings`.
"""

import os
import uuid
from collections.abc import Generator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/mediavault_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("ENV", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402,F401
    Asset,
    Folder,
    RefreshToken,
    Share,
    Tag,
    User,
    Workspace,
    WorkspaceMembership,
)

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _isolate_storage(tmp_path, monkeypatch) -> Generator[None, None, None]:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(storage_root))
    yield


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register(
    client: TestClient,
    email: str,
    password: str = "password123",
    full_name: str = "Test User",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def register_user():
    def _factory(client: TestClient, email: str | None = None, **kwargs) -> dict:
        email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
        return _register(client, email, **kwargs)

    return _factory


@pytest.fixture
def auth_headers():
    def _factory(token_bundle: dict) -> dict:
        return {"Authorization": f"Bearer {token_bundle['access_token']}"}

    return _factory


@pytest.fixture
def make_workspace():
    def _factory(client: TestClient, headers: dict, name: str = "Test Workspace") -> dict:
        slug = f"ws-{uuid.uuid4().hex[:10]}"
        response = client.post(
            "/api/v1/workspaces", json={"name": name, "slug": slug}, headers=headers
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _factory
