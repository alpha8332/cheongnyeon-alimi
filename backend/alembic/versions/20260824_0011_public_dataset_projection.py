"""Add the canonical active public dataset projection.

Revision ID: 20260824_0011
Revises: 20260824_0010
Create Date: 2026-08-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260824_0011"
down_revision: Union[str, None] = "20260824_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


installation_status = postgresql.ENUM(
    "installed",
    "active",
    name="public_dataset_installation_status",
    create_type=False,
)


def upgrade() -> None:
    installation_status.create(op.get_bind(), checkfirst=False)
    op.create_table(
        "public_dataset_installations",
        sa.Column("dataset_version", sa.String(length=128), nullable=False),
        sa.Column("manifest_sha256", sa.String(length=64), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("expected_policy_count", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            installation_status,
            server_default="installed",
            nullable=False,
        ),
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expected_policy_count > 0",
            name="ck_public_dataset_installations_expected_count_positive",
        ),
        sa.CheckConstraint(
            "length(manifest_sha256) = 64",
            name="ck_public_dataset_installations_manifest_sha256_length",
        ),
        sa.CheckConstraint(
            "length(artifact_sha256) = 64",
            name="ck_public_dataset_installations_artifact_sha256_length",
        ),
        sa.CheckConstraint(
            "(status = 'active' AND activated_at IS NOT NULL) OR "
            "(status = 'installed' AND activated_at IS NULL)",
            name="ck_public_dataset_installations_activation_state",
        ),
        sa.PrimaryKeyConstraint("dataset_version"),
    )
    op.create_index(
        "uq_public_dataset_installations_one_active",
        "public_dataset_installations",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "public_dataset_memberships",
        sa.Column("dataset_version", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "length(trim(source_id)) > 0",
            name="ck_public_dataset_memberships_source_nonempty",
        ),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_public_dataset_memberships_external_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version"],
            ["public_dataset_installations.dataset_version"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("dataset_version", "source_id", "external_id"),
        sa.UniqueConstraint(
            "dataset_version",
            "policy_id",
            name="uq_public_dataset_memberships_version_policy",
        ),
    )
    op.create_index(
        "ix_public_dataset_memberships_policy_id",
        "public_dataset_memberships",
        ["policy_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_public_dataset_memberships_policy_id",
        table_name="public_dataset_memberships",
    )
    op.drop_table("public_dataset_memberships")
    op.drop_index(
        "uq_public_dataset_installations_one_active",
        table_name="public_dataset_installations",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_table("public_dataset_installations")
    installation_status.drop(op.get_bind(), checkfirst=False)
