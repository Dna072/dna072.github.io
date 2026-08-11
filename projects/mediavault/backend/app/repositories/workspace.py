"""Workspace and membership repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.workspace import Membership, Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    def get_by_slug(self, slug: str) -> Workspace | None:
        stmt = select(Workspace).where(Workspace.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: uuid.UUID) -> list[tuple[Workspace, Membership]]:
        stmt = (
            select(Workspace, Membership)
            .join(Membership, Membership.workspace_id == Workspace.id)
            .where(Membership.user_id == user_id)
            .order_by(Workspace.name)
        )
        return [tuple(row) for row in self.db.execute(stmt).all()]


class MembershipRepository(BaseRepository[Membership]):
    model = Membership

    def get(self, id_: uuid.UUID) -> Membership | None:
        return self.db.get(Membership, id_)

    def get_for(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Membership | None:
        stmt = select(Membership).where(
            Membership.workspace_id == workspace_id, Membership.user_id == user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_workspace(self, workspace_id: uuid.UUID) -> list[Membership]:
        stmt = (
            select(Membership)
            .where(Membership.workspace_id == workspace_id)
            .order_by(Membership.created_at)
        )
        return list(self.db.execute(stmt).scalars())
