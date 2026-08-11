"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import (
    AuthResponse,
    RefreshRequest,
    TokenPair,
    UserLogin,
    UserPublic,
    UserRegister,
)
from app.services.auth_service import AuthService
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.register(payload)
    # Give every new user a default workspace to start uploading immediately.
    WorkspaceService(db).ensure_default_workspace(user)
    tokens = service.issue_tokens(user)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.authenticate(payload.email, payload.password)
    tokens = service.issue_tokens(user)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post("/token", response_model=TokenPair)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> TokenPair:
    """OAuth2 password-flow endpoint (used by Swagger 'Authorize')."""
    service = AuthService(db)
    user = service.authenticate(form_data.username, form_data.password)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    return AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)
