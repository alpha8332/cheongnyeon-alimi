from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.collection_run import CollectionRun
from app.models.admin_auth import AdminAuthState
from app.models.policy import Policy
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
INITIAL_REVISION = "20260728_0001"
COLLECTION_RUN_REVISION = "20260730_0002"
TIMESTAMP_REVISION = "20260730_0003"
SEARCH_REVISION = "20260803_0004"
QUALITY_REVISION = "20260810_0005"
ELIGIBILITY_REVISION = "20260810_0006"
LIFECYCLE_REVISION = "20260824_0007"
QUEUE_REVISION = "20260824_0008"
ACTIVE_SOURCE_REVISION = "20260824_0009"
COMPLETENESS_REVISION = "20260824_0010"
PUBLIC_DATASET_REVISION = "20260824_0011"
HEAD_REVISION = "20260825_0012"


def alembic_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "alembic"),
    )
    config.attributes["database_url"] = (
        "postgresql://migration:masked@database:5432/policies"
    )
    return config


def render_upgrade_sql() -> str:
    config = alembic_config()
    output = StringIO()
    config.output_buffer = output
    command.upgrade(config, "head", sql=True)
    return output.getvalue()


def render_downgrade_sql() -> str:
    config = alembic_config()
    output = StringIO()
    config.output_buffer = output
    command.downgrade(config, f"{HEAD_REVISION}:base", sql=True)
    return output.getvalue()


def test_collection_quality_revision_is_the_single_alembic_head():
    scripts = ScriptDirectory.from_config(alembic_config())
    revision = scripts.get_current_head()

    assert revision == HEAD_REVISION
    assert (
        scripts.get_revision(revision).down_revision
        == PUBLIC_DATASET_REVISION
    )
    assert (
        scripts.get_revision(PUBLIC_DATASET_REVISION).down_revision
        == COMPLETENESS_REVISION
    )
    assert (
        scripts.get_revision(COMPLETENESS_REVISION).down_revision
        == ACTIVE_SOURCE_REVISION
    )
    assert (
        scripts.get_revision(ACTIVE_SOURCE_REVISION).down_revision
        == QUEUE_REVISION
    )
    assert (
        scripts.get_revision(QUEUE_REVISION).down_revision
        == LIFECYCLE_REVISION
    )
    assert (
        scripts.get_revision(LIFECYCLE_REVISION).down_revision
        == ELIGIBILITY_REVISION
    )
    assert (
        scripts.get_revision(ELIGIBILITY_REVISION).down_revision
        == QUALITY_REVISION
    )
    assert (
        scripts.get_revision(QUALITY_REVISION).down_revision
        == SEARCH_REVISION
    )
    assert (
        scripts.get_revision(SEARCH_REVISION).down_revision
        == TIMESTAMP_REVISION
    )
    assert (
        scripts.get_revision(TIMESTAMP_REVISION).down_revision
        == COLLECTION_RUN_REVISION
    )
    assert (
        scripts.get_revision(COLLECTION_RUN_REVISION).down_revision
        == INITIAL_REVISION
    )
    assert (
        scripts.get_revision(INITIAL_REVISION).down_revision
        is None
    )


def test_upgrade_sql_matches_postgresql_policy_contract():
    sql = render_upgrade_sql()

    assert "CREATE TABLE policies" in sql
    assert sql.count(" JSONB NOT NULL") == 8
    assert "ADD COLUMN keywords JSONB" in sql
    assert "ADD COLUMN life_stages JSONB" in sql
    assert "ADD COLUMN target_groups JSONB" in sql
    assert "ADD COLUMN eligibility_summary JSONB" in sql
    assert "ADD COLUMN last_seen_at TIMESTAMP WITH TIME ZONE" in sql
    assert "ADD COLUMN last_verified_at TIMESTAMP WITH TIME ZONE" in sql
    assert "ADD COLUMN inactive_at TIMESTAMP WITH TIME ZONE" in sql
    assert "last_seen_at = collected_at" in sql
    assert "last_verified_at = updated_at" in sql
    assert "SET CONSTRAINTS ALL IMMEDIATE" in sql
    assert "CONSTRAINT ck_policies_inactive_after_last_seen CHECK" in sql
    assert "CREATE INDEX ix_policies_application_end" in sql
    assert "CREATE INDEX ix_policies_inactive_at" in sql
    assert "external_codes JSONB" in sql
    assert "TIMESTAMP WITH TIME ZONE" in sql
    assert "CREATE TYPE policy_application_schedule AS ENUM" in sql
    assert "CREATE TYPE policy_application_status AS ENUM" in sql
    assert "CREATE TYPE policy_data_quality_status AS ENUM" in sql
    assert "USING gin (categories)" in sql
    assert "USING gin (regions)" in sql
    assert "CONSTRAINT uq_policies_source_external UNIQUE" in sql
    assert "CONSTRAINT ck_policies_age_order CHECK" in sql
    assert "CONSTRAINT ck_policies_application_date_order CHECK" in sql
    assert (
        "UPDATE policies SET updated_at = created_at "
        "WHERE updated_at < created_at"
    ) in sql
    assert "CONSTRAINT ck_policies_timestamp_order CHECK" in sql
    assert "CREATE TYPE policy_coverage_scope AS ENUM" in sql
    assert "CREATE TYPE administrative_region_level AS ENUM" in sql
    assert "CREATE TABLE administrative_regions" in sql
    assert "CREATE TABLE administrative_region_aliases" in sql
    assert "CREATE TABLE policy_region_rules" in sql
    assert "CREATE TABLE policy_search_documents" in sql
    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in sql
    assert "gin (search_text gin_trgm_ops)" in sql
    assert "CREATE CONSTRAINT TRIGGER ck_policies_region_coverage" in sql
    assert "CREATE CONSTRAINT TRIGGER ck_administrative_regions_acyclic" in sql

    for column in Policy.__table__.columns:
        if column.name in {
            "keywords",
            "life_stages",
                "target_groups",
                "coverage_scope",
                "eligibility_summary",
                "last_seen_at",
                "last_verified_at",
                "inactive_at",
            }:
            assert f"ADD COLUMN {column.name} " in sql
        else:
            assert f"\n    {column.name} " in sql


