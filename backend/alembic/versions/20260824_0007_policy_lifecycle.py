"""Add policy observation and inactive lifecycle timestamps.

Revision ID: 20260824_0007
Revises: 20260810_0006
Create Date: 2026-08-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260824_0007"
down_revision: Union[str, None] = "20260810_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for column_name in ("last_seen_at", "last_verified_at"):
        op.add_column(
            "policies",
            sa.Column(
                column_name,
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
    op.add_column(
        "policies",
        sa.Column(
            "inactive_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE policies SET "
        "last_seen_at = collected_at, "
        "last_verified_at = updated_at"
    )
    # A prior revision installs deferred constraint triggers on policies.
    # Flush their events before altering the same table.
    op.execute("SET CONSTRAINTS ALL IMMEDIATE")
    for column_name in ("last_seen_at", "last_verified_at"):
        op.alter_column(
            "policies",
            column_name,
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
    op.create_check_constraint(
        "ck_policies_inactive_after_last_seen",
        "policies",
        "inactive_at IS NULL OR inactive_at >= last_seen_at",
    )
    op.create_index(
        "ix_policies_application_end",
        "policies",
        ["application_end"],
        unique=False,
    )
    op.create_index(
        "ix_policies_inactive_at",
        "policies",
        ["inactive_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_policies_inactive_at", table_name="policies")
    op.drop_index("ix_policies_application_end", table_name="policies")
    op.drop_constraint(
        "ck_policies_inactive_after_last_seen",
        "policies",
        type_="check",
    )
    op.drop_column("policies", "inactive_at")
    op.drop_column("policies", "last_verified_at")
    op.drop_column("policies", "last_seen_at")
