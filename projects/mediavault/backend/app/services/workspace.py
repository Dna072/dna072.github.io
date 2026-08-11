"""Workspace and membership management."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.models.enums import Role
from app.models.user import User
from app.models.workspace import Membership, Workspace
from app.repositories.user import UserRepository
from app.repositories.workspace import MembershipRepository, WorkspaceRepository
from app.utils.text import unique_slug


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.memberships = MembershipRepository(db)
        self.users = UserRepository(db)

    def create(self, owner: User, name: str, slug: str | None, description: str) -> Workspace:
        resolved_slug = slug or unique_slug(name, lambda s: self.workspaces.get_by_slug(s) is not None)
        if self.workspaces.get_by_slug(resolved_slug):
            raise ConflictError(f"Workspace slug '{resolved_slug}' is already taken.")
        workspace = Workspace(
            name=name, slug=resolved_slug, description=description, owner_id=owner.id
        )
        self.workspaces.add(workspace)
        # Owner automatically becomes an ADMIN member.
        self.memberships.add(
            Membership(workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN)
        )
        return workspace

    def list_for_user(self, user: User) -> list[tuple[Workspace, Membership]]:
        return self.workspaces.list_for_user(user.id)

    def get_membership(self, workspace_id: uuid.UUID, user: User) -> Membership:
        membership = self.memberships.get_for(workspace_id, user.id)
        if membership is None:
            if user.is_superuser:
                workspace = self.workspaces.get(workspace_id)
                if workspace is None:
                    raise NotFoundError("Workspace not found.")
                # Superuser gets a synthetic admin membership (not persisted).
                return Membership(workspace_id=workspace_id, user_id=user.id, role=Role.ADMIN)
            raise NotFoundError("Workspace not found.")
        return membership

    def update(self, workspace: Workspace, name: str | None, description: str | None) -> Workspace:
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        self.db.flush()
        return workspace

    def delete(self, workspace: Workspace) -> None:
        self.workspaces.delete(workspace)

    # --- Membership ---------------------------------------------------------
    def list_members(self, workspace_id: uuid.UUID) -> list[Membership]:
        return self.memberships.list_for_workspace(workspace_id)

    def add_member(self, workspace: Workspace, email: str, role: Role) -> Membership:
        user = self.users.get_by_email(email)
        if user is None:
            raise NotFoundError(f"No user with email '{email}'. Ask them to register first.")
        if self.memberships.get_for(workspace.id, user.id):
            raise ConflictError("User is already a member of this workspace.")
        membership = Membership(workspace_id=workspace.id, user_id=user.id, role=role)
        return self.memberships.add(membership)

    def update_member_role(
        self, workspace: Workspace, membership_id: uuid.UUID, role: Role
    ) -> Membership:
        membership = self.memberships.get(membership_id)
        if not membership or membership.workspace_id != workspace.id:
            raise NotFoundError("Membership not found.")
        if membership.user_id == workspace.owner_id and role != Role.ADMIN:
            raise PermissionDeniedError("The workspace owner must remain an ADMIN.")
        membership.role = role
        self.db.flush()
        return membership

    def remove_member(self, workspace: Workspace, membership_id: uuid.UUID) -> None:
        membership = self.memberships.get(membership_id)
        if not membership or membership.workspace_id != workspace.id:
            raise NotFoundError("Membership not found.")
        if membership.user_id == workspace.owner_id:
            raise PermissionDeniedError("The workspace owner cannot be removed.")
        self.memberships.delete(membership)
