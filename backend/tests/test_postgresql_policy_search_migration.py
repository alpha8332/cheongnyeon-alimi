import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.services.region_reference_importer import import_region_reference


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
REGIONS_PATH = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIASES_PATH = (
    ROOT / "data" / "seeds" / "administrative_region_aliases.json"
)
PRE_SEARCH_REVISION = "20260730_0003"


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


def legacy_policy_values(external_id: str, **overrides):
    values = {
        "source_id": "psf3-postgresql",
        "source_name": "PSF3 PostgreSQL 테스트",
        "external_id": external_id,
        "title": "PSF3 검색 저장 정책",
        "categories": [],
        "regions": [],
        "education_statuses": [],
        "employment_statuses": [],
        "required_conditions": [],
        "preferred_conditions": [],
        "excluded_conditions": [],
        "source_url": f"https://fixture.invalid/policies/{external_id}",
        "collected_at": datetime(2026, 8, 3, tzinfo=timezone.utc),
        "provenance": [],
        "data_quality_status": "valid",
    }
    values.update(overrides)
    return values


def test_postgresql_search_storage_upgrade_constraints_and_downgrade():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )

    try:
        command.upgrade(config, PRE_SEARCH_REVISION)
        before = sa.MetaData()
        legacy_policies = sa.Table(
            "policies", before, autoload_with=db_engine
        )
        with db_engine.begin() as connection:
            legacy_id = connection.execute(
                legacy_policies.insert()
                .values(**legacy_policy_values("PSF3-LEGACY"))
                .returning(legacy_policies.c.id)
            ).scalar_one()

        command.upgrade(config, "head")
        inspector = sa.inspect(db_engine)
        for table_name in (
            "administrative_regions",
            "administrative_region_aliases",
            "policy_region_rules",
            "policy_search_documents",
        ):
            assert inspector.has_table(table_name)

        metadata = sa.MetaData()
        policies = sa.Table("policies", metadata, autoload_with=db_engine)
        regions = sa.Table(
            "administrative_regions", metadata, autoload_with=db_engine
        )
        rules = sa.Table(
            "policy_region_rules", metadata, autoload_with=db_engine
        )
        documents = sa.Table(
            "policy_search_documents", metadata, autoload_with=db_engine
        )
        with db_engine.connect() as connection:
            backfilled = connection.execute(
                sa.select(
                    policies.c.schema_version,
                    policies.c.keywords,
                    policies.c.life_stages,
                    policies.c.target_groups,
                    policies.c.coverage_scope,
                ).where(policies.c.id == legacy_id)
            ).one()
            extension_count = connection.execute(
                sa.text(
                    "SELECT count(*) FROM pg_extension "
                    "WHERE extname = 'pg_trgm'"
                )
            ).scalar_one()
        assert backfilled.schema_version == "1.0.0"
        assert backfilled.keywords == []
        assert backfilled.life_stages == []
        assert backfilled.target_groups == []
        assert backfilled.coverage_scope == "unknown"
        assert extension_count == 1

        with session_factory() as db:
            imported = import_region_reference(
                db, REGIONS_PATH, ALIASES_PATH
            )
        assert imported.inserted_regions == 538
        assert imported.inserted_aliases == 1080

        with db_engine.begin() as connection:
            regional_id = connection.execute(
                policies.insert()
                .values(
                    **legacy_policy_values("PSF3-REGIONAL"),
                    schema_version="1.1.0",
                    keywords=["월세"],
                    life_stages=["청년"],
                    target_groups=["청년가구"],
                    coverage_scope="regional",
                )
                .returning(policies.c.id)
            ).scalar_one()
            connection.execute(
                rules.insert().values(
                    policy_id=regional_id,
                    relation="include",
                    resolution_status="matched",
                    region_scheme="kr-bjd-20260803",
                    region_code="4413000000",
                    source_code="44130",
                    source_text="천안시",
                )
            )
            connection.execute(
                documents.insert().values(
                    policy_id=regional_id,
                    title_text="청년 월세 지원",
                    keyword_text="월세 청년",
                    summary_text="",
                    eligibility_text="",
                    support_text="월 20만원",
                    search_text="청년 월세 지원 월 20만원",
                    projection_version="1.0.0",
                )
            )

        with db_engine.connect() as connection:
            stored = connection.execute(
                sa.select(
                    policies.c.keywords,
                    rules.c.region_code,
                    documents.c.search_text,
                    documents.c.updated_at,
                )
                .join(rules, rules.c.policy_id == policies.c.id)
                .join(documents, documents.c.policy_id == policies.c.id)
                .where(policies.c.id == regional_id)
            ).one()
            dongnam = connection.execute(
                sa.select(
                    regions.c.parent_code,
                    regions.c.aggregate_parent_code,
                ).where(
                    regions.c.scheme == "kr-bjd-20260803",
                    regions.c.code == "4413100000",
                )
            ).one()
        assert stored.keywords == ["월세"]
        assert stored.region_code == "4413000000"
        assert stored.search_text == "청년 월세 지원 월 20만원"
        assert stored.updated_at.tzinfo is not None
        assert dongnam.parent_code == "4400000000"
        assert dongnam.aggregate_parent_code == "4413000000"

        with pytest.raises(IntegrityError):
            with db_engine.begin() as connection:
                connection.execute(
                    rules.insert().values(
                        policy_id=regional_id,
                        relation="exclude",
                        resolution_status="matched",
                        region_scheme="kr-bjd-20260803",
                        region_code="4413000000",
                        source_text="천안시 제외",
                    )
                )

        with pytest.raises(IntegrityError):
            with db_engine.begin() as connection:
                connection.execute(
                    policies.insert().values(
                        **legacy_policy_values("PSF3-REGIONAL-INVALID"),
                        schema_version="1.1.0",
                        coverage_scope="regional",
                    )
                )

        with db_engine.begin() as connection:
            unknown_id = connection.execute(
                policies.insert()
                .values(
                    **legacy_policy_values("PSF3-UNKNOWN"),
                    schema_version="1.1.0",
                    coverage_scope="unknown",
                )
                .returning(policies.c.id)
            ).scalar_one()
            connection.execute(
                rules.insert().values(
                    policy_id=unknown_id,
                    relation="include",
                    resolution_status="unmapped",
                    source_code="99999",
                )
            )

        with pytest.raises(IntegrityError):
            with db_engine.begin() as connection:
                connection.execute(
                    regions.insert(),
                    [
                        {
                            "scheme": "cycle-test",
                            "code": "A",
                            "name": "A",
                            "full_name": "A",
                            "level": "district",
                            "status": "active",
                        },
                        {
                            "scheme": "cycle-test",
                            "code": "B",
                            "name": "B",
                            "full_name": "B",
                            "level": "district",
                            "status": "active",
                        },
                    ],
                )
                connection.execute(
                    regions.update()
                    .where(
                        regions.c.scheme == "cycle-test",
                        regions.c.code == "A",
                    )
                    .values(parent_code="B")
                )
                connection.execute(
                    regions.update()
                    .where(
                        regions.c.scheme == "cycle-test",
                        regions.c.code == "B",
                    )
                    .values(parent_code="A")
                )

        command.downgrade(config, PRE_SEARCH_REVISION)
        downgraded_inspector = sa.inspect(db_engine)
        assert not downgraded_inspector.has_table("administrative_regions")
        assert not downgraded_inspector.has_table("policy_region_rules")
        downgraded = sa.MetaData()
        downgraded_policies = sa.Table(
            "policies", downgraded, autoload_with=db_engine
        )
        assert "keywords" not in downgraded_policies.c
        with db_engine.connect() as connection:
            preserved = connection.execute(
                sa.select(
                    downgraded_policies.c.schema_version,
                    downgraded_policies.c.external_id,
                ).where(downgraded_policies.c.id == legacy_id)
            ).one()
        assert preserved.schema_version == "1.0.0"
        assert preserved.external_id == "PSF3-LEGACY"

        command.upgrade(config, "head")
        upgraded_again = sa.MetaData()
        upgraded_policies = sa.Table(
            "policies", upgraded_again, autoload_with=db_engine
        )
        with db_engine.connect() as connection:
            round_trip = connection.execute(
                sa.select(
                    upgraded_policies.c.keywords,
                    upgraded_policies.c.coverage_scope,
                ).where(upgraded_policies.c.id == legacy_id)
            ).one()
        assert round_trip.keywords == []
        assert round_trip.coverage_scope == "unknown"
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
