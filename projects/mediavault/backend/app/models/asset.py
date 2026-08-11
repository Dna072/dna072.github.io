import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Computed, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.folder import Folder
    from app.models.share import Share
    from app.models.tag import Tag
    from app.models.user import User
    from app.models.workspace import Workspace

# The generated tsvector column is computed server-side on PostgreSQL and gives
# us native full-text search (ranked, stemmed, stop-word aware) without an
# external search engine. See migration 0002 for the accompanying GIN index.
_SEARCH_VECTOR_EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(filename, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(original_filename, '')), 'B') || "
    "setweight(to_tsvector('english', coalesce(description, '')), 'C')"
)


class AssetStatus(StrEnum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status"), nullable=False, default=AssetStatus.UPLOADING
    )
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed(_SEARCH_VECTOR_EXPRESSION, persisted=True), nullable=True
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="assets")
    folder: Mapped["Folder | None"] = relationship(back_populates="assets")
    owner: Mapped["User | None"] = relationship()
    tags: Mapped[list["Tag"]] = relationship(secondary="asset_tags", back_populates="assets")
    shares: Mapped[list["Share"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Asset {self.filename}>"
