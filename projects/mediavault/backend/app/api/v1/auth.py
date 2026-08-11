import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.common import Message
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> TokenPair:
    access_token = create_access_token(str(user.id))
    refresh_token, jti, expires_at = create_refresh_token(str(user.id))
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    tokens = _issue_tokens(db, user)
    return AuthResponse(**tokens.model_dump(), user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    tokens = _issue_tokens(db, user)
    return AuthResponse(**tokens.model_dump(), user=UserRead.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    decoded = decode_token(payload.refresh_token)
    if decoded is None or decoded.get("type") != TokenType.REFRESH.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    jti = decoded.get("jti")
    record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if record is None or record.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked"
        )
    if record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired"
        )
    user = db.get(User, uuid.UUID(decoded["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: revoke the presented refresh token and issue a brand new pair.
    record.revoked_at = datetime.now(UTC)
    db.add(record)
    return _issue_tokens(db, user)


@router.post("/logout", response_model=Message)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> Message:
    decoded = decode_token(payload.refresh_token)
    if decoded is not None:
        jti = decoded.get("jti")
        record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            db.add(record)
            db.commit()
    return Message(message="Logged out")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
