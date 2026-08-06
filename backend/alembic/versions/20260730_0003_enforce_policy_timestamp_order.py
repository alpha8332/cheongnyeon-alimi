"""Enforce Policy timestamp order.

Revision ID: 20260730_0003
Revises: 20260730_0002
Create Date: 2026-07-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260730_0003"
down_revision: Union[str, None] = "20260730_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE policies "
            "SET updated_at = created_at "
            "WHERE updated_at < created_at"
        )
    )
    op.create_check_constraint(
        "ck_policies_timestamp_order",
        "policies",
        "updated_at >= created_at",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_policies_timestamp_order",
        "policies",
        type_="check",
    )
