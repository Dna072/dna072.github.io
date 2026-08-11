"""Shared pytest fixtures.

Tests run against a real PostgreSQL database (TEST_DATABASE_URL, defaulting
to a local `streampulse_test` database) so that Postgres-specific SQL used
by the aggregation layer (date(), enum columns, etc.) is exercised exactly
as it runs in production.

Each test runs inside a transaction that is rolled back afterwards, so
tests never leak state into one another.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse_test",
    ),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import DeviceType, EngagementEvent, EngagementType, User, Video, ViewEvent  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session: Session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session):
    user = User(
        email="tester@streampulse.io",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client, test_user):
    response = client.post(
        "/api/auth/login", json={"email": "tester@streampulse.io", "password": "testpassword123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded_videos(db_session):
    """Two videos with fully deterministic view/engagement events so that
    aggregation results can be asserted exactly, not just "greater than 0"."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    today = now.date()

    video_a = Video(
        title="Deterministic Video A",
        description="Fixture video",
        category="Tutorials",
        duration_seconds=100,
        thumbnail_url="https://example.com/a.png",
        published_at=now - timedelta(days=10),
    )
    video_b = Video(
        title="Deterministic Video B",
        description="Fixture video",
        category="Webinars",
        duration_seconds=200,
        thumbnail_url="https://example.com/b.png",
        published_at=now - timedelta(days=5),
    )
    db_session.add_all([video_a, video_b])
    db_session.commit()
    db_session.refresh(video_a)
    db_session.refresh(video_b)

    def _dt(day_offset: int, hour: int = 12) -> datetime:
        d = today - timedelta(days=day_offset)
        return datetime(d.year, d.month, d.day, hour, tzinfo=timezone.utc)

    # Video A: 3 views today, all fully specified.
    view_specs = [
        # (video, day_offset, watch_percent, completed, device, country, referrer)
        (video_a, 0, 100.0, True, DeviceType.desktop, "US", "search"),
        (video_a, 0, 50.0, False, DeviceType.mobile, "US", "social"),
        (video_a, 0, 25.0, False, DeviceType.mobile, "GB", "direct"),
        (video_a, 1, 75.0, False, DeviceType.tablet, "GB", "search"),
        (video_b, 0, 100.0, True, DeviceType.tv, "DE", "embed"),
    ]

    for idx, (video, day_offset, watch_percent, completed, device, country, referrer) in enumerate(view_specs):
        occurred_at = _dt(day_offset)
        watch_seconds = int(video.duration_seconds * watch_percent / 100)
        viewer_id = f"fixture-viewer-{idx}"
        db_session.add(
            ViewEvent(
                video_id=video.id,
                viewer_id=viewer_id,
                occurred_at=occurred_at,
                watch_seconds=watch_seconds,
                watch_percent=watch_percent,
                completed=completed,
                device_type=device,
                country_code=country,
                referrer_source=referrer,
            )
        )

        stages = [EngagementType.play]
        if watch_percent >= 25:
            stages.append(EngagementType.reach_25)
        if watch_percent >= 50:
            stages.append(EngagementType.reach_50)
        if watch_percent >= 75:
            stages.append(EngagementType.reach_75)
        if completed:
            stages.append(EngagementType.complete)
            stages.append(EngagementType.like)

        for stage in stages:
            db_session.add(
                EngagementEvent(
                    video_id=video.id,
                    viewer_id=viewer_id,
                    occurred_at=occurred_at,
                    event_type=stage,
                )
            )

    db_session.commit()
    return {"video_a": video_a, "video_b": video_b, "today": today}
