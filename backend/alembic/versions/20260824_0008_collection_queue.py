"""Add queued state for broker-backed collection runs.

Revision ID: 20260824_0008
Revises: 20260824_0007
Create Date: 2026-08-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260824_0008"
down_revision: Union[str, None] = "20260824_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ACTIVE_CHECK = (
    "(status IN ('queued', 'running') AND finished_at IS NULL) OR "
    "(status NOT IN ('queued', 'running') AND finished_at IS NOT NULL)"
)
LEGACY_CHECK = (
    "(status = 'running' AND finished_at IS NULL) OR "
    "(status <> 'running' AND finished_at IS NOT NULL)"
)


def upgrade() -> None:
    # PostgreSQL does not allow a newly-added enum value to be referenced
    # before its transaction commits, so the enum change is isolated.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE collection_run_status "
            "ADD VALUE IF NOT EXISTS 'queued' BEFORE 'running'"
        )

    op.drop_constraint(
        "ck_collection_runs_terminal_finished_at",
        "collection_runs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_collection_runs_terminal_finished_at",
        "collection_runs",
        ACTIVE_CHECK,
    )


def downgrade() -> None:
    # Preserve the invariant when removing queued: queued work is explicitly
    # terminated rather than silently converted into a running execution.
    op.execute(
        sa.text(
            "UPDATE collection_runs "
            "SET status = 'failed', "
            "finished_at = GREATEST(CURRENT_TIMESTAMP, started_at), "
            "failed_count = GREATEST(failed_count, 1), "
            "error_type = 'QueueSchemaDowngrade' "
            "WHERE status = 'queued'"
        )
    )
    op.drop_constraint(
        "ck_collection_runs_terminal_finished_at",
        "collection_runs",
        type_="check",
    )
    op.execute(
        "ALTER TABLE collection_runs ALTER COLUMN status DROP DEFAULT"
    )
    op.execute(
        "CREATE TYPE collection_run_status_legacy AS ENUM "
        "('running', 'succeeded', 'partial_failure', 'failed')"
    )
    op.execute(
        "ALTER TABLE collection_runs ALTER COLUMN status "
        "TYPE collection_run_status_legacy "
        "USING status::text::collection_run_status_legacy"
    )
    op.execute("DROP TYPE collection_run_status")
    op.execute(
        "ALTER TYPE collection_run_status_legacy "
        "RENAME TO collection_run_status"
    )
    op.execute(
        "ALTER TABLE collection_runs ALTER COLUMN status "
        "SET DEFAULT 'running'"
    )
    op.create_check_constraint(
        "ck_collection_runs_terminal_finished_at",
        "collection_runs",
        LEGACY_CHECK,
    )
