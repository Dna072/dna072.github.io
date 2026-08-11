import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.workspace import Workspace


class Folder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "folders"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Materialized path of ancestor folder ids joined by '/', e.g. "<id1>/<id2>".
    # Empty string for root-level folders. Enables efficient subtree queries.
    path: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    workspace: Mapped["Workspace"] = relationship(back_populates="folders")
    parent: Mapped["Folder | None"] = relationship(
        remote_side="Folder.id", back_populates="children"
    )
    children: Mapped[list["Folder"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="folder")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Folder {self.name}>"
