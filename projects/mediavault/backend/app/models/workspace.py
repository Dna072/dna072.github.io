"""Workspace and membership models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Role
from app.models.mixins import GUID, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.folder import Folder
    from app.models.tag import Tag
    from app.models.user import User


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)

    owner: Mapped[User] = relationship(back_populates="owned_workspaces", foreign_keys=[owner_id])
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    folders: Mapped[list[Folder]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    assets: Mapped[list[Asset]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    tags: Mapped[list[Tag]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_membership_workspace_user"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role"), default=Role.MEMBER, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")
