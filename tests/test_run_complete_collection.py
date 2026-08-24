from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "backend"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.run_complete_collection import (  # noqa: E402
    CompleteCollectionError,
    queue_and_wait,
    read_run_state,
    wait_for_promotable_run,
)
from app.core.database import Base  # noqa: E402
from app.models.collection_run import CollectionRun  # noqa: E402


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _state(run_id: UUID, **overrides):
    selected = {
        "collection_run_id": str(run_id),
        "source_id": "bokjiro-central-welfare-api",
        "status": "succeeded",
        "is_complete_snapshot": True,
        "raw_document_count": 1,
        "accepted_count": 1,
        "invalid_count": 0,
        "rejected_count": 0,
        "failed_count": 0,
        "error_type": None,
    }
    selected.update(overrides)
    return selected


def test_wait_for_promotable_run_accepts_only_clean_complete_success():
    run_id = uuid4()
    states = iter(
        (
            _state(run_id, status="queued", is_complete_snapshot=False),
            _state(run_id, status="running", is_complete_snapshot=False),
            _state(run_id),
        )
    )
    ticks = iter((0.0, 0.1, 0.2, 0.3))
    result = wait_for_promotable_run(
        run_id,
        timeout_seconds=10,
        poll_interval_seconds=0.01,
        state_reader=lambda _: next(states),
        monotonic=lambda: next(ticks),
        sleeper=lambda _: None,
    )
    assert result["collection_run_id"] == str(run_id)
    assert result["is_complete_snapshot"] is True


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"status": "failed"}, "terminated with failed"),
        ({"is_complete_snapshot": False}, "evidence was not preserved"),
        ({"invalid_count": 1}, "validation failures"),
    ),
)
def test_wait_for_promotable_run_rejects_unsafe_terminal_state(
    overrides, message
):
    run_id = uuid4()
    with pytest.raises(CompleteCollectionError, match=message):
        wait_for_promotable_run(
            run_id,
            timeout_seconds=10,
            poll_interval_seconds=1,
            state_reader=lambda _: _state(run_id, **overrides),
        )


def test_failed_run_reports_safe_error_type():
    run_id = uuid4()
    with pytest.raises(
        CompleteCollectionError,
        match=r"terminated with failed \(AuthenticationError\)",
    ):
        wait_for_promotable_run(
            run_id,
            timeout_seconds=10,
            poll_interval_seconds=1,
            state_reader=lambda _: _state(
                run_id,
                status="failed",
                error_type="AuthenticationError",
            ),
        )


def test_queue_and_wait_publishes_complete_snapshot_task(
    monkeypatch, session_factory
):
    published = []

    def fake_wait(run_id, **kwargs):
        return _state(run_id)

    monkeypatch.setattr(
        "scripts.run_complete_collection.wait_for_promotable_run",
        fake_wait,
    )
    result = queue_and_wait(
        source_id="bokjiro-central-welfare-api",
        page_size=500,
        timeout_seconds=10,
        poll_interval_seconds=1,
        session_factory=session_factory,
        publisher=lambda run_id, source_id, page_size, **kwargs: published.append(
            (run_id, source_id, page_size, kwargs["complete_snapshot"])
        ),
    )
    assert result["is_complete_snapshot"] is True
    assert published[0][1:] == (
        "bokjiro-central-welfare-api",
        500,
        True,
    )


def test_queue_and_wait_allows_keyless_incheon_public_source(
    monkeypatch, session_factory
):
    published = []

    def fake_wait(run_id, **kwargs):
        return _state(
            run_id,
            source_id="data-go-kr-incheon-youth-programs",
        )

    monkeypatch.setattr(
        "scripts.run_complete_collection.wait_for_promotable_run",
        fake_wait,
    )
    result = queue_and_wait(
        source_id="data-go-kr-incheon-youth-programs",
        page_size=500,
        timeout_seconds=10,
        poll_interval_seconds=1,
        session_factory=session_factory,
        publisher=lambda run_id, source_id, page_size, **kwargs: published.append(
            (run_id, source_id, page_size, kwargs["complete_snapshot"])
        ),
    )
    assert result["source_id"] == "data-go-kr-incheon-youth-programs"
    assert published[0][1:] == (
        "data-go-kr-incheon-youth-programs",
        500,
        True,
    )


def test_queue_and_wait_refuses_non_public_source(session_factory):
    with pytest.raises(ValueError, match="not approved"):
        queue_and_wait(
            source_id="youthcenter-api",
            page_size=500,
            timeout_seconds=10,
            poll_interval_seconds=1,
            session_factory=session_factory,
            publisher=lambda *args, **kwargs: None,
        )


def test_queue_publish_failure_is_terminal(session_factory):
    def fail_publish(*args, **kwargs):
        raise ConnectionError("broker unavailable")

    with pytest.raises(CompleteCollectionError, match="queue publish failed"):
        queue_and_wait(
            source_id="bokjiro-central-welfare-api",
            page_size=500,
            timeout_seconds=10,
            poll_interval_seconds=1,
            session_factory=session_factory,
            publisher=fail_publish,
        )
    session = session_factory()
    try:
        run_id = session.scalar(select(CollectionRun.run_id))
    finally:
        session.close()
    state = read_run_state(run_id, session_factory=session_factory)
    assert state["status"] == "failed"
    assert state["failed_count"] == 1
    assert state["error_type"] == "ConnectionError"
