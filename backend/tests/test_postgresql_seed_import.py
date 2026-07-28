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
from app.models.policy import Policy
from app.services.seed_importer import import_programs


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = BACKEND_ROOT.parent / "data" / "seeds" / "initial_programs.json"


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


def test_postgresql_seed_validation_dry_run_and_rollback():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url, environment="test")
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    programs = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    try:
        command.upgrade(config, "head")

        dry_run_program = copy.deepcopy(programs[0])
        dry_run_program["external_id"] = "PG-B4-DRY-RUN"
        with session_factory() as db:
            dry_run = import_programs(
                db,
                [dry_run_program],
                dry_run=True,
            )
            dry_run_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(Policy)
                .where(Policy.external_id == "PG-B4-DRY-RUN")
            )

        assert dry_run.inserted == 1
        assert dry_run.committed is False
        assert dry_run_count == 0

        rejected_batch = copy.deepcopy(programs[:2])
        rejected_batch[1].pop("title")
        with session_factory() as db:
            rejected = import_programs(db, rejected_batch)
            rejected_count = db.scalar(
                sa.select(sa.func.count()).select_from(Policy)
            )

        assert rejected.rejected == 1
        assert rejected.inserted == 0
        assert rejected.committed is False
        assert rejected_count == 0

        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    """
                    CREATE FUNCTION reject_b4_test_policy()
                    RETURNS trigger AS $$
                    BEGIN
                        IF NEW.external_id = 'PG-B4-FAIL' THEN
                            RAISE EXCEPTION 'B4 forced write failure';
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                    """
                )
            )
            connection.execute(
                sa.text(
                    """
                    CREATE TRIGGER reject_b4_test_policy_trigger
                    BEFORE INSERT OR UPDATE ON policies
                    FOR EACH ROW EXECUTE FUNCTION reject_b4_test_policy()
                    """
                )
            )

        rollback_batch = copy.deepcopy(programs[:2])
        rollback_batch[0]["external_id"] = "PG-B4-ROLLBACK-OK"
        rollback_batch[1]["external_id"] = "PG-B4-FAIL"
        with session_factory() as db:
            failed = import_programs(db, rollback_batch)
            rollback_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(Policy)
                .where(
                    Policy.external_id.in_(
                        ["PG-B4-ROLLBACK-OK", "PG-B4-FAIL"]
                    )
                )
            )

        assert failed.failed == 1
        assert failed.inserted == 0
        assert failed.committed is False
        assert failed.issues[0].code == "database_write_failed"
        assert failed.issues[0].error_type == "InternalError"
        assert rollback_count == 0
    finally:
        try:
            with db_engine.begin() as connection:
                connection.execute(
                    sa.text(
                        "DROP FUNCTION IF EXISTS "
                        "reject_b4_test_policy() CASCADE"
                    )
                )
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
