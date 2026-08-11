"""Authentication service: registration, login, refresh rotation, logout."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.token import RefreshToken
from app.models.user import User
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.schemas.auth import TokenPair


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    # --- Registration / login ----------------------------------------------
    def register(self, email: str, password: str, full_name: str = "") -> User:
        if self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists.")
        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        self.users.add(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            # Uniform error prevents user enumeration.
            raise AuthenticationError("Incorrect email or password.")
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        return user

    # --- Token lifecycle ----------------------------------------------------
    def issue_tokens(self, user: User) -> TokenPair:
        access = create_access_token(str(user.id), email=user.email)
        refresh = create_refresh_token(str(user.id))
        self._persist_refresh(user, refresh)
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def _persist_refresh(self, user: User, refresh: str) -> None:
        self.tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh),
                expires_at=datetime.now(UTC)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            decode_token(refresh_token, expected_type="refresh")
        except Exception as exc:  # noqa: BLE001 - normalize to auth error
            raise AuthenticationError("Invalid or expired refresh token.") from exc

        stored = self.tokens.get_by_hash(hash_token(refresh_token))
        if not stored or not self.tokens.is_active(stored):
            raise AuthenticationError("Refresh token has been revoked or expired.")

        user = self.users.get(stored.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Account is no longer active.")

        # Rotate: revoke the presented token and issue a fresh pair.
        stored.revoked = True
        self.db.flush()
        return self.issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        stored = self.tokens.get_by_hash(hash_token(refresh_token))
        if stored:
            stored.revoked = True
            self.db.flush()

    def logout_all(self, user: User) -> None:
        self.tokens.revoke_all_for_user(user.id)
