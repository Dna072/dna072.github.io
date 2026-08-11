"""Asset model plus the asset<->tag association table."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Text as SAText
from sqlalchemy.types import TypeDecorator

from app.core.database import Base
from app.models.enums import AssetKind, AssetStatus
from app.models.mixins import GUID, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.folder import Folder
    from app.models.tag import Tag
    from app.models.workspace import Workspace


class TSVector(TypeDecorator):
    """Portable full-text search column: TSVECTOR on PostgreSQL, text elsewhere."""

    impl = SAText
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import TSVECTOR

            return dialect.type_descriptor(TSVECTOR())
        return dialect.type_descriptor(SAText())


class AssetTag(Base):
    __tablename__ = "asset_tags"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_workspace_folder", "workspace_id", "folder_id"),
        Index("ix_assets_workspace_created", "workspace_id", "created_at"),
        Index("ix_assets_workspace_kind", "workspace_id", "kind"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("folders.id", ondelete="SET NULL"), index=True, nullable=True
    )

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Storage metadata
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[AssetKind] = mapped_column(
        SAEnum(AssetKind, name="asset_kind"), default=AssetKind.OTHER, nullable=False
    )
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[AssetStatus] = mapped_column(
        SAEnum(AssetStatus, name="asset_status"), default=AssetStatus.READY, nullable=False
    )

    # Media metadata (nullable — populated for images/video)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Full-text search vector (maintained by a DB trigger on PostgreSQL).
    search_vector: Mapped[str | None] = mapped_column(TSVector(), nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="assets")
    folder: Mapped[Folder | None] = relationship(back_populates="assets")
    tags: Mapped[list[Tag]] = relationship(
        secondary="asset_tags", back_populates="assets"
    )
