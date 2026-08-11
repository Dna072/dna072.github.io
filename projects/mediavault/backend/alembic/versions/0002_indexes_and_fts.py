"""Add lookup/filter indexes and a GIN index for full-text search.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-11 07:46:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # GIN index over the generated tsvector column — backs /search.
    op.execute(
        "CREATE INDEX ix_assets_search_vector ON assets USING gin (search_vector)"
    )

    # Composite indexes matching the API's actual filter/sort query shapes:
    # "list assets in workspace X, optionally in folder Y, sorted by created_at".
    op.create_index("ix_assets_workspace_created_at", "assets", ["workspace_id", "created_at"])
    op.create_index("ix_assets_workspace_folder", "assets", ["workspace_id", "folder_id"])
    op.create_index("ix_assets_workspace_status", "assets", ["workspace_id", "status"])
    op.create_index("ix_assets_owner_id", "assets", ["owner_id"])

    op.create_index("ix_folders_workspace_parent", "folders", ["workspace_id", "parent_id"])
    op.create_index("ix_tags_workspace_id", "tags", ["workspace_id"])
    op.create_index(
        "ix_memberships_user_id", "workspace_memberships", ["user_id"]
    )
    op.create_index("ix_shares_asset_id", "shares", ["asset_id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_shares_asset_id", table_name="shares")
    op.drop_index("ix_memberships_user_id", table_name="workspace_memberships")
    op.drop_index("ix_tags_workspace_id", table_name="tags")
    op.drop_index("ix_folders_workspace_parent", table_name="folders")
    op.drop_index("ix_assets_owner_id", table_name="assets")
    op.drop_index("ix_assets_workspace_status", table_name="assets")
    op.drop_index("ix_assets_workspace_folder", table_name="assets")
    op.drop_index("ix_assets_workspace_created_at", table_name="assets")
    op.drop_index("ix_assets_search_vector", table_name="assets")
