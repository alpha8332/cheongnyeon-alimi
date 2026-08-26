"""Build the administrator collector status projection."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.collection_run import CollectionRun
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)
from app.schemas.admin_collector import (
    AdminCollectorStatus,
    AdminCollectorStatusResponse,
    CollectorQueueStatus,
    CollectorRunSummary,
    CollectorScheduleStatus,
)
from app.services.collection_run_admin import check_is_stale
from app.services.collector_catalog import COLLECTOR_CATALOG
from app.services.collector_runtime_status import (
    CollectorWorkerProbe,
    probe_collector_workers,
)
from app.services.manual_collection_contract import MANUAL_COLLECTION_SOURCE_IDS


def _public_policy_counts(db: Session) -> dict[str, int]:
    active_version = db.scalar(
        select(PublicDatasetInstallation.dataset_version).where(
            PublicDatasetInstallation.status == "active"
        )
    )
    if active_version is None:
        return {}
    return {
        source_id: count
        for source_id, count in db.execute(
            select(
                PublicDatasetMembership.source_id,
                func.count(PublicDatasetMembership.policy_id),
            )
            .where(PublicDatasetMembership.dataset_version == active_version)
            .group_by(PublicDatasetMembership.source_id)
        ).all()
    }


def _run_summary(run: CollectionRun | None) -> CollectorRunSummary | None:
    if run is None:
        return None
    return CollectorRunSummary(
        run_id=run.run_id,
        status=str(run.status),
        trigger_type=str(run.trigger_type),
        started_at=run.started_at,
        finished_at=run.finished_at,
        is_stale=check_is_stale(run.started_at, run.finished_at, str(run.status)),
        requested_count=run.requested_count,
        inserted_count=run.inserted_count,
        updated_count=run.updated_count,
        failed_count=run.failed_count,
        error_type=run.error_type,
    )


def _runs_by_source(
    db: Session,
    source_ids: tuple[str, ...],
) -> tuple[dict[str, CollectionRun], dict[str, CollectionRun]]:
    runs = db.scalars(
        select(CollectionRun)
        .where(CollectionRun.source_id.in_(source_ids))
        .order_by(CollectionRun.started_at.desc())
    ).all()
    latest: dict[str, CollectionRun] = {}
    active: dict[str, CollectionRun] = {}
    for run in runs:
        if run.source_id is None:
            continue
        latest.setdefault(run.source_id, run)
        if run.status in {"queued", "running"} and run.finished_at is None:
            active.setdefault(run.source_id, run)
    return latest, active


def _runtime_projection(
    source_id: str,
    *,
    credential_required: bool,
    probe: CollectorWorkerProbe,
) -> tuple[str, bool | None, str]:
    if probe.worker_count == 0:
        credential_status = "unknown" if credential_required else "not_required"
        return "unavailable", None, credential_status

    worker_registered = source_id in probe.registered_source_ids
    if not worker_registered:
        credential_status = "unknown" if credential_required else "not_required"
        return "unavailable", False, credential_status

    if not credential_required:
        return "ready", True, "not_required"

    configured = probe.credential_configured.get(source_id)
    if configured is None:
        return "unknown", True, "unknown"
    if configured:
        return "ready", True, "configured"
    return "configuration_required", True, "missing"


def get_admin_collector_status(
    db: Session,
    *,
    worker_probe: CollectorWorkerProbe | None = None,
) -> AdminCollectorStatusResponse:
    """Return collector, queue, schedule, dataset, and run status in one view."""
    probe = worker_probe or probe_collector_workers()
    source_ids = tuple(item.source_id for item in COLLECTOR_CATALOG)
    public_counts = _public_policy_counts(db)
    latest_runs, active_runs = _runs_by_source(db, source_ids)
    manual_sources = frozenset(MANUAL_COLLECTION_SOURCE_IDS)

    collectors = []
    for descriptor in COLLECTOR_CATALOG:
        runtime_status, worker_registered, credential_status = _runtime_projection(
            descriptor.source_id,
            credential_required=descriptor.credential_required,
            probe=probe,
        )
        collectors.append(
            AdminCollectorStatus(
                source_id=descriptor.source_id,
                display_name=descriptor.display_name,
                source_type=descriptor.source_type,
                manual_run_enabled=descriptor.source_id in manual_sources,
                runtime_status=runtime_status,
                worker_registered=worker_registered,
                credential_status=credential_status,
                public_policy_count=public_counts.get(descriptor.source_id, 0),
                active_run=_run_summary(active_runs.get(descriptor.source_id)),
                last_run=_run_summary(latest_runs.get(descriptor.source_id)),
            )
        )

    return AdminCollectorStatusResponse(
        generated_at=datetime.now(timezone.utc),
        queue=CollectorQueueStatus(
            queue_name=settings.COLLECTION_QUEUE_NAME,
            broker_available=probe.broker_available,
            worker_available=probe.worker_count > 0,
            worker_count=probe.worker_count,
        ),
        schedule=CollectorScheduleStatus(
            enabled=settings.COLLECTION_SCHEDULE_ENABLED,
            source_id=settings.COLLECTION_SCHEDULE_SOURCE_ID,
            requested_count=settings.COLLECTION_SCHEDULE_REQUESTED_COUNT,
            complete_snapshot=settings.COLLECTION_SCHEDULE_COMPLETE_SNAPSHOT,
            cron_hour=settings.COLLECTION_SCHEDULE_CRON_HOUR,
            cron_minute=settings.COLLECTION_SCHEDULE_CRON_MINUTE,
            timezone="Asia/Seoul",
        ),
        collectors=collectors,
    )
