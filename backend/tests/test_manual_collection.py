from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import sessionmaker

from app.models.collection_run import CollectionRun
from app.services.manual_collection import (
    execute_complete_collection_run,
    execute_manual_collection_run,
)
from app.services.manual_collection_contract import MANUAL_COLLECTION_SOURCE_IDS
from collectors.base import CollectionResult
from collectors import default_registry


class FakeCollector:
    source_id = "cheonan-youthcenter-web"

    def collect(self, options):
        return CollectionResult(
            source_id=self.source_id,
            request_count=2,
            item_count=1,
            detail_count=1,
            stored_paths=(Path("one.json"), Path("two.json")),
        )


class FakeRegistry:
    def create(self, source_id):
        assert source_id == "cheonan-youthcenter-web"
        return FakeCollector()


class FailingRegistry:
    def create(self, source_id):
        raise RuntimeError("expected failure")


def _runtime_result():
    replay = SimpleNamespace(
        extracted_count=1,
        accepted_count=1,
        partial_count=0,
        invalid_count=0,
        regional_skipped_count=0,
        cross_source_skipped_count=0,
    )
    database = SimpleNamespace(
        invalid=0,
        duplicate=0,
        rejected=0,
        inserted=1,
        updated=0,
        unchanged=0,
        skipped=0,
        failed=0,
    )
    return SimpleNamespace(replay=replay, database=database)


def _complete_runtime_result():
    result = _runtime_result()
    result.replay.raw_document_count = 2
    result.is_complete_snapshot = True
    return result


def _create_run(db):
    run = CollectionRun(
        source_id="cheonan-youthcenter-web",
        run_type="collection",
        trigger_type="admin",
        status="running",
        requested_count=1,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.run_id


def test_manual_collection_finishes_same_run(db, tmp_path):
    run_id = _create_run(db)
    factory = sessionmaker(bind=db.get_bind())
    execute_manual_collection_run(
        run_id,
        "cheonan-youthcenter-web",
        1,
        registry=FakeRegistry(),
        importer=lambda *args, **kwargs: _runtime_result(),
        session_factory=factory,
        raw_root=tmp_path,
        decision_root=tmp_path / "decisions",
    )

    db.expire_all()
    run = db.get(CollectionRun, run_id)
    assert run.status == "succeeded"
    assert run.finished_at is not None
    assert run.raw_document_count == 2
    assert run.accepted_count == 1
    assert run.inserted_count == 1
    assert run.failed_count == 0
    assert run.is_complete_snapshot is False


def test_complete_collection_persists_release_evidence(db, tmp_path):
    run_id = _create_run(db)
    factory = sessionmaker(bind=db.get_bind())

    def snapshot_collector(*args, **kwargs):
        return SimpleNamespace(snapshot_id="a" * 32, item_count=1)

    execute_complete_collection_run(
        run_id,
        "cheonan-youthcenter-web",
        100,
        request_budget=12,
        registry=FakeRegistry(),
        importer=lambda *args, **kwargs: _complete_runtime_result(),
        snapshot_collector=snapshot_collector,
        session_factory=factory,
        raw_root=tmp_path,
        decision_root=tmp_path / "decisions",
    )

    db.expire_all()
    run = db.get(CollectionRun, run_id)
    assert run.status == "succeeded"
    assert run.is_complete_snapshot is True
    assert run.requested_count == 1


def test_manual_collection_failure_is_terminal(db, tmp_path):
    run_id = _create_run(db)
    factory = sessionmaker(bind=db.get_bind())

    execute_manual_collection_run(
        run_id,
        "cheonan-youthcenter-web",
        1,
        registry=FailingRegistry(),
        session_factory=factory,
        raw_root=tmp_path,
        decision_root=tmp_path / "decisions",
    )

    db.expire_all()
    run = db.get(CollectionRun, run_id)
    assert run.status == "failed"
    assert run.finished_at is not None
    assert run.failed_count == 1
    assert run.error_type == "RuntimeError"


def test_admin_source_contract_matches_registered_collectors():
    assert MANUAL_COLLECTION_SOURCE_IDS == default_registry.source_ids()
