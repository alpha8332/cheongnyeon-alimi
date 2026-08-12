"""Add duplicate and rejected CollectionRun counts.

Revision ID: 20260810_0005
Revises: 20260803_0004
Create Date: 2026-08-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260810_0005"
down_revision: Union[str, None] = "20260803_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_COUNT_COLUMNS = (
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
NEW_COUNT_COLUMNS = (
    *OLD_COUNT_COLUMNS[:6],
    "duplicate_count",
    "rejected_count",
    *OLD_COUNT_COLUMNS[6:],
)


def _counts_nonnegative(columns: tuple[str, ...]) -> str:
    return " AND ".join(f"{column} >= 0" for column in columns)


def upgrade() -> None:
    op.drop_constraint(
        "ck_collection_runs_counts_nonnegative",
        "collection_runs",
        type_="check",
    )
    for column in ("duplicate_count", "rejected_count"):
        op.add_column(
            "collection_runs",
            sa.Column(
                column,
                sa.Integer(),
                server_default="0",
                nullable=False,
            ),
        )
    op.create_check_constraint(
        "ck_collection_runs_counts_nonnegative",
        "collection_runs",
        _counts_nonnegative(NEW_COUNT_COLUMNS),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_collection_runs_counts_nonnegative",
        "collection_runs",
        type_="check",
    )
    for column in ("rejected_count", "duplicate_count"):
        op.drop_column("collection_runs", column)
    op.create_check_constraint(
        "ck_collection_runs_counts_nonnegative",
        "collection_runs",
        _counts_nonnegative(OLD_COUNT_COLUMNS),
    )
