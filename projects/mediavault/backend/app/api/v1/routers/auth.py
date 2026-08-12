"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.common import Message
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.register(payload.email, payload.password, payload.full_name)
    tokens = service.issue_tokens(user)
    db.commit()
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.authenticate(payload.email, payload.password)
    tokens = service.issue_tokens(user)
    db.commit()
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    service = AuthService(db)
    tokens = service.refresh(payload.refresh_token)
    db.commit()
    return tokens


@router.post("/logout", response_model=Message)
def logout(payload: RefreshRequest, db: DbSession) -> Message:
    service = AuthService(db)
    service.logout(payload.refresh_token)
    db.commit()
    return Message(detail="Logged out.")


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
