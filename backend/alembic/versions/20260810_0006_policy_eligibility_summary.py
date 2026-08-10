"""Add source-backed policy eligibility summary.

Revision ID: 20260810_0006
Revises: 20260810_0005
Create Date: 2026-08-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260810_0006"
down_revision: Union[str, None] = "20260810_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EMPTY_ELIGIBILITY_SUMMARY_SQL = (
    "'{\"coverage\":\"unknown\",\"requirements\":[],"
    "\"exclusions\":[],\"preferences\":[],\"documents\":[],"
    "\"unknowns\":[],\"institutional_contacts\":[]}'"
)


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column(
            "eligibility_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(EMPTY_ELIGIBILITY_SUMMARY_SQL),
            nullable=False,
        ),
    )
    op.alter_column(
        "policies",
        "schema_version",
        existing_type=sa.String(length=32),
        server_default="1.2.0",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "policies",
        "schema_version",
        existing_type=sa.String(length=32),
        server_default="1.1.0",
        existing_nullable=False,
    )
    op.drop_column("policies", "eligibility_summary")
