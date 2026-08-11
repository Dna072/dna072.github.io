from collections.abc import Generator

import redis
from fastapi import Request
from renderflow_common.config import Settings
from sqlalchemy.orm import Session


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def get_redis_client(request: Request) -> redis.Redis:
    return request.app.state.redis_client


__all__ = ["get_db", "get_redis_client", "get_settings"]
