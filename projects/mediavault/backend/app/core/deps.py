"""FastAPI dependencies: auth, current user, workspace membership/RBAC guards."""

import uuid

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.membership import WorkspaceMembership, WorkspaceRole
from app.models.user import User
from app.services.rbac import role_at_least

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != TokenType.ACCESS.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    user = db.get(User, uuid.UUID(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user


class WorkspaceContext:
    """Resolved workspace membership for the current request."""

    def __init__(self, workspace_id: uuid.UUID, user: User, membership: WorkspaceMembership):
        self.workspace_id = workspace_id
        self.user = user
        self.membership = membership
        self.role = membership.role


def get_workspace_context(
    workspace_id: uuid.UUID = Path(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceContext:
    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user.id,
        )
        .first()
    )
    if membership is None:
        if user.is_superuser:
            # Superusers can administer any workspace without an explicit membership row.
            fake = WorkspaceMembership(
                workspace_id=workspace_id, user_id=user.id, role=WorkspaceRole.ADMIN
            )
            return WorkspaceContext(workspace_id, user, fake)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return WorkspaceContext(workspace_id, user, membership)


def require_role(minimum: WorkspaceRole):
    def _dependency(ctx: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if not role_at_least(ctx.role, minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least {minimum.value} role in this workspace",
            )
        return ctx

    return _dependency


require_viewer = require_role(WorkspaceRole.VIEWER)
require_member = require_role(WorkspaceRole.MEMBER)
require_admin = require_role(WorkspaceRole.ADMIN)
