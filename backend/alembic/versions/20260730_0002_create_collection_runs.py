"""Create the collection_runs table.

Revision ID: 20260730_0002
Revises: 20260728_0001
Create Date: 2026-07-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260730_0002"
down_revision: Union[str, None] = "20260728_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


run_type_enum = postgresql.ENUM(
    "seed_import",
    "runtime_import",
    "collection",
    name="collection_run_type",
    create_type=False,
)
trigger_type_enum = postgresql.ENUM(
    "cli",
    "scheduler",
    "admin",
    name="collection_run_trigger_type",
    create_type=False,
)
status_enum = postgresql.ENUM(
    "running",
    "succeeded",
    "partial_failure",
    "failed",
    name="collection_run_status",
    create_type=False,
)


COUNT_COLUMNS = (
    "requested_count",
    "raw_document_count",
    "extracted_count",
    "accepted_count",
    "partial_count",
    "invalid_count",
    "inserted_count",
    "updated_count",
    "unchanged_count",
    "skipped_count",
    "failed_count",
)


def upgrade() -> None:
    bind = op.get_bind()
    run_type_enum.create(bind, checkfirst=False)
    trigger_type_enum.create(bind, checkfirst=False)
    status_enum.create(bind, checkfirst=False)

    op.create_table(
        "collection_runs",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("source_id", sa.Text(), nullable=True),
        sa.Column("run_type", run_type_enum, nullable=False),
        sa.Column("trigger_type", trigger_type_enum, nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            status_enum,
            server_default="running",
            nullable=False,
        ),
        *(
            sa.Column(
                column,
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
            for column in COUNT_COLUMNS
        ),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "source_id IS NULL OR length(trim(source_id)) > 0",
            name="ck_collection_runs_source_id_nonempty",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_collection_runs_timestamp_order",
        ),
        sa.CheckConstraint(
            "(status = 'running' AND finished_at IS NULL) OR "
            "(status <> 'running' AND finished_at IS NOT NULL)",
            name="ck_collection_runs_terminal_finished_at",
        ),
        sa.CheckConstraint(
            " AND ".join(f"{field} >= 0" for field in COUNT_COLUMNS),
            name="ck_collection_runs_counts_nonnegative",
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "ix_collection_runs_source_id",
        "collection_runs",
        ["source_id"],
    )
    op.create_index(
        "ix_collection_runs_started_at",
        "collection_runs",
        ["started_at"],
    )
    op.create_index(
        "ix_collection_runs_status",
        "collection_runs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collection_runs_status",
        table_name="collection_runs",
    )
    op.drop_index(
        "ix_collection_runs_started_at",
        table_name="collection_runs",
    )
    op.drop_index(
        "ix_collection_runs_source_id",
        table_name="collection_runs",
    )
    op.drop_table("collection_runs")

    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=False)
    trigger_type_enum.drop(bind, checkfirst=False)
    run_type_enum.drop(bind, checkfirst=False)
