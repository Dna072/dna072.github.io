"""FastAPI dependencies: auth, current user, workspace context, pagination."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Path, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import PaginationParams
from app.services.rbac import WorkspaceContext
from app.services.workspace import WorkspaceService

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Not authenticated.")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired access token.") from exc

    user_id = payload.get("sub")
    user = UserRepository(db).get(uuid.UUID(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_workspace_context(
    db: DbSession,
    current_user: CurrentUser,
    workspace_id: Annotated[uuid.UUID, Path(description="Workspace id")],
) -> WorkspaceContext:
    service = WorkspaceService(db)
    membership = service.get_membership(workspace_id, current_user)
    workspace = service.workspaces.get(workspace_id)
    if workspace is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Workspace not found.")
    return WorkspaceContext(user=current_user, workspace=workspace, membership=membership)


WorkspaceCtx = Annotated[WorkspaceContext, Depends(get_workspace_context)]


def pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(pagination)]
