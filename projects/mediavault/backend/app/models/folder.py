"""Folder model supporting a hierarchical tree per workspace."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import GUID, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.workspace import Workspace


class Folder(Base, TimestampMixin):
    __tablename__ = "folders"
    __table_args__ = (
        UniqueConstraint("workspace_id", "parent_id", "name", name="uq_folder_name_per_parent"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("folders.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Materialized path ("/Marketing/2026") for efficient breadcrumb + subtree queries.
    path: Mapped[str] = mapped_column(String(1024), default="/", nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    workspace: Mapped[Workspace] = relationship(back_populates="folders")
    parent: Mapped[Folder | None] = relationship(
        remote_side="Folder.id", back_populates="children"
    )
    children: Mapped[list[Folder]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    assets: Mapped[list[Asset]] = relationship(back_populates="folder")