def test_upgrade_sql_matches_collection_run_contract():
    sql = render_upgrade_sql()

    assert "CREATE TABLE collection_runs" in sql
    assert "CREATE TYPE collection_run_type AS ENUM" in sql
    assert "CREATE TYPE collection_run_trigger_type AS ENUM" in sql
    assert "CREATE TYPE collection_run_status AS ENUM" in sql
    assert "UUID NOT NULL" in sql
    assert "CONSTRAINT ck_collection_runs_counts_nonnegative CHECK" in sql
    assert "CONSTRAINT ck_collection_runs_terminal_finished_at CHECK" in sql
    assert "CREATE INDEX ix_collection_runs_started_at" in sql
    assert "ADD COLUMN duplicate_count INTEGER DEFAULT '0' NOT NULL" in sql
    assert "ADD COLUMN rejected_count INTEGER DEFAULT '0' NOT NULL" in sql
    assert "ADD VALUE IF NOT EXISTS 'queued' BEFORE 'running'" in sql
    assert "status IN ('queued', 'running')" in sql
    assert "CREATE UNIQUE INDEX uq_collection_runs_active_source" in sql
    assert "ADD COLUMN is_complete_snapshot BOOLEAN DEFAULT false NOT NULL" in sql

    for column in CollectionRun.__table__.columns:
        if column.name in {
            "duplicate_count",
            "rejected_count",
            "is_complete_snapshot",
        }:
            assert f"ADD COLUMN {column.name} " in sql
        else:
            assert f"\n    {column.name} " in sql


def test_upgrade_sql_matches_public_dataset_projection_contract():
    sql = render_upgrade_sql()

    assert "CREATE TABLE public_dataset_installations" in sql
    assert "CREATE TABLE public_dataset_memberships" in sql
    assert "CREATE TYPE public_dataset_installation_status AS ENUM" in sql
    assert "uq_public_dataset_installations_one_active" in sql
    assert "status = 'active'" in sql
    assert "ck_public_dataset_installations_manifest_sha256_length" in sql
    assert "ck_public_dataset_installations_artifact_sha256_length" in sql
    assert "FOREIGN KEY(policy_id) REFERENCES policies (id) ON DELETE RESTRICT" in sql

    for model in (PublicDatasetInstallation, PublicDatasetMembership):
        for column in model.__table__.columns:
            assert f"\n    {column.name} " in sql


def test_upgrade_sql_matches_admin_auth_state_contract():
    sql = render_upgrade_sql()

    assert "CREATE TABLE admin_auth_state" in sql
    assert "ck_admin_auth_state_singleton" in sql
    assert "ck_admin_auth_state_pin_hash_length" in sql
    assert "ck_admin_auth_state_session_generation_positive" in sql

    for column in AdminAuthState.__table__.columns:
        assert f"\n    {column.name} " in sql


def test_downgrade_sql_removes_table_indexes_and_enum_types():
    sql = render_downgrade_sql()

    assert "DROP COLUMN rejected_count" in sql
    assert "DROP TABLE public_dataset_memberships" in sql
    assert "DROP TABLE admin_auth_state" in sql
    assert "DROP TABLE public_dataset_installations" in sql
    assert "DROP TYPE public_dataset_installation_status" in sql
    assert "DROP COLUMN duplicate_count" in sql
    assert "DROP COLUMN is_complete_snapshot" in sql
    assert "DROP COLUMN eligibility_summary" in sql
    assert "DROP COLUMN inactive_at" in sql
    assert "DROP COLUMN last_verified_at" in sql
    assert "DROP COLUMN last_seen_at" in sql
    assert "DROP TABLE collection_runs" in sql
    assert "DROP CONSTRAINT ck_policies_timestamp_order" in sql
    assert "DROP TYPE collection_run_status" in sql
    assert "DROP TYPE collection_run_trigger_type" in sql
    assert "DROP TYPE collection_run_type" in sql
    assert "DROP INDEX ix_policies_categories_gin" in sql
    assert "DROP INDEX ix_policies_regions_gin" in sql
    assert "DROP TABLE policies" in sql
    assert "DROP TYPE policy_data_quality_status" in sql
    assert "DROP TYPE policy_application_status" in sql
    assert "DROP TYPE policy_application_schedule" in sql
    assert "DROP TABLE policy_search_documents" in sql
    assert "DROP TABLE policy_region_rules" in sql
    assert "DROP TABLE administrative_region_aliases" in sql
    assert "DROP TABLE administrative_regions" in sql
    assert "DROP TYPE policy_region_resolution_status" in sql
    assert "DROP TYPE policy_coverage_scope" in sql
