"""Add persistent administrator authentication state.

Revision ID: 20260825_0012
Revises: 20260824_0011
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260825_0012"
down_revision: Union[str, None] = "20260824_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_auth_state",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("pin_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "session_generation",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_admin_auth_state_singleton"),
        sa.CheckConstraint(
            "length(pin_hash) BETWEEN 64 AND 255",
            name="ck_admin_auth_state_pin_hash_length",
        ),
        sa.CheckConstraint(
            "session_generation > 0",
            name="ck_admin_auth_state_session_generation_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("admin_auth_state")
