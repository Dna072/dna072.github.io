import fakeredis
import pytest
from fastapi.testclient import TestClient
from renderflow_common.config import Settings
from renderflow_common.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app


def _test_settings(**overrides) -> Settings:
    defaults = dict(
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        queue_key="test:queue",
        delayed_queue_key="test:delayed",
        heartbeat_timeout_seconds=1,
        scheduler_interval_seconds=999,  # effectively disabled during API tests
    )
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.fixture()
def settings() -> Settings:
    return _test_settings()


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(engine):
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = factory()
    yield session
    session.close()


@pytest.fixture()
def fake_redis():
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture()
def client(settings, monkeypatch):
    """A TestClient backed by an isolated in-memory SQLite DB and a fake
    Redis client (patched in before app creation, since `create_app` wires
    up its own Redis client from `settings.redis_url`)."""
    import fakeredis as _fakeredis

    monkeypatch.setattr(
        "app.main.get_redis",
        lambda url: _fakeredis.FakeStrictRedis(decode_responses=True),
    )
    app = create_app(settings=settings)
    with TestClient(app) as test_client:
        yield test_client
