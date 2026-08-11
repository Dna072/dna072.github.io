"""Pytest fixtures.

Tests run against a real PostgreSQL database (the analytics queries use
``date_trunc``, ``count(distinct)`` and ``FILTER``-style conditional
aggregation that SQLite cannot emulate). Point ``TEST_DATABASE_URL`` at a
throwaway database; the schema is created/dropped per session.
"""

import os
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Always target a dedicated test database. TEST_DATABASE_URL wins over any
# inherited DATABASE_URL so tests can never accidentally drop a dev database.
_TEST_URL = os.environ.get("TEST_DATABASE_URL") or (
    "postgresql+psycopg2://streampulse:streampulse@localhost:5433/streampulse_test"
)
if "_test" not in _TEST_URL:
    raise RuntimeError(
        "Refusing to run tests: TEST_DATABASE_URL must point at a *_test database "
        f"(got {_TEST_URL!r})."
    )
os.environ["DATABASE_URL"] = _TEST_URL
os.environ.setdefault("LOG_JSON", "false")

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.analytics import ImpressionEvent, Video, ViewEvent  # noqa: E402
from app.models.user import User  # noqa: E402

TEST_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

TEST_EMAIL = "tester@streampulse.dev"
TEST_PASSWORD = "test-password"


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def seeded():
    """Insert a small, fully deterministic dataset used across tests."""
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
    with TestingSessionLocal() as db:
        db.add(
            User(
                email=TEST_EMAIL,
                full_name="Tester",
                hashed_password=hash_password(TEST_PASSWORD),
                is_active=True,
            )
        )
        v1 = Video(
            title="Alpha",
            category="Tutorials",
            duration_seconds=100,
            published_at=now - timedelta(days=40),
        )
        v2 = Video(
            title="Beta",
            category="Shorts",
            duration_seconds=60,
            published_at=now - timedelta(days=40),
        )
        db.add_all([v1, v2])
        db.flush()

        # Current period: 4 views on day now-2, spread across 2 viewers.
        def view(video, day, viewer, q, country, device, liked=False):
            return ViewEvent(
                video_id=video.id,
                viewer_id=viewer,
                event_time=now - timedelta(days=day),
                country_code=country,
                device_type=device,
                watch_seconds=int(video.duration_seconds * q / 4),
                quartile_reached=q,
                liked=liked,
            )

        db.add_all(
            [
                view(v1, 2, "u1", 4, "US", "mobile", liked=True),
                view(v1, 2, "u1", 2, "US", "desktop"),
                view(v1, 3, "u2", 4, "GB", "mobile", liked=True),
                view(v2, 2, "u2", 1, "US", "tv"),
            ]
        )
        # Previous period views: the comparison window for CURRENT_RANGE
        # (2026-06-12 .. 2026-06-16) is the preceding 4 days
        # [2026-06-08, 2026-06-12); days now-4 and now-5 land inside it.
        db.add_all(
            [
                view(v1, 4, "u3", 4, "US", "mobile"),
                view(v2, 5, "u3", 2, "DE", "desktop"),
            ]
        )
        # Impressions for the funnel (current period).
        for _ in range(20):
            db.add(
                ImpressionEvent(
                    video_id=v1.id,
                    event_time=now - timedelta(days=2, hours=1),
                    country_code="US",
                    device_type="mobile",
                )
            )
        db.commit()
    yield {"now": now}


@pytest.fixture()
def client(seeded):
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Date range covering the current-period test events (now-4 .. now).
CURRENT_RANGE = {"start_date": "2026-06-12", "end_date": "2026-06-16"}
