import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

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
from app.services.runtime_importer import import_runtime_raw  # noqa: E402
from app.services.region_reference_importer import (  # noqa: E402
    import_region_reference,
)
from app.services.seed_importer import import_programs  # noqa: E402
from collectors.gyeongbuk_youth import (  # noqa: E402
    DETAIL_MODAL_URL,
    LIST_JSON_URL,
    SOURCE_ID as GYEONGBUK_SOURCE_ID,
    decide_gyeongbuk_regional_policy,
)
from collectors.raw import (  # noqa: E402
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.snapshot import (  # noqa: E402
    SnapshotManifest,
    SnapshotManifestStore,
)
from collectors.storage import RawDocumentStore  # noqa: E402


def _gyeongbuk_documents() -> tuple[RawPolicyDocument, ...]:
    fixture_root = ROOT / "data" / "fixtures" / "regional" / "gyeongbuk"
    list_bytes = (fixture_root / "list_response.json").read_bytes()
    list_payload = json.loads(list_bytes)
    item_bytes = json.dumps(
        list_payload["resultList1"][0],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    collected_at = datetime(2026, 8, 11, 5, 30, tzinfo=timezone.utc)

    def raw(
        number: int,
        role: RawDocumentRole,
        payload: bytes,
        raw_format: RawFormat,
        source_url: str,
        *,
        external_id: str | None = None,
        parent_document_id: str | None = None,
        at: datetime = collected_at,
    ) -> RawPolicyDocument:
        return RawPolicyDocument.from_bytes(
            document_id=f"{number:032x}",
            source_id=GYEONGBUK_SOURCE_ID,
            source_type=SourceType.WEB,
            document_role=role,
            external_id=external_id,
            parent_document_id=parent_document_id,
            source_url=source_url,
            collected_at=at,
            content_type=(
                "application/json; charset=utf-8"
                if raw_format is RawFormat.JSON
                else "text/html; charset=utf-8"
            ),
            raw_format=raw_format,
            raw_payload=payload,
            http_status=200,
            collector_version="test/1.0",
        )

    parent = raw(
        1,
        RawDocumentRole.LIST_RESPONSE,
        list_bytes,
        RawFormat.JSON,
        LIST_JSON_URL,
    )
    item = raw(
        2,
        RawDocumentRole.LIST_ITEM,
        item_bytes,
        RawFormat.JSON,
        LIST_JSON_URL,
        external_id="1098",
        parent_document_id=parent.document_id,
    )
    detail = raw(
        3,
        RawDocumentRole.DETAIL_RESPONSE,
        (fixture_root / "detail_1098.html").read_bytes(),
        RawFormat.HTML,
        DETAIL_MODAL_URL,
        external_id="1098",
        at=collected_at + timedelta(minutes=1),
    )
    return parent, item, detail


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


def test_baseline_read_transaction_ends_before_regional_policy_write():
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

    try:
        command.upgrade(config, "head")
        with session_factory() as db:
            import_region_reference(
                db,
                ROOT / "data" / "seeds" / "administrative_regions.json",
                ROOT
                / "data"
                / "seeds"
                / "administrative_region_aliases.json",
            )
        with session_factory() as db:
            assert import_programs(db, programs).inserted == 4
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SnapshotManifestStore(temp_dir)
            raw_store = RawDocumentStore(temp_dir)
            for document in _gyeongbuk_documents():
                raw_store.save(document)
            for source_id, marker in (
                ("youthcenter-api", "1"),
                ("bokjiro-central-welfare-api", "2"),
            ):
                count = sum(
                    value["source_id"] == source_id for value in programs
                )
                store.save(
                    SnapshotManifest(
                        snapshot_id=marker * 32,
                        source_id=source_id,
                        started_at=datetime(2026, 8, 11, tzinfo=timezone.utc),
                        completed_at=datetime(
                            2026, 8, 11, 0, 1, tzinfo=timezone.utc
                        ),
                        page_size=500,
                        detail_limit=0,
                        request_budget=1,
                        request_count=1,
                        total_count=count,
                        item_count=count,
                        list_response_document_ids=(marker * 31 + "a",),
                        detail_document_ids=(),
                    )
                )
            original = decide_gyeongbuk_regional_policy
            with patch(
                "collectors.runtime.decide_gyeongbuk_regional_policy",
                side_effect=lambda policy: original(
                    policy, as_of=datetime(2026, 6, 10).date()
                ),
            ):
                with session_factory() as db:
                    result = import_runtime_raw(
                        db,
                        raw_root=temp_dir,
                        source_id=GYEONGBUK_SOURCE_ID,
                        limit=1,
                    )

        assert result.replay.accepted_count == 1
        assert result.database.inserted == 1
        assert result.database.failed == 0
    finally:
        command.downgrade(config, "base")
        engine.dispose()
