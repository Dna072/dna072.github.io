"""Current-user profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.security import hash_password
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_profile(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_profile(payload: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserRead:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.password is not None:
        current_user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    return UserRead.model_validate(current_user)
