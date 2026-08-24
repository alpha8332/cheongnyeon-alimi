import copy
import json
import os
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import create_db_engine  # noqa: E402
from app.models.collection_run import CollectionRun  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.collection_runs import (  # noqa: E402
    CollectionRunCounts,
    CollectionRunWriter,
)
from app.services.seed_importer import import_programs  # noqa: E402


SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
ROLLBACK_FUNCTION = "reject_dtl4_2b_policy"


def _test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def _migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    return config


def test_postgresql_recurrent_quality_and_collection_run_counts():
    database_url = _test_database_url()
    config = _migration_config(database_url)
    engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    programs = json.loads(SEED_PATH.read_text(encoding="utf-8"))[:2]

    try:
        command.upgrade(config, "head")

        with session_factory() as db:
            first = import_programs(db, programs)
            original_metadata = {
                policy.external_id: (policy.collected_at, policy.provenance)
                for policy in db.scalars(sa.select(Policy)).all()
            }
        assert first.inserted == 2

        metadata_rerun = copy.deepcopy(programs)
        metadata_rerun[0]["collected_at"] = "2026-08-10T03:00:00+00:00"
        for evidence in metadata_rerun[0]["provenance"]:
            evidence["collected_at"] = "2026-08-10T03:00:00+00:00"
        with session_factory() as db:
            metadata_only = import_programs(db, metadata_rerun)
            stored_metadata = {
                policy.external_id: (policy.collected_at, policy.provenance)
                for policy in db.scalars(sa.select(Policy)).all()
            }
        assert metadata_only.updated == 0
        assert metadata_only.unchanged == 2
        assert stored_metadata == original_metadata

        business_rerun = copy.deepcopy(programs)
        business_rerun[0]["title"] = "PostgreSQL 반복 수집 변경 정책"
        with session_factory() as db:
            business_change = import_programs(db, business_rerun)
        assert business_change.updated == 1
        assert business_change.unchanged == 1

        duplicate_batch = copy.deepcopy(business_rerun)
        duplicate_batch.append(copy.deepcopy(duplicate_batch[0]))
        with session_factory() as db:
            duplicate = import_programs(db, duplicate_batch)
            policy_count = int(
                db.scalar(sa.select(sa.func.count()).select_from(Policy)) or 0
            )
        assert duplicate.updated == 0
        assert duplicate.unchanged == 2
        assert duplicate.duplicate == 1
        assert policy_count == 2

        writer = CollectionRunWriter(session_factory)
        run_id = writer.start(
            source_id="youthcenter-api",
            run_type="runtime_import",
            trigger_type="cli",
            requested_count=3,
        )
        writer.finish(
            run_id,
            status="partial_failure",
            counts=CollectionRunCounts(
                requested_count=3,
                accepted_count=2,
                duplicate_count=1,
                rejected_count=1,
                unchanged_count=2,
            ),
        )
        with session_factory() as db:
            run = db.get(CollectionRun, run_id)
            assert run is not None
            assert run.duplicate_count == 1
            assert run.rejected_count == 1

        with engine.begin() as connection:
            connection.execute(
                sa.text(
                    f"""
                    CREATE FUNCTION {ROLLBACK_FUNCTION}()
                    RETURNS trigger AS $$
                    BEGIN
                        IF NEW.external_id = '{programs[1]['external_id']}' THEN
                            RAISE EXCEPTION 'forced DTL4-2B write failure';
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
                    CREATE TRIGGER {ROLLBACK_FUNCTION}_trigger
                    BEFORE UPDATE ON policies
                    FOR EACH ROW EXECUTE FUNCTION {ROLLBACK_FUNCTION}()
                    """
                )
            )

        failed_batch = copy.deepcopy(business_rerun)
        failed_batch[0]["title"] = "rollback 대상 첫 정책"
        failed_batch[1]["title"] = "rollback 강제 두 번째 정책"
        with session_factory() as db:
            failed = import_programs(db, failed_batch)
            stored_titles = {
                policy.external_id: policy.title
                for policy in db.scalars(sa.select(Policy)).all()
            }
        assert failed.failed == 1
        assert failed.inserted == 0
        assert failed.updated == 0
        assert failed.committed is False
        assert failed.issues[0].stage == "persist"
        assert stored_titles[programs[0]["external_id"]] == business_rerun[0][
            "title"
        ]
        assert stored_titles[programs[1]["external_id"]] == programs[1]["title"]
    finally:
        try:
            with engine.begin() as connection:
                connection.execute(
                    sa.text(
                        f"DROP FUNCTION IF EXISTS "
                        f"{ROLLBACK_FUNCTION}() CASCADE"
                    )
                )
            command.downgrade(config, "base")
        finally:
            engine.dispose()
