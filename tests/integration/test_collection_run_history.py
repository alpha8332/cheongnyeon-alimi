import os
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import (  # noqa: E402
    create_db_engine,
    create_session_factory,
)
from app.models.collection_run import CollectionRun  # noqa: E402
from app.services.collection_runs import (  # noqa: E402
    CollectionRunCounts,
    CollectionRunWriter,
)


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
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "alembic"),
    )
    config.attributes["database_url"] = database_url
    return config


def test_postgresql_seed_and_runtime_run_history_lifecycle():
    database_url = _test_database_url()
    config = _migration_config(database_url)
    engine = create_db_engine(database_url)
    session_factory = create_session_factory(engine)

    try:
        command.upgrade(config, "head")
        writer = CollectionRunWriter(session_factory)

        seed_run_id = writer.start(
            source_id=None,
            run_type="seed_import",
            trigger_type="cli",
        )
        writer.finish(
            seed_run_id,
            status="succeeded",
            counts=CollectionRunCounts(
                requested_count=4,
                accepted_count=4,
                partial_count=2,
                inserted_count=4,
            ),
        )

        runtime_run_id = writer.start(
            source_id="youthcenter-api",
            run_type="runtime_import",
            trigger_type="cli",
            requested_count=10,
        )
        writer.finish(
            runtime_run_id,
            status="partial_failure",
            counts=CollectionRunCounts(
                requested_count=10,
                raw_document_count=4,
                extracted_count=3,
                accepted_count=2,
                invalid_count=1,
                duplicate_count=1,
                rejected_count=1,
                inserted_count=2,
            ),
        )

        failed_run_id = writer.start(
            source_id="bokjiro-central-welfare-api",
            run_type="runtime_import",
            trigger_type="admin",
            requested_count=5,
        )
        writer.finish(
            failed_run_id,
            status="failed",
            counts=CollectionRunCounts(
                requested_count=5,
                failed_count=1,
            ),
            error_type="OperationalError",
        )

        session = session_factory()
        try:
            runs = session.execute(
                sa.select(CollectionRun).order_by(
                    CollectionRun.started_at,
                    CollectionRun.run_id,
                )
            ).scalars().all()
        finally:
            session.close()

        assert len(runs) == 3
        assert runs[0].source_id is None
        assert runs[0].status == "succeeded"
        assert runs[0].partial_count == 2
        assert runs[1].source_id == "youthcenter-api"
        assert runs[1].status == "partial_failure"
        assert runs[1].invalid_count == 1
        assert runs[1].duplicate_count == 1
        assert runs[1].rejected_count == 1
        assert runs[2].trigger_type == "admin"
        assert runs[2].status == "failed"
        assert runs[2].error_type == "OperationalError"
    finally:
        try:
            command.downgrade(config, "base")
            inspector = sa.inspect(engine)
            assert not inspector.has_table("collection_runs")
            assert not inspector.has_table("policies")
        finally:
            engine.dispose()
