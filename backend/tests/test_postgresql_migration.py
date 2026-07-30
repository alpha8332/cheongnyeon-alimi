import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.core.database import create_db_engine


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PRE_TIMESTAMP_CONSTRAINT_REVISION = "20260730_0002"


def require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "alembic"),
    )
    config.attributes["database_url"] = database_url
    return config


def test_postgresql_upgrade_jsonb_round_trip_and_downgrade():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url, environment="test")

    try:
        command.upgrade(config, "head")

        metadata = sa.MetaData()
        policies = sa.Table("policies", metadata, autoload_with=db_engine)
        collection_runs = sa.Table(
            "collection_runs",
            metadata,
            autoload_with=db_engine,
        )
        assert isinstance(policies.c.categories.type, JSONB)
        assert isinstance(policies.c.provenance.type, JSONB)
        assert policies.c.collected_at.type.timezone is True
        assert collection_runs.c.started_at.type.timezone is True
        assert collection_runs.c.finished_at.type.timezone is True

        collected_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
        provenance = [
            {
                "raw_document_id": "a" * 32,
                "document_role": "list_item",
                "content_hash": f"sha256:{'b' * 64}",
                "collected_at": collected_at.isoformat(),
                "source_url": "https://fixture.invalid/api",
            }
        ]
        with db_engine.begin() as connection:
            policy_id = connection.execute(
                policies.insert()
                .values(
                    source_id="postgresql-integration",
                    source_name="PostgreSQL 통합 테스트",
                    external_id="PG-B2-001",
                    title="PostgreSQL B2 정책",
                    categories=["housing", "welfare"],
                    regions=["서울특별시"],
                    education_statuses=[],
                    employment_statuses=[],
                    required_conditions=[],
                    preferred_conditions=[],
                    excluded_conditions=[],
                    source_url="https://fixture.invalid/policies/PG-B2-001",
                    collected_at=collected_at,
                    provenance=provenance,
                    data_quality_status="valid",
                )
                .returning(policies.c.id)
            ).scalar_one()
            row = connection.execute(
                sa.select(
                    policies.c.categories,
                    policies.c.provenance,
                    policies.c.collected_at,
                ).where(policies.c.id == policy_id)
            ).one()

        assert row.categories == ["housing", "welfare"]
        assert row.provenance == provenance
        assert row.collected_at.astimezone(timezone.utc) == collected_at

        with pytest.raises(IntegrityError):
            with db_engine.begin() as connection:
                connection.execute(
                    policies.insert().values(
                        source_id="postgresql-integration",
                        source_name="PostgreSQL 통합 테스트",
                        external_id="PG-B2-INVALID",
                        title="잘못된 연령 범위",
                        categories=[],
                        regions=[],
                        age_min=151,
                        education_statuses=[],
                        employment_statuses=[],
                        required_conditions=[],
                        preferred_conditions=[],
                        excluded_conditions=[],
                        source_url=(
                            "https://fixture.invalid/policies/PG-B2-INVALID"
                        ),
                        collected_at=collected_at,
                        provenance=provenance,
                        data_quality_status="valid",
                    )
                )
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
            assert not sa.inspect(db_engine).has_table("collection_runs")
            with db_engine.connect() as connection:
                enum_count = connection.execute(
                    sa.text(
                        "SELECT count(*) FROM pg_type "
                        "WHERE typname IN ("
                        "'policy_application_schedule', "
                        "'policy_application_status', "
                        "'policy_data_quality_status', "
                        "'collection_run_type', "
                        "'collection_run_trigger_type', "
                        "'collection_run_status'"
                        ")"
                    )
                ).scalar_one()
            assert enum_count == 0
        finally:
            db_engine.dispose()


def test_postgresql_timestamp_migration_repairs_existing_rows():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url, environment="test")
    created_at = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    reversed_updated_at = datetime(
        2026,
        7,
        30,
        0,
        0,
        tzinfo=timezone.utc,
    )

    try:
        command.upgrade(config, PRE_TIMESTAMP_CONSTRAINT_REVISION)
        metadata = sa.MetaData()
        policies = sa.Table("policies", metadata, autoload_with=db_engine)

        with db_engine.begin() as connection:
            policy_id = connection.execute(
                policies.insert()
                .values(
                    source_id="postgresql-migration",
                    source_name="PostgreSQL Migration 테스트",
                    external_id="PG-R1-REPAIR",
                    title="역전 시각 보정 정책",
                    categories=[],
                    regions=[],
                    education_statuses=[],
                    employment_statuses=[],
                    required_conditions=[],
                    preferred_conditions=[],
                    excluded_conditions=[],
                    source_url=(
                        "https://fixture.invalid/policies/PG-R1-REPAIR"
                    ),
                    collected_at=created_at,
                    provenance=[],
                    data_quality_status="valid",
                    created_at=created_at,
                    updated_at=reversed_updated_at,
                )
                .returning(policies.c.id)
            ).scalar_one()

        command.upgrade(config, "head")

        constraint_names = {
            constraint["name"]
            for constraint in sa.inspect(db_engine).get_check_constraints(
                "policies"
            )
        }
        assert "ck_policies_timestamp_order" in constraint_names

        with db_engine.connect() as connection:
            repaired = connection.execute(
                sa.select(
                    policies.c.created_at,
                    policies.c.updated_at,
                ).where(policies.c.id == policy_id)
            ).one()
        assert repaired.updated_at == repaired.created_at

        with pytest.raises(IntegrityError):
            with db_engine.begin() as connection:
                connection.execute(
                    policies.update()
                    .where(policies.c.id == policy_id)
                    .values(updated_at=reversed_updated_at)
                )

        command.downgrade(config, PRE_TIMESTAMP_CONSTRAINT_REVISION)
        downgraded_constraint_names = {
            constraint["name"]
            for constraint in sa.inspect(db_engine).get_check_constraints(
                "policies"
            )
        }
        assert (
            "ck_policies_timestamp_order"
            not in downgraded_constraint_names
        )
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
            assert not sa.inspect(db_engine).has_table("collection_runs")
        finally:
            db_engine.dispose()
