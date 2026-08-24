from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)

from app.core.database import Base


PUBLIC_DATASET_INSTALLATION_STATUS_VALUES = ("installed", "active")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PublicDatasetInstallation(Base):
    """Verified public dataset release installed in this database."""

    __tablename__ = "public_dataset_installations"

    dataset_version = Column(String(128), primary_key=True)
    manifest_sha256 = Column(String(64), nullable=False)
    artifact_sha256 = Column(String(64), nullable=False)
    expected_policy_count = Column(Integer, nullable=False)
    status = Column(
        Enum(
            *PUBLIC_DATASET_INSTALLATION_STATUS_VALUES,
            name="public_dataset_installation_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default="installed",
        server_default="installed",
    )
    installed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    activated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "expected_policy_count > 0",
            name="ck_public_dataset_installations_expected_count_positive",
        ),
        CheckConstraint(
            "length(manifest_sha256) = 64",
            name="ck_public_dataset_installations_manifest_sha256_length",
        ),
        CheckConstraint(
            "length(artifact_sha256) = 64",
            name="ck_public_dataset_installations_artifact_sha256_length",
        ),
        CheckConstraint(
            "(status = 'active' AND activated_at IS NOT NULL) OR "
            "(status = 'installed' AND activated_at IS NULL)",
            name="ck_public_dataset_installations_activation_state",
        ),
        Index(
            "uq_public_dataset_installations_one_active",
            "status",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )


class PublicDatasetMembership(Base):
    """Exact policy identity projected by a verified dataset release."""

    __tablename__ = "public_dataset_memberships"

    dataset_version = Column(
        String(128),
        ForeignKey(
            "public_dataset_installations.dataset_version",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    source_id = Column(Text, primary_key=True)
    external_id = Column(String(512), primary_key=True)
    policy_id = Column(
        Integer,
        ForeignKey("policies.id", ondelete="RESTRICT"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_version",
            "policy_id",
            name="uq_public_dataset_memberships_version_policy",
        ),
        CheckConstraint(
            "length(trim(source_id)) > 0",
            name="ck_public_dataset_memberships_source_nonempty",
        ),
        CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_public_dataset_memberships_external_nonempty",
        ),
        Index("ix_public_dataset_memberships_policy_id", "policy_id"),
    )
