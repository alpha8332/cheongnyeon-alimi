"""Add policy search and administrative-region storage.

Revision ID: 20260803_0004
Revises: 20260730_0003
Create Date: 2026-08-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260803_0004"
down_revision: Union[str, None] = "20260730_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


coverage_scope_enum = postgresql.ENUM(
    "nationwide",
    "regional",
    "unknown",
    name="policy_coverage_scope",
    create_type=False,
)
region_level_enum = postgresql.ENUM(
    "country",
    "province",
    "district",
    name="administrative_region_level",
    create_type=False,
)
region_status_enum = postgresql.ENUM(
    "active",
    "retired",
    name="administrative_region_status",
    create_type=False,
)
region_alias_kind_enum = postgresql.ENUM(
    "official_full",
    "official_short",
    "curated",
    name="administrative_region_alias_kind",
    create_type=False,
)
region_relation_enum = postgresql.ENUM(
    "include",
    "exclude",
    name="policy_region_relation",
    create_type=False,
)
region_resolution_status_enum = postgresql.ENUM(
    "matched",
    "unmapped",
    "ambiguous",
    name="policy_region_resolution_status",
    create_type=False,
)


def _create_enums() -> None:
    bind = op.get_bind()
    for enum in (
        coverage_scope_enum,
        region_level_enum,
        region_status_enum,
        region_alias_kind_enum,
        region_relation_enum,
        region_resolution_status_enum,
    ):
        enum.create(bind, checkfirst=False)


def _add_policy_search_columns() -> None:
    empty_array = sa.text("'[]'::jsonb")
    for name in ("keywords", "life_stages", "target_groups"):
        op.add_column(
            "policies",
            sa.Column(
                name,
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=empty_array,
                nullable=False,
            ),
        )
    op.add_column(
        "policies",
        sa.Column(
            "coverage_scope",
            coverage_scope_enum,
            server_default="unknown",
            nullable=False,
        ),
    )
    op.alter_column(
        "policies",
        "schema_version",
        server_default="1.1.0",
    )
    for name in ("keywords", "life_stages", "target_groups"):
        op.create_index(
            f"ix_policies_{name}_gin",
            "policies",
            [name],
            postgresql_using="gin",
        )
    op.create_index(
        "ix_policies_coverage_scope",
        "policies",
        ["coverage_scope"],
    )


def _create_region_tables() -> None:
    op.create_table(
        "administrative_regions",
        sa.Column("scheme", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("level", region_level_enum, nullable=False),
        sa.Column("status", region_status_enum, nullable=False),
        sa.Column("parent_code", sa.String(length=32), nullable=True),
        sa.Column(
            "aggregate_parent_code",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column("source_parent_code", sa.String(length=32), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column(
            "external_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(scheme)) > 0 AND length(trim(code)) > 0",
            name="ck_administrative_regions_identity_nonempty",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0 AND length(trim(full_name)) > 0",
            name="ck_administrative_regions_names_nonempty",
        ),
        sa.CheckConstraint(
            "parent_code IS NULL OR parent_code <> code",
            name="ck_administrative_regions_parent_not_self",
        ),
        sa.CheckConstraint(
            "aggregate_parent_code IS NULL "
            "OR aggregate_parent_code <> code",
            name="ck_administrative_regions_aggregate_parent_not_self",
        ),
        sa.CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL "
            "OR valid_from <= valid_to",
            name="ck_administrative_regions_validity_order",
        ),
        sa.ForeignKeyConstraint(
            ("scheme", "parent_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_regions_parent",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("scheme", "aggregate_parent_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_regions_aggregate_parent",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("scheme", "code"),
    )
    op.create_index(
        "ix_administrative_regions_parent",
        "administrative_regions",
        ["scheme", "parent_code"],
    )
    op.create_index(
        "ix_administrative_regions_aggregate_parent",
        "administrative_regions",
        ["scheme", "aggregate_parent_code"],
    )
    op.create_index(
        "ix_administrative_regions_status",
        "administrative_regions",
        ["scheme", "status"],
    )
    op.create_index(
        "ix_administrative_regions_external_codes_gin",
        "administrative_regions",
        ["external_codes"],
        postgresql_using="gin",
    )

    op.create_table(
        "administrative_region_aliases",
        sa.Column("scheme", sa.String(length=64), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("region_code", sa.String(length=32), nullable=False),
        sa.Column("kind", region_alias_kind_enum, nullable=False),
        sa.CheckConstraint(
            "length(trim(alias)) > 0",
            name="ck_administrative_region_aliases_alias_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ("scheme", "region_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_administrative_region_aliases_region",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("scheme", "alias", "region_code", "kind"),
        sa.UniqueConstraint(
            "scheme",
            "alias",
            "region_code",
            "kind",
            name="uq_administrative_region_aliases_identity",
        ),
    )
    op.create_index(
        "ix_administrative_region_aliases_lookup",
        "administrative_region_aliases",
        ["scheme", "alias"],
    )


def _create_policy_region_rules() -> None:
    op.create_table(
        "policy_region_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("relation", region_relation_enum, nullable=False),
        sa.Column(
            "resolution_status",
            region_resolution_status_enum,
            nullable=False,
        ),
        sa.Column("region_scheme", sa.String(length=64), nullable=True),
        sa.Column("region_code", sa.String(length=32), nullable=True),
        sa.Column("source_code", sa.Text(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "((resolution_status = 'matched' "
            "AND region_scheme IS NOT NULL AND region_code IS NOT NULL) "
            "OR (resolution_status <> 'matched' "
            "AND region_scheme IS NULL AND region_code IS NULL "
            "AND (source_code IS NOT NULL OR source_text IS NOT NULL)))",
            name="ck_policy_region_rules_resolution_identity",
        ),
        sa.CheckConstraint(
            "source_code IS NULL OR length(trim(source_code)) > 0",
            name="ck_policy_region_rules_source_code_nonempty",
        ),
        sa.CheckConstraint(
            "source_text IS NULL OR length(trim(source_text)) > 0",
            name="ck_policy_region_rules_source_text_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ("policy_id",),
            ("policies.id",),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ("region_scheme", "region_code"),
            (
                "administrative_regions.scheme",
                "administrative_regions.code",
            ),
            name="fk_policy_region_rules_region",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "policy_id",
            "region_scheme",
            "region_code",
            name="uq_policy_region_rules_canonical_region",
        ),
    )
    op.create_index(
        "ix_policy_region_rules_policy_id",
        "policy_region_rules",
        ["policy_id"],
    )
    op.create_index(
        "ix_policy_region_rules_region",
        "policy_region_rules",
        ["region_scheme", "region_code"],
    )


def _create_search_documents() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.create_table(
        "policy_search_documents",
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("title_text", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "keyword_text",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
        sa.Column(
            "summary_text",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
        sa.Column(
            "eligibility_text",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
        sa.Column(
            "support_text",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
        sa.Column("search_text", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "projection_version",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(projection_version)) > 0",
            name="ck_policy_search_documents_version_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ("policy_id",),
            ("policies.id",),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("policy_id"),
    )
    op.create_index(
        "ix_policy_search_documents_search_text_trgm",
        "policy_search_documents",
        ["search_text"],
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )


def _create_deferred_contract_triggers() -> None:
    op.execute(
        sa.text(
            """
            CREATE FUNCTION enforce_administrative_region_acyclic(
                target_scheme varchar,
                target_code varchar
            ) RETURNS void AS $$
            DECLARE
                has_cycle boolean;
            BEGIN
                WITH RECURSIVE walk(code, path, cycle) AS (
                    SELECT target_code, ARRAY[target_code]::varchar[], false
                    UNION ALL
                    SELECT edge.parent_code,
                           walk.path || edge.parent_code,
                           edge.parent_code = ANY(walk.path)
                    FROM walk
                    JOIN administrative_regions region
                      ON region.scheme = target_scheme
                     AND region.code = walk.code
                    CROSS JOIN LATERAL (
                        VALUES (region.parent_code),
                               (region.aggregate_parent_code)
                    ) AS edge(parent_code)
                    WHERE edge.parent_code IS NOT NULL
                      AND NOT walk.cycle
                )
                SELECT EXISTS(SELECT 1 FROM walk WHERE cycle)
                  INTO has_cycle;

                IF has_cycle THEN
                    RAISE EXCEPTION 'administrative region parent cycle'
                        USING ERRCODE = '23514',
                              CONSTRAINT = 'ck_administrative_regions_acyclic';
                END IF;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION check_administrative_region_acyclic()
            RETURNS trigger AS $$
            BEGIN
                PERFORM enforce_administrative_region_acyclic(
                    NEW.scheme,
                    NEW.code
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE CONSTRAINT TRIGGER ck_administrative_regions_acyclic
            AFTER INSERT OR UPDATE ON administrative_regions
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW
            EXECUTE FUNCTION check_administrative_region_acyclic()
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE FUNCTION enforce_policy_region_coverage(
                target_policy_id integer
            ) RETURNS void AS $$
            DECLARE
                policy_scope policy_coverage_scope;
                total_rules bigint;
                matched_rules bigint;
                matched_includes bigint;
            BEGIN
                SELECT coverage_scope
                  INTO policy_scope
                  FROM policies
                 WHERE id = target_policy_id;
                IF NOT FOUND THEN
                    RETURN;
                END IF;

                SELECT count(*),
                       count(*) FILTER (
                           WHERE resolution_status = 'matched'
                       ),
                       count(*) FILTER (
                           WHERE resolution_status = 'matched'
                             AND relation = 'include'
                       )
                  INTO total_rules, matched_rules, matched_includes
                  FROM policy_region_rules
                 WHERE policy_id = target_policy_id;

                IF policy_scope = 'nationwide' AND total_rules <> 0 THEN
                    RAISE EXCEPTION 'nationwide policy cannot have region rules'
                        USING ERRCODE = '23514',
                              CONSTRAINT = 'ck_policies_region_coverage';
                ELSIF policy_scope = 'regional'
                      AND matched_includes = 0 THEN
                    RAISE EXCEPTION 'regional policy requires matched include'
                        USING ERRCODE = '23514',
                              CONSTRAINT = 'ck_policies_region_coverage';
                ELSIF policy_scope = 'unknown' AND matched_rules <> 0 THEN
                    RAISE EXCEPTION 'unknown policy cannot have matched rules'
                        USING ERRCODE = '23514',
                              CONSTRAINT = 'ck_policies_region_coverage';
                END IF;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION check_policy_region_coverage()
            RETURNS trigger AS $$
            BEGIN
                IF TG_TABLE_NAME = 'policies' THEN
                    PERFORM enforce_policy_region_coverage(NEW.id);
                    RETURN NEW;
                END IF;

                IF TG_OP = 'DELETE' THEN
                    PERFORM enforce_policy_region_coverage(OLD.policy_id);
                    RETURN OLD;
                END IF;

                PERFORM enforce_policy_region_coverage(NEW.policy_id);
                IF TG_OP = 'UPDATE'
                   AND OLD.policy_id <> NEW.policy_id THEN
                    PERFORM enforce_policy_region_coverage(OLD.policy_id);
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE CONSTRAINT TRIGGER ck_policies_region_coverage
            AFTER INSERT OR UPDATE ON policies
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW
            EXECUTE FUNCTION check_policy_region_coverage()
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE CONSTRAINT TRIGGER ck_policy_region_rules_coverage
            AFTER INSERT OR UPDATE OR DELETE ON policy_region_rules
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW
            EXECUTE FUNCTION check_policy_region_coverage()
            """
        )
    )


def upgrade() -> None:
    _create_enums()
    _add_policy_search_columns()
    _create_region_tables()
    _create_policy_region_rules()
    _create_search_documents()
    _create_deferred_contract_triggers()


def downgrade() -> None:
    op.execute(
        sa.text(
            "DROP TRIGGER ck_policy_region_rules_coverage "
            "ON policy_region_rules"
        )
    )
    op.execute(
        sa.text("DROP TRIGGER ck_policies_region_coverage ON policies")
    )
    op.execute(sa.text("DROP FUNCTION check_policy_region_coverage()"))
    op.execute(
        sa.text("DROP FUNCTION enforce_policy_region_coverage(integer)")
    )
    op.execute(
        sa.text(
            "DROP TRIGGER ck_administrative_regions_acyclic "
            "ON administrative_regions"
        )
    )
    op.execute(
        sa.text("DROP FUNCTION check_administrative_region_acyclic()")
    )
    op.execute(
        sa.text(
            "DROP FUNCTION enforce_administrative_region_acyclic"
            "(varchar, varchar)"
        )
    )

    op.drop_index(
        "ix_policy_search_documents_search_text_trgm",
        table_name="policy_search_documents",
    )
    op.drop_table("policy_search_documents")
    op.drop_index(
        "ix_policy_region_rules_region",
        table_name="policy_region_rules",
    )
    op.drop_index(
        "ix_policy_region_rules_policy_id",
        table_name="policy_region_rules",
    )
    op.drop_table("policy_region_rules")
    op.drop_index(
        "ix_administrative_region_aliases_lookup",
        table_name="administrative_region_aliases",
    )
    op.drop_table("administrative_region_aliases")
    op.drop_index(
        "ix_administrative_regions_external_codes_gin",
        table_name="administrative_regions",
    )
    op.drop_index(
        "ix_administrative_regions_status",
        table_name="administrative_regions",
    )
    op.drop_index(
        "ix_administrative_regions_aggregate_parent",
        table_name="administrative_regions",
    )
    op.drop_index(
        "ix_administrative_regions_parent",
        table_name="administrative_regions",
    )
    op.drop_table("administrative_regions")

    op.drop_index("ix_policies_coverage_scope", table_name="policies")
    for name in ("target_groups", "life_stages", "keywords"):
        op.drop_index(f"ix_policies_{name}_gin", table_name="policies")
    op.drop_column("policies", "coverage_scope")
    op.drop_column("policies", "target_groups")
    op.drop_column("policies", "life_stages")
    op.drop_column("policies", "keywords")
    op.alter_column(
        "policies",
        "schema_version",
        server_default="1.0.0",
    )

    bind = op.get_bind()
    for enum in (
        region_resolution_status_enum,
        region_relation_enum,
        region_alias_kind_enum,
        region_status_enum,
        region_level_enum,
        coverage_scope_enum,
    ):
        enum.drop(bind, checkfirst=False)
