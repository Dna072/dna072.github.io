import secrets
import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.user import User


class SharePermission(StrEnum):
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"


def generate_share_token() -> str:
    return secrets.token_urlsafe(24)


class Share(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shares"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, default=generate_share_token
    )
    permission: Mapped[SharePermission] = mapped_column(
        Enum(SharePermission, name="share_permission"),
        nullable=False,
        default=SharePermission.VIEW,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="shares")
    creator: Mapped["User"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Share {self.token}>"
