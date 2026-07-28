"""Create the policies table.

Revision ID: 20260728_0001
Revises:
Create Date: 2026-07-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260728_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


application_schedule_enum = postgresql.ENUM(
    "fixed_period",
    "always",
    "until_budget_exhausted",
    name="policy_application_schedule",
    create_type=False,
)
application_status_enum = postgresql.ENUM(
    "open",
    "closed",
    "scheduled",
    name="policy_application_status",
    create_type=False,
)
data_quality_status_enum = postgresql.ENUM(
    "valid",
    "partial",
    "invalid",
    name="policy_data_quality_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    application_schedule_enum.create(bind, checkfirst=False)
    application_status_enum.create(bind, checkfirst=False)
    data_quality_status_enum.create(bind, checkfirst=False)

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            server_default="1.0.0",
            nullable=False,
        ),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("organization", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category_text", sa.Text(), nullable=True),
        sa.Column(
            "categories",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("application_period_text", sa.Text(), nullable=True),
        sa.Column("application_start", sa.Date(), nullable=True),
        sa.Column("application_end", sa.Date(), nullable=True),
        sa.Column("application_schedule", application_schedule_enum, nullable=True),
        sa.Column("application_status", application_status_enum, nullable=True),
        sa.Column("region_text", sa.Text(), nullable=True),
        sa.Column(
            "regions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("age_condition_text", sa.Text(), nullable=True),
        sa.Column("eligibility_text", sa.Text(), nullable=True),
        sa.Column("support_content", sa.Text(), nullable=True),
        sa.Column("application_method", sa.Text(), nullable=True),
        sa.Column(
            "education_statuses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "employment_statuses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "required_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "preferred_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "excluded_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("data_quality_status", data_quality_status_enum, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "age_min IS NULL OR (age_min >= 0 AND age_min <= 150)",
            name="ck_policies_age_min_range",
        ),
        sa.CheckConstraint(
            "age_max IS NULL OR (age_max >= 0 AND age_max <= 150)",
            name="ck_policies_age_max_range",
        ),
        sa.CheckConstraint(
            "age_min IS NULL OR age_max IS NULL OR age_min <= age_max",
            name="ck_policies_age_order",
        ),
        sa.CheckConstraint(
            "application_start IS NULL OR application_end IS NULL "
            "OR application_start <= application_end",
            name="ck_policies_application_date_order",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_policies_source_external",
        ),
    )
    op.create_index("ix_policies_source_id", "policies", ["source_id"])
    op.create_index("ix_policies_external_id", "policies", ["external_id"])
    op.create_index(
        "ix_policies_data_quality_status",
        "policies",
        ["data_quality_status"],
    )
    op.create_index(
        "ix_policies_categories_gin",
        "policies",
        ["categories"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_policies_regions_gin",
        "policies",
        ["regions"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_policies_regions_gin", table_name="policies")
    op.drop_index("ix_policies_categories_gin", table_name="policies")
    op.drop_index("ix_policies_data_quality_status", table_name="policies")
    op.drop_index("ix_policies_external_id", table_name="policies")
    op.drop_index("ix_policies_source_id", table_name="policies")
    op.drop_table("policies")

    bind = op.get_bind()
    data_quality_status_enum.drop(bind, checkfirst=False)
    application_status_enum.drop(bind, checkfirst=False)
    application_schedule_enum.drop(bind, checkfirst=False)
