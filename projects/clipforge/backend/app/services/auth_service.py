"""Authentication & registration business logic."""

from __future__ import annotations

import re

import jwt
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.auth import TokenPair, UserRegister


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workspace"


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def register(self, data: UserRegister) -> User:
        if self.users.get_by_email(data.email):
            raise ConflictError("An account with this email already exists")

        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self.users.add(user)

        # Bootstrap a default workspace so the user can upload immediately.
        base_slug = _slugify(data.full_name or data.email.split("@")[0])
        slug = base_slug
        suffix = 1
        while self.workspaces.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        workspace = Workspace(
            name=f"{data.full_name.split(' ')[0]}'s Workspace",
            slug=slug,
            owner_id=user.id,
        )
        self.workspaces.add(workspace)
        self.workspaces.db.add(
            WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("Account is disabled")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid or expired refresh token") from exc

        user = self.users.get(payload["sub"])
        if not user or not user.is_active:
            raise AuthError("User no longer active")
        return self.issue_tokens(user)
