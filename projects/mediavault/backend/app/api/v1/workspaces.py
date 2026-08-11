import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import (
    WorkspaceContext,
    get_current_user,
    require_admin,
    require_viewer,
)
from app.db.session import get_db
from app.models.asset import Asset
from app.models.membership import WorkspaceMembership, WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.common import Message
from app.schemas.workspace import (
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _to_workspace_read(db: Session, workspace: Workspace, user_id: uuid.UUID) -> WorkspaceRead:
    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == user_id,
        )
        .first()
    )
    member_count = (
        db.query(func.count(WorkspaceMembership.id))
        .filter(WorkspaceMembership.workspace_id == workspace.id)
        .scalar()
    )
    asset_count = (
        db.query(func.count(Asset.id)).filter(Asset.workspace_id == workspace.id).scalar()
    )
    data = WorkspaceRead.model_validate(workspace)
    data.my_role = membership.role if membership else None
    data.member_count = member_count or 0
    data.asset_count = asset_count or 0
    return data


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceRead:
    existing = db.query(Workspace).filter(Workspace.slug == payload.slug).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")
    workspace = Workspace(name=payload.name, slug=payload.slug, owner_id=current_user.id)
    db.add(workspace)
    db.flush()
    membership = WorkspaceMembership(
        workspace_id=workspace.id, user_id=current_user.id, role=WorkspaceRole.ADMIN
    )
    db.add(membership)
    db.commit()
    db.refresh(workspace)
    return _to_workspace_read(db, workspace, current_user.id)


@router.get("", response_model=list[WorkspaceRead])
def list_my_workspaces(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WorkspaceRead]:
    workspaces = (
        db.query(Workspace)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .filter(WorkspaceMembership.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )
    return [_to_workspace_read(db, w, current_user.id) for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(
    ctx: WorkspaceContext = Depends(require_viewer), db: Session = Depends(get_db)
) -> WorkspaceRead:
    workspace = db.get(Workspace, ctx.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return _to_workspace_read(db, workspace, ctx.user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(
    payload: WorkspaceUpdate,
    ctx: WorkspaceContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkspaceRead:
    workspace = db.get(Workspace, ctx.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if payload.name is not None:
        workspace.name = payload.name
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return _to_workspace_read(db, workspace, ctx.user.id)


@router.delete("/{workspace_id}", response_model=Message)
def delete_workspace(
    ctx: WorkspaceContext = Depends(require_admin), db: Session = Depends(get_db)
) -> Message:
    workspace = db.get(Workspace, ctx.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.owner_id != ctx.user.id and not ctx.user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete a workspace"
        )
    db.delete(workspace)
    db.commit()
    return Message(message="Workspace deleted")


@router.get("/{workspace_id}/members", response_model=list[MembershipRead])
def list_members(
    ctx: WorkspaceContext = Depends(require_viewer), db: Session = Depends(get_db)
) -> list[MembershipRead]:
    rows = (
        db.query(WorkspaceMembership, User)
        .join(User, User.id == WorkspaceMembership.user_id)
        .filter(WorkspaceMembership.workspace_id == ctx.workspace_id)
        .order_by(WorkspaceMembership.created_at.asc())
        .all()
    )
    return [
        MembershipRead(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            role=m.role,
            created_at=m.created_at,
            user_email=u.email,
            user_full_name=u.full_name,
        )
        for m, u in rows
    ]


@router.post("/{workspace_id}/members", response_model=MembershipRead, status_code=201)
def invite_member(
    payload: MembershipCreate,
    ctx: WorkspaceContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MembershipRead:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that email. They must register first.",
        )
    existing = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == ctx.workspace_id,
            WorkspaceMembership.user_id == user.id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
        )
    membership = WorkspaceMembership(
        workspace_id=ctx.workspace_id, user_id=user.id, role=payload.role
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return MembershipRead(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        created_at=membership.created_at,
        user_email=user.email,
        user_full_name=user.full_name,
    )


@router.patch("/{workspace_id}/members/{membership_id}", response_model=MembershipRead)
def update_member_role(
    membership_id: uuid.UUID,
    payload: MembershipUpdate,
    ctx: WorkspaceContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MembershipRead:
    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.id == membership_id,
            WorkspaceMembership.workspace_id == ctx.workspace_id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    workspace = db.get(Workspace, ctx.workspace_id)
    is_owner = workspace and workspace.owner_id == membership.user_id
    if is_owner and payload.role != WorkspaceRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote the workspace owner",
        )
    membership.role = payload.role
    db.add(membership)
    db.commit()
    db.refresh(membership)
    user = db.get(User, membership.user_id)
    return MembershipRead(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        created_at=membership.created_at,
        user_email=user.email,
        user_full_name=user.full_name,
    )


@router.delete("/{workspace_id}/members/{membership_id}", response_model=Message)
def remove_member(
    membership_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Message:
    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.id == membership_id,
            WorkspaceMembership.workspace_id == ctx.workspace_id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    workspace = db.get(Workspace, ctx.workspace_id)
    if workspace and workspace.owner_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the workspace owner"
        )
    db.delete(membership)
    db.commit()
    return Message(message="Member removed")
