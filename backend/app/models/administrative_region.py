from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


REGION_LEVEL_VALUES = ("country", "province", "district")
REGION_STATUS_VALUES = ("active", "retired")
REGION_ALIAS_KIND_VALUES = (
    "official_full",
    "official_short",
    "curated",
)

JSON_OBJECT = JSON().with_variant(JSONB(), "postgresql")


class AdministrativeRegion(Base):
    __tablename__ = "administrative_regions"

    scheme = Column(String(64), primary_key=True)
    code = Column(String(32), primary_key=True)
    name = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)
    level = Column(
        Enum(
            *REGION_LEVEL_VALUES,
            name="administrative_region_level",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    status = Column(
        Enum(
            *REGION_STATUS_VALUES,
            name="administrative_region_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    parent_code = Column(String(32), nullable=True)
    aggregate_parent_code = Column(String(32), nullable=True)
    source_parent_code = Column(String(32), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    external_codes = Column(
        JSON_OBJECT,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ("scheme", "parent_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_regions_parent",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("scheme", "aggregate_parent_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_regions_aggregate_parent",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(scheme)) > 0 AND length(trim(code)) > 0",
            name="ck_administrative_regions_identity_nonempty",
        ),
        CheckConstraint(
            "length(trim(name)) > 0 AND length(trim(full_name)) > 0",
            name="ck_administrative_regions_names_nonempty",
        ),
        CheckConstraint(
            "parent_code IS NULL OR parent_code <> code",
            name="ck_administrative_regions_parent_not_self",
        ),
        CheckConstraint(
            "aggregate_parent_code IS NULL "
            "OR aggregate_parent_code <> code",
            name="ck_administrative_regions_aggregate_parent_not_self",
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL "
            "OR valid_from <= valid_to",
            name="ck_administrative_regions_validity_order",
        ),
        Index(
            "ix_administrative_regions_parent",
            "scheme",
            "parent_code",
        ),
        Index(
            "ix_administrative_regions_aggregate_parent",
            "scheme",
            "aggregate_parent_code",
        ),
        Index(
            "ix_administrative_regions_status",
            "scheme",
            "status",
        ),
        Index(
            "ix_administrative_regions_external_codes_gin",
            "external_codes",
            postgresql_using="gin",
        ),
    )


class AdministrativeRegionAlias(Base):
    __tablename__ = "administrative_region_aliases"

    scheme = Column(String(64), primary_key=True)
    alias = Column(Text, primary_key=True)
    region_code = Column(String(32), primary_key=True)
    kind = Column(
        Enum(
            *REGION_ALIAS_KIND_VALUES,
            name="administrative_region_alias_kind",
            create_constraint=True,
            validate_strings=True,
        ),
        primary_key=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ("scheme", "region_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_region_aliases_region",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "length(trim(alias)) > 0",
            name="ck_administrative_region_aliases_alias_nonempty",
        ),
        UniqueConstraint(
            "scheme",
            "alias",
            "region_code",
            "kind",
            name="uq_administrative_region_aliases_identity",
        ),
        Index(
            "ix_administrative_region_aliases_lookup",
            "scheme",
            "alias",
        ),
    )
