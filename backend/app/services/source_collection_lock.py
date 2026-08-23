"""Source-scoped collection locks shared by Celery workers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import Lock, RLock

from sqlalchemy import text
from sqlalchemy.orm import Session


_LOCAL_LOCKS_GUARD = RLock()
_LOCAL_LOCKS: dict[str, Lock] = {}


@contextmanager
def source_collection_lock(
    source_id: str,
    session_factory: Callable[[], Session],
) -> Iterator[bool]:
    """Try to hold one source lock for the entire external collection.

    PostgreSQL session advisory locks coordinate all worker processes. The
    in-process lock is intentionally limited to SQLite/unit-test execution.
    """
    session = session_factory()
    local_lock: Lock | None = None
    acquired = False
    is_postgresql = session.get_bind().dialect.name == "postgresql"
    try:
        if is_postgresql:
            acquired = bool(
                session.execute(
                    text(
                        "SELECT pg_try_advisory_lock("
                        "hashtextextended(:source_id, 0))"
                    ),
                    {"source_id": source_id},
                ).scalar_one()
            )
        else:
            with _LOCAL_LOCKS_GUARD:
                local_lock = _LOCAL_LOCKS.setdefault(source_id, Lock())
            acquired = local_lock.acquire(blocking=False)
        yield acquired
    finally:
        if acquired:
            if is_postgresql:
                session.execute(
                    text(
                        "SELECT pg_advisory_unlock("
                        "hashtextextended(:source_id, 0))"
                    ),
                    {"source_id": source_id},
                )
            elif local_lock is not None:
                local_lock.release()
        session.close()
