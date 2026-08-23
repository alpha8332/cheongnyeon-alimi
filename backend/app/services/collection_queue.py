"""Publish durable CollectionRun identifiers to the central broker."""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from app.core.config import settings


COLLECTION_TASK_NAME = "collection.collect_source"


class CollectionQueuePublishError(RuntimeError):
    """Raised when a durable queued run cannot be published to Redis."""


def publish_collection_run(
    run_id: UUID,
    source_id: str,
    requested_count: int,
    *,
    complete_snapshot: bool = False,
    sender: Callable[..., Any] | None = None,
) -> str:
    """Publish one idempotent task using the run UUID as Celery task ID."""
    if sender is None:
        from app.worker.celery_app import celery_app

        sender = celery_app.send_task

    try:
        result = sender(
            COLLECTION_TASK_NAME,
            args=(str(run_id), source_id, requested_count, complete_snapshot),
            task_id=str(run_id),
            queue=settings.COLLECTION_QUEUE_NAME,
            retry=True,
            retry_policy={
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 1,
                "interval_max": 3,
            },
        )
    except Exception as exc:
        raise CollectionQueuePublishError(type(exc).__name__) from exc
    return str(result.id)
