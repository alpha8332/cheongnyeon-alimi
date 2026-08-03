import copy
import json
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.models.administrative_region import AdministrativeRegion
from app.models.policy import Policy
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument
from app.services.policy_search_projection import (
    POLICY_SEARCH_PROJECTION_VERSION,
)
from app.services.seed_importer import import_programs


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = BACKEND_ROOT.parent / "data" / "seeds" / "initial_programs.json"
REGION_SCHEME = "test-kr-bjd"
REGION_CODE = "4413000000"
FAIL_FUNCTION = "reject_psf5_search_document"


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


def regional_program(external_id: str) -> dict:
    program = copy.deepcopy(
        json.loads(SEED_PATH.read_text(encoding="utf-8"))[0]
    )
    program["external_id"] = external_id
    program["region_text"] = "충청남도 천안시"
    program["regions"] = ["충청남도 천안시"]
    program["coverage_scope"] = "regional"
    program["region_rules"] = [
        {
            "relation": "include",
            "resolution_status": "matched",
            "region_scheme": REGION_SCHEME,
            "region_code": REGION_CODE,
            "source_code": "44130",
            "source_text": "충청남도 천안시",
        }
    ]
    return program


def test_postgresql_policy_rule_projection_transaction_and_idempotency():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    program = regional_program("PSF5-REGIONAL")

    try:
        command.upgrade(config, "head")
        with session_factory.begin() as db:
            db.add(
                AdministrativeRegion(
                    scheme=REGION_SCHEME,
                    code=REGION_CODE,
                    name="천안시",
                    full_name="충청남도 천안시",
                    level="district",
                    status="active",
                    external_codes={"test-prefix5": "44130"},
                )
            )

        with session_factory() as db:
            first = import_programs(db, [program])
            policy = db.scalar(
                sa.select(Policy).where(
                    Policy.external_id == "PSF5-REGIONAL"
                )
            )
            rule_count = db.scalar(
                sa.select(sa.func.count()).select_from(PolicyRegionRule)
            )
            document = db.get(PolicySearchDocument, policy.id)
            first_policy_updated_at = policy.updated_at
            first_document_updated_at = document.updated_at

        with session_factory() as db:
            second = import_programs(db, [program])
            policy = db.scalar(
                sa.select(Policy).where(
                    Policy.external_id == "PSF5-REGIONAL"
                )
            )
            document = db.get(PolicySearchDocument, policy.id)

        assert first.inserted == 1
        assert rule_count == 1
        assert document.projection_version == POLICY_SEARCH_PROJECTION_VERSION
        assert "월세" in document.search_text
        assert second.unchanged == 1
        assert policy.updated_at == first_policy_updated_at
        assert document.updated_at == first_document_updated_at

        with session_factory.begin() as db:
            document = db.scalar(sa.select(PolicySearchDocument))
            document.projection_version = "stale"

        with session_factory() as db:
            repaired = import_programs(db, [program])
            policy = db.scalar(
                sa.select(Policy).where(
                    Policy.external_id == "PSF5-REGIONAL"
                )
            )
            document = db.get(PolicySearchDocument, policy.id)

        assert repaired.updated == 1
        assert document.projection_version == POLICY_SEARCH_PROJECTION_VERSION

        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    f"""
                    CREATE FUNCTION {FAIL_FUNCTION}()
                    RETURNS trigger AS $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM policies
                             WHERE id = NEW.policy_id
                               AND external_id = 'PSF5-FAIL'
                        ) THEN
                            RAISE EXCEPTION 'PSF5 forced projection failure';
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                    """
                )
            )
            connection.execute(
                sa.text(
                    f"""
                    CREATE TRIGGER {FAIL_FUNCTION}_trigger
                    BEFORE INSERT OR UPDATE ON policy_search_documents
                    FOR EACH ROW EXECUTE FUNCTION {FAIL_FUNCTION}()
                    """
                )
            )

        rollback_batch = [
            regional_program("PSF5-ROLLBACK-OK"),
            regional_program("PSF5-FAIL"),
        ]
        with session_factory() as db:
            failed = import_programs(db, rollback_batch)
            policy_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(Policy)
                .where(
                    Policy.external_id.in_(
                        ["PSF5-ROLLBACK-OK", "PSF5-FAIL"]
                    )
                )
            )
            related_rule_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(PolicyRegionRule)
                .join(Policy)
                .where(
                    Policy.external_id.in_(
                        ["PSF5-ROLLBACK-OK", "PSF5-FAIL"]
                    )
                )
            )
            related_document_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(PolicySearchDocument)
                .join(Policy)
                .where(
                    Policy.external_id.in_(
                        ["PSF5-ROLLBACK-OK", "PSF5-FAIL"]
                    )
                )
            )

        assert failed.failed == 1
        assert failed.committed is False
        assert failed.inserted == 0
        assert failed.issues[0].code == "database_write_failed"
        assert policy_count == 0
        assert related_rule_count == 0
        assert related_document_count == 0
    finally:
        try:
            with db_engine.begin() as connection:
                connection.execute(
                    sa.text(
                        f"DROP FUNCTION IF EXISTS {FAIL_FUNCTION}() CASCADE"
                    )
                )
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
