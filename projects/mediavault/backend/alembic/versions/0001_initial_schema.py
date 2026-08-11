"""Initial MediaVault schema with full-text search support.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-11
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.asset import TSVector
from app.models.mixins import GUID

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = sa.Enum("ADMIN", "MEMBER", "VIEWER", name="role")
ASSET_KIND = sa.Enum("VIDEO", "IMAGE", "DOCUMENT", "OTHER", name="asset_kind")
ASSET_STATUS = sa.Enum("UPLOADING", "PROCESSING", "READY", "FAILED", name="asset_status")

# Maintains assets.search_vector on write (PostgreSQL only).
FTS_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION assets_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.original_filename, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;
"""


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "users",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("owner_id", GUID(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    op.create_table(
        "memberships",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", ROLE, nullable=False, server_default="MEMBER"),
        *_timestamps(),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_membership_workspace_user"),
    )
    op.create_index("ix_memberships_workspace_id", "memberships", ["workspace_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])

    op.create_table(
        "folders",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", GUID(), sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("path", sa.String(1024), nullable=False, server_default="/"),
        sa.Column("created_by", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("workspace_id", "parent_id", "name", name="uq_folder_name_per_parent"),
    )
    op.create_index("ix_folders_workspace_id", "folders", ["workspace_id"])
    op.create_index("ix_folders_parent_id", "folders", ["parent_id"])
    op.create_index("ix_folders_path", "folders", ["path"])

    op.create_table(
        "tags",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(16), nullable=False, server_default="#0f766e"),
        *_timestamps(),
        sa.UniqueConstraint("workspace_id", "name", name="uq_tag_name_per_workspace"),
    )
    op.create_index("ix_tags_workspace_id", "tags", ["workspace_id"])
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "assets",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("workspace_id", GUID(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("folder_id", GUID(), sa.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("kind", ASSET_KIND, nullable=False, server_default="OTHER"),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("status", ASSET_STATUS, nullable=False, server_default="READY"),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("uploaded_by", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("search_vector", TSVector(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_assets_workspace_id", "assets", ["workspace_id"])
    op.create_index("ix_assets_folder_id", "assets", ["folder_id"])
    op.create_index("ix_assets_workspace_folder", "assets", ["workspace_id", "folder_id"])
    op.create_index("ix_assets_workspace_created", "assets", ["workspace_id", "created_at"])
    op.create_index("ix_assets_workspace_kind", "assets", ["workspace_id", "kind"])

    op.create_table(
        "asset_tags",
        sa.Column("asset_id", GUID(), sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", GUID(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "shares",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("asset_id", GUID(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("created_by", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_downloads", sa.Integer(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("allow_download", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    op.create_index("ix_shares_asset_id", "shares", ["asset_id"])
    op.create_index("ix_shares_token", "shares", ["token"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    # PostgreSQL-only: GIN index + trigger to maintain the full-text vector.
    if is_pg:
        op.execute(FTS_TRIGGER_FN)
        op.execute(
            "CREATE TRIGGER assets_search_vector_trigger BEFORE INSERT OR UPDATE "
            "ON assets FOR EACH ROW EXECUTE FUNCTION assets_search_vector_update();"
        )
        op.create_index(
            "ix_assets_search_vector",
            "assets",
            ["search_vector"],
            postgresql_using="gin",
        )
        # Trigram index accelerates ILIKE fallback / prefix search on names.
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        op.execute("CREATE INDEX ix_assets_name_trgm ON assets USING gin (name gin_trgm_ops);")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_assets_name_trgm;")
        op.drop_index("ix_assets_search_vector", table_name="assets")
        op.execute("DROP TRIGGER IF EXISTS assets_search_vector_trigger ON assets;")
        op.execute("DROP FUNCTION IF EXISTS assets_search_vector_update();")

    op.drop_table("refresh_tokens")
    op.drop_table("shares")
    op.drop_table("asset_tags")
    op.drop_table("assets")
    op.drop_table("tags")
    op.drop_table("folders")
    op.drop_table("memberships")
    op.drop_table("workspaces")
    op.drop_table("users")

    for enum in (ROLE, ASSET_KIND, ASSET_STATUS):
        enum.drop(bind, checkfirst=True)
