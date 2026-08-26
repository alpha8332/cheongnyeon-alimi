"""Probe Celery workers without returning credentials or worker identities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectorWorkerProbe:
    broker_available: bool
    worker_count: int
    registered_source_ids: frozenset[str]
    credential_configured: dict[str, bool]


def probe_collector_workers(*, timeout_seconds: float = 1.0) -> CollectorWorkerProbe:
    """Return an aggregated, secret-free snapshot from active collection workers."""
    from app.worker.celery_app import celery_app

    try:
        replies = celery_app.control.broadcast(
            "collector_runtime_status",
            reply=True,
            timeout=timeout_seconds,
        )
    except Exception:
        return CollectorWorkerProbe(
            broker_available=False,
            worker_count=0,
            registered_source_ids=frozenset(),
            credential_configured={},
        )

    registered_source_ids: set[str] = set()
    credential_configured: dict[str, bool] = {}
    valid_worker_count = 0
    for reply in replies or ():
        if not isinstance(reply, dict):
            continue
        for payload in reply.values():
            if not isinstance(payload, dict):
                continue
            valid_worker_count += 1
            source_ids = payload.get("registered_source_ids")
            if isinstance(source_ids, list):
                registered_source_ids.update(
                    source_id
                    for source_id in source_ids
                    if isinstance(source_id, str)
                )
            statuses = payload.get("credential_configured")
            if isinstance(statuses, dict):
                for source_id, is_configured in statuses.items():
                    if isinstance(source_id, str) and isinstance(is_configured, bool):
                        credential_configured[source_id] = (
                            credential_configured.get(source_id, False)
                            or is_configured
                        )

    return CollectorWorkerProbe(
        broker_available=True,
        worker_count=valid_worker_count,
        registered_source_ids=frozenset(registered_source_ids),
        credential_configured=credential_configured,
    )
