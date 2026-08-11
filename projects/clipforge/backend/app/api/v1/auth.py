from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import (
    RefreshRequest,
    TokenPair,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: DbSession) -> UserRead:
    user = AuthService(db).register(data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
def login(data: UserLogin, db: DbSession) -> TokenPair:
    service = AuthService(db)
    user = service.authenticate(data.email, data.password)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: DbSession) -> TokenPair:
    return AuthService(db).refresh(data.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
