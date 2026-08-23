"""Idempotent central collection tasks."""

from __future__ import annotations

import random
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import logger
from app.models.collection_run import CollectionRun
from app.repositories.collection_run_admin import get_active_running_collection_run
from app.services.collection_runs import CollectionRunCounts, CollectionRunWriter
from app.services.manual_collection import execute_manual_collection_run
from app.services.source_collection_lock import source_collection_lock
from app.worker.celery_app import celery_app


def _retry_delay(retries: int) -> int:
    cap = min(
        2 ** (retries + 1),
        settings.COLLECTION_TASK_RETRY_BACKOFF_MAX_SECONDS,
    )
    return random.randint(1, max(1, cap))


def _mark_lock_exhausted(run_id: UUID) -> None:
    writer = CollectionRunWriter(SessionLocal)
    writer.finish(
        run_id,
        status="failed",
        counts=CollectionRunCounts(failed_count=1),
        error_type="SourceCollectionLockTimeout",
    )


def execute_queued_collection(
    run_id: UUID,
    source_id: str,
    requested_count: int,
) -> str:
    """Execute or safely acknowledge one broker delivery."""
    writer = CollectionRunWriter(SessionLocal)
    with source_collection_lock(source_id, SessionLocal) as acquired:
        if not acquired:
            return "busy"
        current = writer.mark_running(run_id)
        if current != "running":
            return current
        execute_manual_collection_run(
            run_id,
            source_id,
            requested_count,
            session_factory=SessionLocal,
        )
    session = SessionLocal()
    try:
        completed = session.get(CollectionRun, run_id)
        if completed is None:
            raise LookupError("collection run was not found after execution")
        return str(completed.status)
    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="collection.collect_source",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=settings.COLLECTION_TASK_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.COLLECTION_TASK_TIME_LIMIT_SECONDS,
    max_retries=settings.COLLECTION_TASK_MAX_RETRIES,
)
def collect_source_task(
    self,
    run_id: str,
    source_id: str,
    requested_count: int,
) -> str:
    parsed_run_id = UUID(run_id)
    outcome = execute_queued_collection(
        parsed_run_id,
        source_id,
        requested_count,
    )
    if outcome != "busy":
        return outcome

    if self.request.retries >= settings.COLLECTION_TASK_MAX_RETRIES:
        _mark_lock_exhausted(parsed_run_id)
        return "failed"
    logger.warning(
        "collection_source_lock_busy",
        extra={
            "component": "collector",
            "collection_run_id": run_id,
            "source_id": source_id,
            "retry": self.request.retries + 1,
        },
    )
    raise self.retry(countdown=_retry_delay(self.request.retries))


@celery_app.task(
    name="collection.enqueue_scheduled_source",
    soft_time_limit=30,
    time_limit=60,
)
def enqueue_scheduled_source_task() -> str:
    """Create a durable scheduled run only when the source is idle."""
    source_id = settings.COLLECTION_SCHEDULE_SOURCE_ID
    session = SessionLocal()
    try:
        active = get_active_running_collection_run(session, source_id)
        if active is not None:
            return f"active:{active.run_id}"
        run = CollectionRun(
            source_id=source_id,
            run_type="collection",
            trigger_type="scheduler",
            status="queued",
            requested_count=settings.COLLECTION_SCHEDULE_REQUESTED_COUNT,
        )
        session.add(run)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            active = get_active_running_collection_run(session, source_id)
            if active is None:
                raise
            return f"active:{active.run_id}"
        session.refresh(run)
        run_id = run.run_id
    finally:
        session.close()

    from app.services.collection_queue import (
        CollectionQueuePublishError,
        publish_collection_run,
    )

    try:
        publish_collection_run(
            run_id,
            source_id,
            settings.COLLECTION_SCHEDULE_REQUESTED_COUNT,
        )
    except CollectionQueuePublishError:
        CollectionRunWriter(SessionLocal).finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(
                requested_count=settings.COLLECTION_SCHEDULE_REQUESTED_COUNT,
                failed_count=1,
            ),
            error_type="CollectionQueuePublishError",
        )
        return f"failed:{run_id}"
    return str(run_id)


@celery_app.task(
    name="collection.acceptance_probe",
    soft_time_limit=15,
    time_limit=30,
)
def acceptance_probe_task(run_id: str) -> str:
    """Exercise Redis→worker→PostgreSQL without contacting a live Source."""
    parsed_run_id = UUID(run_id)
    writer = CollectionRunWriter(SessionLocal)
    if settings.ENVIRONMENT not in {"acceptance", "test"}:
        writer.finish(
            parsed_run_id,
            status="failed",
            counts=CollectionRunCounts(failed_count=1),
            error_type="AcceptanceProbeDisabled",
        )
        return "failed"
    current = writer.mark_running(parsed_run_id)
    if current != "running":
        return current
    writer.finish(
        parsed_run_id,
        status="succeeded",
        counts=CollectionRunCounts(),
    )
    return "succeeded"
