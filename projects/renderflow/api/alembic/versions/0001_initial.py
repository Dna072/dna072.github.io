"""initial jobs and workers tables

Revision ID: 0001
Revises:
Create Date: 2026-08-11 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import renderflow_common.db_types

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", renderflow_common.db_types.GUID(), nullable=False),
        sa.Column(
            "job_type",
            sa.Enum(
                "transcode", "thumbnail", "audio_extract", "metadata", name="job_type"
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "processing",
                "retrying",
                "completed",
                "failed",
                "cancelled",
                name="job_status",
            ),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("input_uri", sa.String(length=2048), nullable=False),
        sa.Column("output_uri", sa.String(length=2048), nullable=True),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_idempotency_key"), "jobs", ["idempotency_key"], unique=True)
    op.create_index(op.f("ix_jobs_priority"), "jobs", ["priority"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_worker_id"), "jobs", ["worker_id"], unique=False)

    op.create_table(
        "workers",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.Enum("idle", "busy", "offline", name="worker_status"), nullable=False
        ),
        sa.Column("current_job_id", renderflow_common.db_types.GUID(), nullable=True),
        sa.Column("jobs_processed", sa.Integer(), nullable=False),
        sa.Column("jobs_failed", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["current_job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("workers")
    op.drop_index(op.f("ix_jobs_worker_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_priority"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_idempotency_key"), table_name="jobs")
    op.drop_table("jobs")
