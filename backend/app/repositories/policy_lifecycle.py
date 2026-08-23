from __future__ import annotations

from collections.abc import Collection
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import ColumnElement, or_, update
from sqlalchemy.orm import Session

from app.models.policy import Policy


def public_policy_predicates(
    *,
    as_of: date | None = None,
) -> tuple[ColumnElement[bool], ...]:
    """Return the shared public visibility boundary for policy queries."""

    boundary = (
        as_of
        if as_of is not None
        else datetime.now(timezone(timedelta(hours=9))).date()
    )
    return (
        Policy.inactive_at.is_(None),
        or_(
            Policy.application_end.is_(None),
            Policy.application_end >= boundary,
        ),
    )


def mark_missing_policies_inactive(
    db: Session,
    *,
    source_id: str,
    seen_external_ids: Collection[str],
    inactive_at: datetime,
) -> int:
    """Soft-deactivate identities absent from one proven complete source run.

    Transaction ownership remains with the caller. This function must never be
    called for a failed, partial, bounded, or otherwise incomplete collection.
    """

    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a nonempty string")
    if inactive_at.tzinfo is None or inactive_at.utcoffset() is None:
        raise ValueError("inactive_at must include a timezone")
    if any(
        not isinstance(value, str) or not value
        for value in seen_external_ids
    ):
        raise ValueError("seen_external_ids must contain nonempty strings")
    normalized_ids = tuple(sorted(set(seen_external_ids)))

    statement = update(Policy).where(
        Policy.source_id == source_id,
        Policy.inactive_at.is_(None),
    )
    if normalized_ids:
        statement = statement.where(
            or_(
                Policy.external_id.is_(None),
                Policy.external_id.not_in(normalized_ids),
            )
        )
    result = db.execute(statement.values(inactive_at=inactive_at))
    return int(result.rowcount or 0)
