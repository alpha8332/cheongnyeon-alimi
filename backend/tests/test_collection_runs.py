from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.collection_run import CollectionRun
from app.services.collection_runs import (
    CollectionRunCounts,
    CollectionRunWriter,
)


def _writer(db) -> tuple[CollectionRunWriter, sessionmaker]:
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )
    return CollectionRunWriter(session_factory), session_factory


def test_writer_persists_source_runtime_lifecycle(db):
    writer, session_factory = _writer(db)
    started_at = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    finished_at = started_at + timedelta(seconds=5)

    run_id = writer.start(
        source_id="youthcenter-api",
        run_type="runtime_import",
        trigger_type="cli",
        requested_count=10,
        started_at=started_at,
    )
    writer.finish(
        run_id,
        status="partial_failure",
        counts=CollectionRunCounts(
            requested_count=10,
            raw_document_count=4,
            extracted_count=3,
            accepted_count=2,
            partial_count=0,
            invalid_count=1,
            duplicate_count=2,
            rejected_count=1,
            inserted_count=2,
        ),
        finished_at=finished_at,
    )

    session = session_factory()
    try:
        run = session.get(CollectionRun, run_id)
        assert run is not None
        assert run.source_id == "youthcenter-api"
        assert run.status == "partial_failure"
        assert run.accepted_count == 2
        assert run.invalid_count == 1
        assert run.duplicate_count == 2
        assert run.rejected_count == 1
        assert run.inserted_count == 2
        assert run.error_type is None
    finally:
        session.close()


def test_writer_supports_cross_source_seed_and_safe_failure_type(db):
    writer, session_factory = _writer(db)
    run_id = writer.start(
        source_id=None,
        run_type="seed_import",
        trigger_type="cli",
    )
    writer.finish(
        run_id,
        status="failed",
        counts=CollectionRunCounts(
            requested_count=4,
            accepted_count=4,
            failed_count=1,
        ),
        error_type="IntegrityError",
    )

    session = session_factory()
    try:
        run = session.get(CollectionRun, run_id)
        assert run is not None
        assert run.source_id is None
        assert run.status == "failed"
        assert run.error_type == "IntegrityError"
        assert run.failed_count == 1
    finally:
        session.close()


def test_writer_persists_queued_claim_and_terminal_redelivery(db):
    writer, session_factory = _writer(db)
    run_id = writer.enqueue(
        source_id="youthcenter-api",
        trigger_type="admin",
        requested_count=25,
    )

    session = session_factory()
    try:
        queued = session.get(CollectionRun, run_id)
        assert queued.status == "queued"
        assert queued.finished_at is None
    finally:
        session.close()

    assert writer.mark_running(run_id) == "running"
    writer.finish(
        run_id,
        status="succeeded",
        counts=CollectionRunCounts(requested_count=25),
    )
    assert writer.mark_running(run_id) == "succeeded"


def test_writer_rejects_negative_counts_and_invalid_contract_values(db):
    writer, _ = _writer(db)

    with pytest.raises(ValueError):
        CollectionRunCounts(invalid_count=-1)
    with pytest.raises(ValueError):
        CollectionRunCounts(duplicate_count=-1)
    with pytest.raises(ValueError):
        CollectionRunCounts(rejected_count=-1)
    with pytest.raises(ValueError):
        writer.start(
            source_id=" ",
            run_type="runtime_import",
            trigger_type="cli",
        )
    run_id = writer.start(
        source_id="youthcenter-api",
        run_type="runtime_import",
        trigger_type="cli",
    )
    with pytest.raises(ValueError):
        writer.finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(failed_count=1),
            error_type="password=do-not-store",
        )
    with pytest.raises(ValueError):
        writer.start(
            source_id="youthcenter-api",
            run_type="unknown",
            trigger_type="cli",
        )


def test_database_rejects_terminal_run_without_finished_at(db):
    db.add(
        CollectionRun(
            source_id="youthcenter-api",
            run_type="runtime_import",
            trigger_type="cli",
            status="failed",
            finished_at=None,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


def test_database_rejects_two_active_runs_for_same_source(db):
    db.add_all(
        [
            CollectionRun(
                source_id="youthcenter-api",
                run_type="collection",
                trigger_type="admin",
                status="queued",
            ),
            CollectionRun(
                source_id="youthcenter-api",
                run_type="collection",
                trigger_type="scheduler",
                status="running",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


def test_writer_does_not_finish_a_terminal_run_twice(db):
    writer, _ = _writer(db)
    run_id = writer.start(
        source_id="youthcenter-api",
        run_type="runtime_import",
        trigger_type="cli",
    )
    writer.finish(
        run_id,
        status="succeeded",
        counts=CollectionRunCounts(),
    )

    with pytest.raises(ValueError):
        writer.finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(failed_count=1),
        )
