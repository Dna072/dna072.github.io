"""Authentication service: registration, login, token refresh."""

from __future__ import annotations

import jwt
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenPair, UserRegister


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: UserRegister) -> User:
        email = payload.email.lower()
        if self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists.")
        user = User(
            email=email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        self.users.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.lower())
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(
                user.id, extra_claims={"email": user.email}
            ),
            refresh_token=create_refresh_token(user.id),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired refresh token.") from exc
        user = self.users.get(payload["sub"])
        if not user or not user.is_active:
            raise AuthenticationError("User no longer exists or is disabled.")
        return self.issue_tokens(user)

    def get_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user
