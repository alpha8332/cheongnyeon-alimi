import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

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


def test_postgresql_atomic_upsert_identity_and_outcomes():
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

        with session_factory() as db:
            first = import_programs(db, programs)
            second = import_programs(db, programs)

        assert first.inserted == 4
        assert first.updated == 0
        assert first.unchanged == 0
        assert second.inserted == 0
        assert second.updated == 0
        assert second.unchanged == 4

        changed_programs = copy.deepcopy(programs)
        changed_programs[0]["title"] = "PostgreSQL에서 변경된 합성 정책"
        with session_factory() as db:
            changed = import_programs(db, changed_programs)

        assert changed.updated == 1
        assert changed.unchanged == 3

        missing_identity = copy.deepcopy(programs[0])
        missing_identity["external_id"] = None
        with session_factory() as db:
            skipped = import_programs(db, [missing_identity])

        assert skipped.skipped == 1
        assert skipped.issues[0].code == "missing_external_id"

        invalid_age = copy.deepcopy(programs[0])
        invalid_age["external_id"] = "PG-B3-INVALID"
        invalid_age["age_min"] = 151
        with session_factory() as db:
            failed = import_programs(db, [invalid_age])

        assert failed.failed == 1
        assert failed.issues[0].code == "database_write_failed"
        assert failed.issues[0].error_type == "IntegrityError"

        concurrent_program = copy.deepcopy(programs[0])
        concurrent_program["external_id"] = "PG-B3-CONCURRENT"
        barrier = Barrier(2)

        def concurrent_import():
            with session_factory() as db:
                barrier.wait()
                return import_programs(db, [concurrent_program])

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: concurrent_import(), range(2)))

        assert sum(result.inserted for result in outcomes) == 1
        assert sum(result.unchanged for result in outcomes) == 1
        assert sum(result.updated for result in outcomes) == 0

        with session_factory() as db:
            total = db.scalar(sa.select(sa.func.count()).select_from(Policy))
            concurrent_count = db.scalar(
                sa.select(sa.func.count())
                .select_from(Policy)
                .where(
                    Policy.source_id == concurrent_program["source_id"],
                    Policy.external_id == concurrent_program["external_id"],
                )
            )

        assert total == 5
        assert concurrent_count == 1
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
