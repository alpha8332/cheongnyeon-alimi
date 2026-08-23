"""Execute one administrator-requested collection inside the API process."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import logger
from app.services.collection_runs import CollectionRunCounts, CollectionRunWriter


DEFAULT_RAW_ROOT = Path("runtime/raw")
DEFAULT_DECISION_ROOT = Path("runtime/decisions")


def execute_manual_collection_run(
    run_id: UUID,
    source_id: str,
    requested_count: int,
    *,
    registry=None,
    importer=None,
    session_factory=SessionLocal,
    raw_root: Path = DEFAULT_RAW_ROOT,
    decision_root: Path = DEFAULT_DECISION_ROOT,
) -> None:
    """Collect, replay, persist, and terminally finish an existing run."""
    writer = CollectionRunWriter(session_factory)
    db: Session | None = None
    try:
        from collectors import CollectionOptions, default_registry
        from app.services.runtime_importer import import_runtime_raw

        selected_registry = registry or default_registry
        selected_importer = importer or import_runtime_raw
        collector = selected_registry.create(source_id)
        collection = collector.collect(
            CollectionOptions(
                page=1,
                limit=requested_count,
                detail_limit=min(requested_count, 5),
            )
        )
        db = session_factory()
        imported = selected_importer(
            db,
            raw_root=raw_root,
            source_id=source_id,
            limit=requested_count,
            decision_root=decision_root,
        )
        counts = _result_counts(collection, imported, requested_count)
        writer.finish(
            run_id,
            status=_result_status(imported),
            counts=counts,
            is_complete_snapshot=False,
        )
        logger.info(
            "manual_collection_finished",
            extra={
                "component": "collector",
                "collection_run_id": str(run_id),
                "source_id": source_id,
                "status": _result_status(imported),
            },
        )
    except Exception as exc:
        _finish_failed(writer, run_id, requested_count, type(exc).__name__)
        logger.error(
            "manual_collection_failed",
            extra={
                "component": "collector",
                "collection_run_id": str(run_id),
                "source_id": source_id,
                "error_type": type(exc).__name__,
            },
        )
    finally:
        if db is not None:
            db.close()


def execute_complete_collection_run(
    run_id: UUID,
    source_id: str,
    page_size: int,
    *,
    request_budget: int,
    registry=None,
    importer=None,
    snapshot_collector=None,
    session_factory=SessionLocal,
    raw_root: Path = DEFAULT_RAW_ROOT,
    decision_root: Path = DEFAULT_DECISION_ROOT,
) -> None:
    """Collect and import one authority-wide snapshot for release evidence."""
    writer = CollectionRunWriter(session_factory)
    db: Session | None = None
    try:
        from collectors import default_registry
        from collectors.snapshot import SnapshotManifestStore, collect_snapshot
        from app.services.runtime_importer import import_runtime_raw

        selected_registry = registry or default_registry
        selected_importer = importer or import_runtime_raw
        selected_snapshot_collector = snapshot_collector or collect_snapshot
        manifest = selected_snapshot_collector(
            selected_registry.create(source_id),
            manifest_store=SnapshotManifestStore(raw_root),
            page_size=page_size,
            detail_limit=0,
            request_budget=request_budget,
        )
        db = session_factory()
        imported = selected_importer(
            db,
            raw_root=raw_root,
            source_id=source_id,
            limit=manifest.item_count,
            snapshot_id=manifest.snapshot_id,
            decision_root=decision_root,
        )
        if _result_status(imported) != "succeeded":
            raise RuntimeError("complete snapshot import was not successful")
        if not imported.is_complete_snapshot:
            raise RuntimeError("complete snapshot evidence was not preserved")
        writer.finish(
            run_id,
            status="succeeded",
            counts=_complete_snapshot_counts(imported, manifest.item_count),
            is_complete_snapshot=True,
        )
        logger.info(
            "complete_collection_finished",
            extra={
                "component": "collector",
                "collection_run_id": str(run_id),
                "source_id": source_id,
                "status": "succeeded",
            },
        )
    except Exception as exc:
        _finish_failed(writer, run_id, page_size, type(exc).__name__)
        logger.error(
            "complete_collection_failed",
            extra={
                "component": "collector",
                "collection_run_id": str(run_id),
                "source_id": source_id,
                "error_type": type(exc).__name__,
            },
        )
    finally:
        if db is not None:
            db.close()


def _result_status(result: Any) -> str:
    database = result.database
    if database.skipped or database.rejected or database.failed:
        return "failed"
    if result.replay.invalid_count:
        return "partial_failure" if result.replay.accepted_count else "failed"
    return "succeeded"


def _result_counts(
    collection: Any,
    result: Any,
    requested_count: int,
) -> CollectionRunCounts:
    replay = result.replay
    database = result.database
    return CollectionRunCounts(
        requested_count=requested_count,
        raw_document_count=collection.raw_document_count,
        extracted_count=replay.extracted_count,
        accepted_count=replay.accepted_count,
        partial_count=replay.partial_count,
        invalid_count=replay.invalid_count + database.invalid,
        duplicate_count=database.duplicate,
        rejected_count=replay.invalid_count + database.rejected,
        inserted_count=database.inserted,
        updated_count=database.updated,
        unchanged_count=database.unchanged,
        skipped_count=(
            database.skipped
            + replay.regional_skipped_count
            + replay.cross_source_skipped_count
        ),
        failed_count=database.failed,
    )


def _complete_snapshot_counts(
    result: Any, requested_count: int
) -> CollectionRunCounts:
    replay = result.replay
    database = result.database
    return CollectionRunCounts(
        requested_count=requested_count,
        raw_document_count=replay.raw_document_count,
        extracted_count=replay.extracted_count,
        accepted_count=replay.accepted_count,
        partial_count=replay.partial_count,
        invalid_count=replay.invalid_count + database.invalid,
        duplicate_count=database.duplicate,
        rejected_count=replay.invalid_count + database.rejected,
        inserted_count=database.inserted,
        updated_count=database.updated,
        unchanged_count=database.unchanged,
        skipped_count=(
            database.skipped
            + replay.regional_skipped_count
            + replay.cross_source_skipped_count
        ),
        failed_count=database.failed,
    )


def _finish_failed(
    writer: CollectionRunWriter,
    run_id: UUID,
    requested_count: int,
    error_type: str,
) -> None:
    try:
        writer.finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(
                requested_count=requested_count,
                failed_count=1,
            ),
            error_type=error_type,
        )
    except Exception:
        logger.exception(
            "manual_collection_failure_finalization_failed",
            extra={
                "component": "collector",
                "collection_run_id": str(run_id),
            },
        )
