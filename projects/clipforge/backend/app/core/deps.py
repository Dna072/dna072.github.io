"""Shared FastAPI dependencies (auth, current user)."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=False
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise AuthError("Not authenticated")
    try:
        payload = decode_token(token, expected_type="access")
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired token") from exc

    user = UserRepository(db).get(payload.get("sub", ""))
    if user is None or not user.is_active:
        raise AuthError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
