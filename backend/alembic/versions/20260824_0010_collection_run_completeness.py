"""Persist full-snapshot evidence on CollectionRun.

Revision ID: 20260824_0010
Revises: 20260824_0009
Create Date: 2026-08-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260824_0010"
down_revision: Union[str, None] = "20260824_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "collection_runs",
        sa.Column(
            "is_complete_snapshot",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("collection_runs", "is_complete_snapshot")
