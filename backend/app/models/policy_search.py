from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)

from app.core.database import Base
from app.models.policy import utc_now


REGION_RELATION_VALUES = ("include", "exclude")
REGION_RESOLUTION_STATUS_VALUES = (
    "matched",
    "unmapped",
    "ambiguous",
)


class PolicyRegionRule(Base):
    __tablename__ = "policy_region_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(
        Integer,
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation = Column(
        Enum(
            *REGION_RELATION_VALUES,
            name="policy_region_relation",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    resolution_status = Column(
        Enum(
            *REGION_RESOLUTION_STATUS_VALUES,
            name="policy_region_resolution_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    region_scheme = Column(String(64), nullable=True)
    region_code = Column(String(32), nullable=True)
    source_code = Column(Text, nullable=True)
    source_text = Column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ("region_scheme", "region_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_policy_region_rules_region",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "((resolution_status = 'matched' "
            "AND region_scheme IS NOT NULL AND region_code IS NOT NULL) "
            "OR (resolution_status <> 'matched' "
            "AND region_scheme IS NULL AND region_code IS NULL "
            "AND (source_code IS NOT NULL OR source_text IS NOT NULL)))",
            name="ck_policy_region_rules_resolution_identity",
        ),
        CheckConstraint(
            "source_code IS NULL OR length(trim(source_code)) > 0",
            name="ck_policy_region_rules_source_code_nonempty",
        ),
        CheckConstraint(
            "source_text IS NULL OR length(trim(source_text)) > 0",
            name="ck_policy_region_rules_source_text_nonempty",
        ),
        UniqueConstraint(
            "policy_id",
            "region_scheme",
            "region_code",
            name="uq_policy_region_rules_canonical_region",
        ),
        Index("ix_policy_region_rules_policy_id", "policy_id"),
        Index(
            "ix_policy_region_rules_region",
            "region_scheme",
            "region_code",
        ),
    )


class PolicySearchDocument(Base):
    __tablename__ = "policy_search_documents"

    policy_id = Column(
        Integer,
        ForeignKey("policies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    title_text = Column(Text, nullable=False, server_default="")
    keyword_text = Column(Text, nullable=False, server_default="")
    summary_text = Column(Text, nullable=False, server_default="")
    eligibility_text = Column(Text, nullable=False, server_default="")
    support_text = Column(Text, nullable=False, server_default="")
    search_text = Column(Text, nullable=False, server_default="")
    projection_version = Column(String(32), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(projection_version)) > 0",
            name="ck_policy_search_documents_version_nonempty",
        ),
        Index(
            "ix_policy_search_documents_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )
