import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.collection_run import (
    COLLECTION_RUN_STATUS_VALUES,
    COLLECTION_RUN_TRIGGER_TYPE_VALUES,
    COLLECTION_RUN_TYPE_VALUES,
    CollectionRun,
    utc_now,
)


TERMINAL_STATUSES = frozenset(
    {"succeeded", "partial_failure", "failed"}
)
ERROR_TYPE_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)


@dataclass(frozen=True)
class CollectionRunCounts:
    requested_count: int = 0
    raw_document_count: int = 0
    extracted_count: int = 0
    accepted_count: int = 0
    partial_count: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    rejected_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0

    def __post_init__(self) -> None:
        if any(value < 0 for value in asdict(self).values()):
            raise ValueError("collection run counts must be nonnegative")


class CollectionRunWriter:
    """Persist run summaries independently from the policy transaction."""

    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory

    def start(
        self,
        *,
        source_id: str | None,
        run_type: str,
        trigger_type: str,
        requested_count: int = 0,
        started_at: datetime | None = None,
    ) -> UUID:
        _validate_choice("run_type", run_type, COLLECTION_RUN_TYPE_VALUES)
        _validate_choice(
            "trigger_type",
            trigger_type,
            COLLECTION_RUN_TRIGGER_TYPE_VALUES,
        )
        counts = CollectionRunCounts(requested_count=requested_count)
        session = self._session_factory()
        try:
            run = CollectionRun(
                source_id=_normalized_source_id(source_id),
                run_type=run_type,
                trigger_type=trigger_type,
                started_at=started_at or utc_now(),
                status="running",
                **asdict(counts),
            )
            session.add(run)
            session.commit()
            run_id = run.run_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return run_id

    def enqueue(
        self,
        *,
        source_id: str,
        run_type: str = "collection",
        trigger_type: str,
        requested_count: int = 0,
        started_at: datetime | None = None,
    ) -> UUID:
        """Create the durable run record before publishing its queue task."""
        _validate_choice("run_type", run_type, COLLECTION_RUN_TYPE_VALUES)
        _validate_choice(
            "trigger_type",
            trigger_type,
            COLLECTION_RUN_TRIGGER_TYPE_VALUES,
        )
        counts = CollectionRunCounts(requested_count=requested_count)
        session = self._session_factory()
        try:
            run = CollectionRun(
                source_id=_normalized_source_id(source_id),
                run_type=run_type,
                trigger_type=trigger_type,
                started_at=started_at or utc_now(),
                status="queued",
                **asdict(counts),
            )
            session.add(run)
            session.commit()
            run_id = run.run_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return run_id

    def mark_running(self, run_id: UUID) -> str:
        """Claim a queued run; terminal redeliveries remain no-ops."""
        session = self._session_factory()
        try:
            run = session.get(CollectionRun, run_id)
            if run is None:
                raise LookupError("collection run was not found")
            current_status = str(run.status)
            if current_status in TERMINAL_STATUSES:
                return current_status
            if current_status not in {"queued", "running"}:
                raise ValueError("collection run has an invalid active status")
            run.status = "running"
            session.commit()
            return "running"
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def finish(
        self,
        run_id: UUID,
        *,
        status: str,
        counts: CollectionRunCounts,
        error_type: str | None = None,
        finished_at: datetime | None = None,
        is_complete_snapshot: bool = False,
    ) -> None:
        if status not in TERMINAL_STATUSES:
            raise ValueError(
                "terminal collection run status must be one of "
                f"{sorted(TERMINAL_STATUSES)}"
            )
        _validate_choice(
            "status",
            status,
            COLLECTION_RUN_STATUS_VALUES,
        )
        safe_error_type = _safe_error_type(error_type)

        session = self._session_factory()
        try:
            run = session.get(CollectionRun, run_id)
            if run is None:
                raise LookupError("collection run was not found")
            if run.status not in {"queued", "running"}:
                raise ValueError("collection run is already terminal")

            run.status = status
            run.finished_at = finished_at or utc_now()
            run.error_type = safe_error_type
            run.is_complete_snapshot = is_complete_snapshot
            for field, value in asdict(counts).items():
                setattr(run, field, value)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _validate_choice(
    field: str,
    value: str,
    choices: tuple[str, ...],
) -> None:
    if value not in choices:
        raise ValueError(f"{field} must be one of {list(choices)}")


def _normalized_source_id(source_id: str | None) -> str | None:
    if source_id is None:
        return None
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be null or a nonempty string")
    return source_id


def _safe_error_type(error_type: Any) -> str | None:
    if error_type is None:
        return None
    if not isinstance(error_type, str):
        raise TypeError("error_type must be a string or null")
    if (
        not error_type
        or len(error_type) > 255
        or ERROR_TYPE_PATTERN.fullmatch(error_type) is None
    ):
        raise ValueError(
            "error_type must be an exception identifier, not a message"
        )
    return error_type
