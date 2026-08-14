import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import create_db_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.runtime_importer import import_runtime_raw  # noqa: E402
from collectors.cheonan_youthcenter import (  # noqa: E402
    APPROVED_EXTERNAL_ID,
    BOARD_URL,
    SOURCE_ID,
)
from collectors.raw import (  # noqa: E402
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.runtime import RuntimeReplayError  # noqa: E402
from collectors.storage import RawDocumentStore  # noqa: E402


FIXTURE_ROOT = (
    ROOT / "data" / "fixtures" / "html" / SOURCE_ID
)


def _normalize_evidence_datetimes(value):
    if isinstance(value, dict):
        return {
            key: (
                datetime.fromisoformat(item.replace("Z", "+00:00"))
                if key == "collected_at"
                else _normalize_evidence_datetimes(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_evidence_datetimes(item) for item in value]
    return value


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


def _migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    return config


def _save_batch(
    store: RawDocumentStore,
    *,
    collected_at: datetime,
    detail_payload: bytes,
) -> tuple[RawPolicyDocument, ...]:
    list_payload = (FIXTURE_ROOT / "list_normal.html").read_bytes()
    response = RawPolicyDocument.from_bytes(
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=RawDocumentRole.LIST_RESPONSE,
        external_id=None,
        parent_document_id=None,
        source_url=BOARD_URL,
        collected_at=collected_at,
        content_type="text/html; charset=utf-8",
        raw_format=RawFormat.HTML,
        raw_payload=list_payload,
        http_status=200,
        collector_version="test/1.0",
    )
    item = RawPolicyDocument.from_bytes(
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=RawDocumentRole.LIST_ITEM,
        external_id=APPROVED_EXTERNAL_ID,
        parent_document_id=response.document_id,
        source_url=BOARD_URL,
        collected_at=collected_at,
        content_type="text/html; charset=utf-8",
        raw_format=RawFormat.HTML,
        raw_payload=list_payload,
        http_status=200,
        collector_version="test/1.0",
    )
    detail = RawPolicyDocument.from_bytes(
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=RawDocumentRole.DETAIL_RESPONSE,
        external_id=APPROVED_EXTERNAL_ID,
        parent_document_id=None,
        source_url=BOARD_URL,
        collected_at=collected_at,
        content_type="text/html; charset=utf-8",
        raw_format=RawFormat.HTML,
        raw_payload=detail_payload,
        http_status=200,
        collector_version="test/1.0",
    )
    for document in (response, item, detail):
        store.save(document)
    return response, item, detail


def test_cheonan_web_runtime_is_idempotent_and_drift_safe() -> None:
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    collected_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    normal_detail = (FIXTURE_ROOT / "detail_normal.html").read_bytes()
    changed_support = "변경된 주거 안전장비를 2년간 지원"
    changed_detail = normal_detail.replace(
        "주거 안전장비를 1년간 지원".encode("utf-8"),
        changed_support.encode("utf-8"),
    )
    drift_detail = (
        FIXTURE_ROOT / "detail_selector_drift.html"
    ).read_bytes()

    try:
        command.upgrade(config, "head")
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            first_batch = _save_batch(
                store,
                collected_at=collected_at,
                detail_payload=normal_detail,
            )

            with session_factory() as db:
                inserted = import_runtime_raw(
                    db,
                    raw_root=temp_dir,
                    source_id=SOURCE_ID,
                    limit=1,
                )
            with session_factory() as db:
                unchanged = import_runtime_raw(
                    db,
                    raw_root=temp_dir,
                    source_id=SOURCE_ID,
                    limit=1,
                )
                policy = db.scalar(
                    sa.select(Policy).where(
                        Policy.source_id == SOURCE_ID,
                        Policy.external_id == APPROVED_EXTERNAL_ID,
                    )
                )
                assert policy is not None
                policy_id = policy.id

            assert inserted.database.inserted == 1
            assert inserted.replay.partial_count == 1
            assert unchanged.database.inserted == 0
            assert unchanged.database.updated == 0
            assert unchanged.database.unchanged == 1
            assert policy.application_status is None
            assert policy.data_quality_status == "partial"
            assert policy.required_conditions == []
            assert policy.excluded_conditions == []
            assert policy.eligibility_summary["coverage"] == "partial"
            assert len(policy.eligibility_summary["requirements"]) == 1
            assert len(policy.eligibility_summary["exclusions"]) == 1
            assert len(policy.eligibility_summary["documents"]) == 1
            assert len(policy.eligibility_summary["unknowns"]) == 1
            assert len(
                policy.eligibility_summary["institutional_contacts"]
            ) == 2
            assert {
                item["raw_document_id"] for item in policy.provenance
            } == {document.document_id for document in first_batch}

            def override_get_db():
                with session_factory() as db:
                    yield db

            app.dependency_overrides[get_db] = override_get_db
            try:
                with TestClient(
                    app,
                    raise_server_exceptions=False,
                ) as client:
                    hidden = client.get(f"/api/v1/policies/{policy_id}")
                    visible = client.get(
                        f"/api/v1/policies/{policy_id}",
                        params={"include_partial": "true"},
                    )
            finally:
                app.dependency_overrides.pop(get_db, None)

            assert hidden.status_code == 404
            assert visible.status_code == 200
            assert visible.json()["source_id"] == SOURCE_ID
            assert visible.json()["external_id"] == APPROVED_EXTERNAL_ID
            assert visible.json()["application_status"] is None
            assert visible.json()["data_quality_status"] == "partial"
            assert (
                _normalize_evidence_datetimes(
                    visible.json()["eligibility_summary"]
                )
                == _normalize_evidence_datetimes(
                    policy.eligibility_summary
                )
            )
            assert "provenance" not in visible.json()

            refreshed_batch = _save_batch(
                store,
                collected_at=collected_at + timedelta(hours=12),
                detail_payload=normal_detail,
            )
            with session_factory() as db:
                refreshed = import_runtime_raw(
                    db,
                    raw_root=temp_dir,
                    source_id=SOURCE_ID,
                    limit=1,
                )
                refreshed_policy = db.get(Policy, policy_id)
                assert refreshed_policy is not None

            assert refreshed.database.updated == 0
            assert refreshed.database.unchanged == 1
            assert refreshed_batch != first_batch
            assert {
                item["raw_document_id"]
                for item in refreshed_policy.provenance
            } == {document.document_id for document in first_batch}

            changed_batch = _save_batch(
                store,
                collected_at=collected_at + timedelta(days=1),
                detail_payload=changed_detail,
            )
            with session_factory() as db:
                updated = import_runtime_raw(
                    db,
                    raw_root=temp_dir,
                    source_id=SOURCE_ID,
                    limit=1,
                )
            with session_factory() as db:
                changed_policy = db.get(Policy, policy_id)
                assert changed_policy is not None

            assert updated.database.inserted == 0
            assert updated.database.updated == 1
            assert updated.database.unchanged == 0
            assert changed_policy.support_content == changed_support
            assert {
                item["raw_document_id"]
                for item in changed_policy.provenance
            } == {document.document_id for document in changed_batch}

            _save_batch(
                store,
                collected_at=collected_at + timedelta(days=2),
                detail_payload=drift_detail,
            )
            with session_factory() as db:
                with pytest.raises(
                    RuntimeReplayError,
                    match="runtime extraction failed",
                ):
                    import_runtime_raw(
                        db,
                        raw_root=temp_dir,
                        source_id=SOURCE_ID,
                        limit=1,
                    )
            with session_factory() as db:
                preserved = db.get(Policy, policy_id)
                policy_count = db.scalar(
                    sa.select(sa.func.count()).select_from(Policy)
                )
                assert preserved is not None

            assert policy_count == 1
            assert preserved.support_content == changed_support
            assert {
                item["raw_document_id"] for item in preserved.provenance
            } == {document.document_id for document in changed_batch}
    finally:
        try:
            app.dependency_overrides.pop(get_db, None)
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
