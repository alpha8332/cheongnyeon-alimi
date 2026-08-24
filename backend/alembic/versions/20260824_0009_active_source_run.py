"""Enforce one active CollectionRun per source.

Revision ID: 20260824_0009
Revises: 20260824_0008
Create Date: 2026-08-24

"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260824_0009"
down_revision: Union[str, None] = "20260824_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT run_id,
                   row_number() OVER (
                       PARTITION BY source_id
                       ORDER BY started_at DESC, run_id DESC
                   ) AS active_rank
            FROM collection_runs
            WHERE source_id IS NOT NULL
              AND status IN ('queued', 'running')
        )
        UPDATE collection_runs AS runs
        SET status = 'failed',
            finished_at = GREATEST(CURRENT_TIMESTAMP, runs.started_at),
            failed_count = GREATEST(runs.failed_count, 1),
            error_type = 'DuplicateActiveRunMigration'
        FROM ranked
        WHERE runs.run_id = ranked.run_id
          AND ranked.active_rank > 1
        """
    )
    op.create_index(
        "uq_collection_runs_active_source",
        "collection_runs",
        ["source_id"],
        unique=True,
        postgresql_where=(
            "source_id IS NOT NULL AND status IN ('queued', 'running')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_collection_runs_active_source",
        table_name="collection_runs",
    )
