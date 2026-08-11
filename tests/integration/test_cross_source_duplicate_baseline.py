import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
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
from app.services.aggregator_baseline import (  # noqa: E402
    load_aggregator_baseline,
)
from app.services.seed_importer import import_programs  # noqa: E402
from collectors.snapshot import (  # noqa: E402
    SnapshotManifest,
    SnapshotManifestStore,
)


def _require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def test_approved_snapshot_and_postgresql_rows_form_read_only_baseline():
    database_url = _require_test_database_url()
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    engine = create_db_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    programs = json.loads(
        (ROOT / "data" / "fixtures" / "normalized" / "programs.json")
        .read_text(encoding="utf-8")
    )
    source_counts = {
        source_id: sum(
            value["source_id"] == source_id for value in programs
        )
        for source_id in (
            "youthcenter-api",
            "bokjiro-central-welfare-api",
        )
    }

    try:
        command.upgrade(config, "head")
        with session_factory() as db:
            imported = import_programs(db, programs)
            assert imported.inserted == 4
            with tempfile.TemporaryDirectory() as temp_dir:
                store = SnapshotManifestStore(temp_dir)
                for source_id, marker in (
                    ("youthcenter-api", "1"),
                    ("bokjiro-central-welfare-api", "2"),
                ):
                    store.save(
                        SnapshotManifest(
                            snapshot_id=marker * 32,
                            source_id=source_id,
                            started_at=datetime(
                                2026, 8, 11, tzinfo=timezone.utc
                            ),
                            completed_at=datetime(
                                2026, 8, 11, 0, 1, tzinfo=timezone.utc
                            ),
                            page_size=500,
                            detail_limit=0,
                            request_budget=1,
                            request_count=1,
                            total_count=source_counts[source_id],
                            item_count=source_counts[source_id],
                            list_response_document_ids=(
                                marker * 31 + "a",
                            ),
                            detail_document_ids=(),
                        )
                    )
                baseline = load_aggregator_baseline(
                    db,
                    raw_root=temp_dir,
                    now=lambda: datetime(
                        2026, 8, 11, 1, tzinfo=timezone.utc
                    ),
                )

        assert len(baseline.records) == 4
        assert {
            value.source_id: value.database_policy_count
            for value in baseline.descriptors
        } == source_counts
    finally:
        command.downgrade(config, "base")
        engine.dispose()
