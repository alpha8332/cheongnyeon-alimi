"""Queue one complete source snapshot and wait for terminal evidence."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import SessionLocal  # noqa: E402
from app.models.collection_run import CollectionRun  # noqa: E402
from app.services.collection_queue import publish_collection_run  # noqa: E402
from app.services.collection_runs import (  # noqa: E402
    CollectionRunCounts,
    CollectionRunWriter,
)


TERMINAL_STATUSES = frozenset({"succeeded", "partial_failure", "failed"})
SAFE_SOURCE_IDS = frozenset(
    {
        "bokjiro-central-welfare-api",
        "data-go-kr-incheon-youth-programs",
    }
)


class CompleteCollectionError(RuntimeError):
    """A queued complete collection did not produce promotable evidence."""


def read_run_state(
    run_id: UUID,
    *,
    session_factory=SessionLocal,
) -> dict[str, Any]:
    session = session_factory()
    try:
        run = session.get(CollectionRun, run_id)
        if run is None:
            raise CompleteCollectionError("collection run was not found")
        return {
            "collection_run_id": str(run.run_id),
            "source_id": run.source_id,
            "status": str(run.status),
            "is_complete_snapshot": bool(run.is_complete_snapshot),
            "raw_document_count": int(run.raw_document_count),
            "accepted_count": int(run.accepted_count),
            "invalid_count": int(run.invalid_count),
            "rejected_count": int(run.rejected_count),
            "failed_count": int(run.failed_count),
            "error_type": run.error_type,
        }
    finally:
        session.close()


def wait_for_promotable_run(
    run_id: UUID,
    *,
    timeout_seconds: int,
    poll_interval_seconds: float,
    state_reader: Callable[[UUID], dict[str, Any]],
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")
    deadline = monotonic() + timeout_seconds
    while True:
        state = state_reader(run_id)
        status = state.get("status")
        if status in TERMINAL_STATUSES:
            if status != "succeeded":
                error_type = state.get("error_type")
                error_suffix = f" ({error_type})" if error_type else ""
                raise CompleteCollectionError(
                    f"complete collection terminated with {status}"
                    f"{error_suffix}"
                )
            if state.get("is_complete_snapshot") is not True:
                raise CompleteCollectionError(
                    "complete snapshot evidence was not preserved"
                )
            if any(
                state.get(field) != 0
                for field in ("invalid_count", "rejected_count", "failed_count")
            ):
                raise CompleteCollectionError(
                    "complete collection contains validation failures"
                )
            return state
        if status not in {"queued", "running"}:
            raise CompleteCollectionError("collection run has an invalid status")
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise CompleteCollectionError("complete collection timed out")
        sleeper(min(poll_interval_seconds, remaining))


def queue_and_wait(
    *,
    source_id: str,
    page_size: int,
    timeout_seconds: int,
    poll_interval_seconds: float,
    session_factory=SessionLocal,
    publisher=publish_collection_run,
) -> dict[str, Any]:
    if source_id not in SAFE_SOURCE_IDS:
        raise ValueError("source_id is not approved for public collection")
    if not 1 <= page_size <= 500:
        raise ValueError("page_size must be from 1 to 500")
    writer = CollectionRunWriter(session_factory)
    run_id = writer.enqueue(
        source_id=source_id,
        trigger_type="scheduler",
        requested_count=page_size,
    )
    try:
        publisher(
            run_id,
            source_id,
            page_size,
            complete_snapshot=True,
        )
    except Exception as exc:
        writer.finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(
                requested_count=page_size,
                failed_count=1,
            ),
            error_type=type(exc).__name__,
        )
        raise CompleteCollectionError("collection queue publish failed") from exc
    return wait_for_promotable_run(
        run_id,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        state_reader=lambda selected_id: read_run_state(
            selected_id,
            session_factory=session_factory,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-id",
        default="bokjiro-central-welfare-api",
        choices=sorted(SAFE_SOURCE_IDS),
    )
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    try:
        args = parser.parse_args()
        result = queue_and_wait(
            source_id=args.source_id,
            page_size=args.page_size,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, CompleteCollectionError) as exc:
        print(
            f"W6_P4_COMPLETE_COLLECTION_BLOCKED: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
