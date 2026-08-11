"""initial schema: users, videos, impression_events, view_events

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-11

Index strategy is intentional; see README "Database & indexing" for the why.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_videos_category", "videos", ["category"])
    op.create_index("ix_videos_published_at", "videos", ["published_at"])

    op.create_table(
        "impression_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("device_type", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_impressions_video_time", "impression_events", ["video_id", "event_time"]
    )
    op.create_index("ix_impressions_time", "impression_events", ["event_time"])

    op.create_table(
        "view_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("viewer_id", sa.String(length=36), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("device_type", sa.String(length=16), nullable=False),
        sa.Column("watch_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "quartile_reached", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("liked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("commented", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("shared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "quartile_reached BETWEEN 0 AND 4", name="ck_quartile_range"
        ),
    )
    op.create_index("ix_views_time", "view_events", ["event_time"])
    op.create_index("ix_views_video_time", "view_events", ["video_id", "event_time"])
    op.create_index(
        "ix_views_country_time", "view_events", ["country_code", "event_time"]
    )
    op.create_index(
        "ix_views_device_time", "view_events", ["device_type", "event_time"]
    )


def downgrade() -> None:
    op.drop_table("view_events")
    op.drop_table("impression_events")
    op.drop_index("ix_videos_published_at", table_name="videos")
    op.drop_index("ix_videos_category", table_name="videos")
    op.drop_table("videos")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
