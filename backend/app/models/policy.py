from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


APPLICATION_SCHEDULE_VALUES = (
    "fixed_period",
    "always",
    "until_budget_exhausted",
)
APPLICATION_STATUS_VALUES = ("open", "closed", "scheduled")
DATA_QUALITY_STATUS_VALUES = ("valid", "partial", "invalid")
COVERAGE_SCOPE_VALUES = ("nationwide", "regional", "unknown")

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")
EMPTY_ELIGIBILITY_SUMMARY = {
    "coverage": "unknown",
    "requirements": [],
    "exclusions": [],
    "preferences": [],
    "documents": [],
    "unknowns": [],
    "institutional_contacts": [],
}
EMPTY_ELIGIBILITY_SUMMARY_SQL = (
    "'{\"coverage\":\"unknown\",\"requirements\":[],"
    "\"exclusions\":[],\"preferences\":[],\"documents\":[],"
    "\"unknowns\":[],\"institutional_contacts\":[]}'"
)


def empty_eligibility_summary_document() -> dict[str, object]:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in EMPTY_ELIGIBILITY_SUMMARY.items()
    }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Policy(Base):
    """Database representation of the NormalizedProgram 1.2.0 contract."""

    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)

    schema_version = Column(
        String(32),
        nullable=False,
        default="1.2.0",
        server_default="1.2.0",
    )
    source_id = Column(Text, nullable=False)
    source_name = Column(String(255), nullable=False)
    external_id = Column(String(512), nullable=True)

    title = Column(String(1000), nullable=False)
    organization = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    category_text = Column(Text, nullable=True)
    categories = Column(JSON_DOCUMENT, nullable=False, default=list)
    keywords = Column(
        JSON_DOCUMENT,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    life_stages = Column(
        JSON_DOCUMENT,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    target_groups = Column(
        JSON_DOCUMENT,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )

    application_period_text = Column(Text, nullable=True)
    application_start = Column(Date, nullable=True)
    application_end = Column(Date, nullable=True)
    application_schedule = Column(
        Enum(
            *APPLICATION_SCHEDULE_VALUES,
            name="policy_application_schedule",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=True,
    )
    application_status = Column(
        Enum(
            *APPLICATION_STATUS_VALUES,
            name="policy_application_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    region_text = Column(Text, nullable=True)
    regions = Column(JSON_DOCUMENT, nullable=False, default=list)
    coverage_scope = Column(
        Enum(
            *COVERAGE_SCOPE_VALUES,
            name="policy_coverage_scope",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )

    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    age_condition_text = Column(Text, nullable=True)
    eligibility_text = Column(Text, nullable=True)
    eligibility_summary = Column(
        JSON_DOCUMENT,
        nullable=False,
        default=empty_eligibility_summary_document,
        server_default=text(EMPTY_ELIGIBILITY_SUMMARY_SQL),
    )

    support_content = Column(Text, nullable=True)
    application_method = Column(Text, nullable=True)

    education_statuses = Column(JSON_DOCUMENT, nullable=False, default=list)
    employment_statuses = Column(JSON_DOCUMENT, nullable=False, default=list)
    required_conditions = Column(JSON_DOCUMENT, nullable=False, default=list)
    preferred_conditions = Column(JSON_DOCUMENT, nullable=False, default=list)
    excluded_conditions = Column(JSON_DOCUMENT, nullable=False, default=list)

    source_url = Column(Text, nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    provenance = Column(JSON_DOCUMENT, nullable=False, default=list)

    data_quality_status = Column(
        Enum(
            *DATA_QUALITY_STATUS_VALUES,
            name="policy_data_quality_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    last_verified_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    inactive_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_policies_source_external",
        ),
        CheckConstraint(
            "age_min IS NULL OR (age_min >= 0 AND age_min <= 150)",
            name="ck_policies_age_min_range",
        ),
        CheckConstraint(
            "age_max IS NULL OR (age_max >= 0 AND age_max <= 150)",
            name="ck_policies_age_max_range",
        ),
        CheckConstraint(
            "age_min IS NULL OR age_max IS NULL OR age_min <= age_max",
            name="ck_policies_age_order",
        ),
        CheckConstraint(
            "application_start IS NULL OR application_end IS NULL "
            "OR application_start <= application_end",
            name="ck_policies_application_date_order",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_policies_timestamp_order",
        ),
        CheckConstraint(
            "inactive_at IS NULL OR inactive_at >= last_seen_at",
            name="ck_policies_inactive_after_last_seen",
        ),
        Index("ix_policies_source_id", "source_id"),
        Index("ix_policies_external_id", "external_id"),
        Index("ix_policies_data_quality_status", "data_quality_status"),
        Index("ix_policies_application_end", "application_end"),
        Index("ix_policies_inactive_at", "inactive_at"),
        Index(
            "ix_policies_categories_gin",
            "categories",
            postgresql_using="gin",
        ),
        Index(
            "ix_policies_regions_gin",
            "regions",
            postgresql_using="gin",
        ),
        Index(
            "ix_policies_keywords_gin",
            "keywords",
            postgresql_using="gin",
        ),
        Index(
            "ix_policies_life_stages_gin",
            "life_stages",
            postgresql_using="gin",
        ),
        Index(
            "ix_policies_target_groups_gin",
            "target_groups",
            postgresql_using="gin",
        ),
        Index("ix_policies_coverage_scope", "coverage_scope"),
    )
