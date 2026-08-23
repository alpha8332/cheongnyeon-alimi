from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.collection_run import CollectionRun
from app.services.collection_queue import (
    COLLECTION_TASK_NAME,
    CollectionQueuePublishError,
    publish_collection_run,
)
from app.services.collection_runs import CollectionRunCounts, CollectionRunWriter
from app.services.source_collection_lock import source_collection_lock
from app.worker import tasks
from app.worker.celery_app import celery_app


def _factory(db):
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )


def test_publish_uses_run_id_as_idempotent_celery_task_id():
    calls = []

    def sender(name, **kwargs):
        calls.append((name, kwargs))
        return SimpleNamespace(id=kwargs["task_id"])

    from uuid import uuid4

    writer_id = uuid4()
    task_id = publish_collection_run(
        writer_id,
        "youthcenter-api",
        100,
        sender=sender,
    )

    assert task_id == str(writer_id)
    assert calls[0][0] == COLLECTION_TASK_NAME
    assert calls[0][1]["task_id"] == str(writer_id)
    assert calls[0][1]["args"] == (
        str(writer_id),
        "youthcenter-api",
        100,
    )
    assert calls[0][1]["queue"] == "collection"


def test_publish_redacts_broker_exception_details():
    def sender(*args, **kwargs):
        raise RuntimeError("redis://user:secret@broker.invalid")

    from uuid import uuid4

    with pytest.raises(CollectionQueuePublishError) as captured:
        publish_collection_run(
            uuid4(),
            "youthcenter-api",
            1,
            sender=sender,
        )

    assert str(captured.value) == "RuntimeError"
    assert "secret" not in str(captured.value)


def test_worker_execution_is_terminal_redelivery_safe(db, monkeypatch):
    factory = _factory(db)
    writer = CollectionRunWriter(factory)
    run_id = writer.enqueue(
        source_id="youthcenter-api",
        trigger_type="admin",
        requested_count=1,
    )
    calls = []

    def fake_execute(
        received_run_id,
        source_id,
        requested_count,
        *,
        session_factory,
    ):
        calls.append(received_run_id)
        CollectionRunWriter(session_factory).finish(
            received_run_id,
            status="succeeded",
            counts=CollectionRunCounts(requested_count=requested_count),
        )

    monkeypatch.setattr(tasks, "SessionLocal", factory)
    monkeypatch.setattr(tasks, "execute_manual_collection_run", fake_execute)

    assert tasks.execute_queued_collection(
        run_id,
        "youthcenter-api",
        1,
    ) == "succeeded"
    assert tasks.execute_queued_collection(
        run_id,
        "youthcenter-api",
        1,
    ) == "succeeded"
    assert calls == [run_id]


def test_source_lock_rejects_parallel_same_source_in_process(db):
    factory = _factory(db)

    with source_collection_lock("youthcenter-api", factory) as first:
        with source_collection_lock("youthcenter-api", factory) as second:
            assert first is True
            assert second is False


def test_celery_delivery_contract_is_late_ack_and_single_prefetch():
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_ignore_result is True


def test_acceptance_probe_is_disabled_outside_test_environments(
    db,
    monkeypatch,
):
    factory = _factory(db)
    writer = CollectionRunWriter(factory)
    run_id = writer.enqueue(
        source_id="queue-acceptance-probe",
        trigger_type="cli",
    )
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    monkeypatch.setattr(tasks.settings, "ENVIRONMENT", "production")

    assert tasks.acceptance_probe_task(run_id=str(run_id)) == "failed"

    session = factory()
    try:
        run = session.get(CollectionRun, run_id)
        assert run.status == "failed"
        assert run.error_type == "AcceptanceProbeDisabled"
    finally:
        session.close()


def test_acceptance_probe_transitions_to_succeeded_in_acceptance(
    db,
    monkeypatch,
):
    factory = _factory(db)
    writer = CollectionRunWriter(factory)
    run_id = writer.enqueue(
        source_id="queue-acceptance-probe",
        trigger_type="cli",
    )
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    monkeypatch.setattr(tasks.settings, "ENVIRONMENT", "acceptance")

    assert tasks.acceptance_probe_task(run_id=str(run_id)) == "succeeded"

    session = factory()
    try:
        run = session.get(CollectionRun, run_id)
        assert run.status == "succeeded"
        assert run.finished_at is not None
    finally:
        session.close()


def test_scheduler_publishes_the_same_collection_task_boundary(
    db,
    monkeypatch,
):
    factory = _factory(db)
    published = []
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    monkeypatch.setattr(
        "app.services.collection_queue.publish_collection_run",
        lambda run_id, source_id, requested_count: published.append(
            (run_id, source_id, requested_count)
        ),
    )
    monkeypatch.setattr(
        tasks.settings,
        "COLLECTION_SCHEDULE_SOURCE_ID",
        "youthcenter-api",
    )
    monkeypatch.setattr(
        tasks.settings,
        "COLLECTION_SCHEDULE_REQUESTED_COUNT",
        25,
    )

    run_id = tasks.enqueue_scheduled_source_task()

    session = factory()
    try:
        run = session.get(CollectionRun, UUID(run_id))
        assert run.status == "queued"
        assert run.trigger_type == "scheduler"
        assert run.requested_count == 25
        assert published == [(run.run_id, "youthcenter-api", 25)]
    finally:
        session.close()
