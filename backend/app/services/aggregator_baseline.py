"""Read-only approved aggregator baseline loader for regional imports."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.models.policy_search import PolicyRegionRule
from collectors.cross_source_duplicate import (
    AGGREGATOR_SOURCE_IDS,
    AggregatorBaseline,
    BaselineDescriptor,
    BaselineRecord,
    CrossSourceDuplicateError,
)
from collectors.snapshot import SnapshotError, SnapshotManifestStore


class AggregatorBaselineLoadError(RuntimeError):
    """The approved snapshot and PostgreSQL rows cannot be compared safely."""


def load_aggregator_baseline(
    db: Session,
    *,
    raw_root: str | Path,
    now: Callable[[], datetime] | None = None,
) -> AggregatorBaseline:
    """Load current aggregator rows with their latest approved snapshots."""
    checked_at = (now or (lambda: datetime.now(timezone.utc)))()
    if checked_at.tzinfo is None or checked_at.utcoffset() is None:
        raise AggregatorBaselineLoadError(
            "baseline check timestamp requires a timezone"
        )
    store = SnapshotManifestStore(raw_root)
    try:
        manifests = {
            source_id: store.latest(source_id)
            for source_id in AGGREGATOR_SOURCE_IDS
        }
    except SnapshotError as exc:
        raise AggregatorBaselineLoadError(str(exc)) from None
    missing = sorted(
        source_id
        for source_id, manifest in manifests.items()
        if manifest is None
    )
    if missing:
        raise AggregatorBaselineLoadError(
            "approved aggregator snapshot is missing: " + ",".join(missing)
        )

    policies = db.scalars(
        select(Policy)
        .where(
            Policy.source_id.in_(AGGREGATOR_SOURCE_IDS),
            Policy.data_quality_status != "invalid",
        )
        .order_by(Policy.source_id, Policy.external_id, Policy.id)
    ).all()
    if any(policy.external_id is None for policy in policies):
        raise AggregatorBaselineLoadError(
            "approved aggregator row has no external identity"
        )
    if any(
        _as_utc(policy.collected_at)
        > manifests[policy.source_id].completed_at.astimezone(timezone.utc)
        for policy in policies
    ):
        raise AggregatorBaselineLoadError(
            "PostgreSQL baseline is newer than its latest snapshot"
        )
    policy_ids = tuple(policy.id for policy in policies)
    rules_by_policy: dict[int, list[str]] = defaultdict(list)
    if policy_ids:
        rules = db.scalars(
            select(PolicyRegionRule)
            .where(
                PolicyRegionRule.policy_id.in_(policy_ids),
                PolicyRegionRule.relation == "include",
                PolicyRegionRule.resolution_status == "matched",
            )
            .order_by(
                PolicyRegionRule.policy_id,
                PolicyRegionRule.region_scheme,
                PolicyRegionRule.region_code,
            )
        ).all()
        for rule in rules:
            if rule.region_scheme is not None and rule.region_code is not None:
                rules_by_policy[rule.policy_id].append(
                    f"{rule.region_scheme}:{rule.region_code}"
                )

    records = tuple(
        BaselineRecord.from_mapping(
            {
                column.name: getattr(policy, column.name)
                for column in Policy.__table__.columns
            },
            canonical_region_keys=rules_by_policy[policy.id],
            database_row_id=policy.id,
        )
        for policy in policies
    )
    counts = {
        source_id: sum(
            record.identity.source_id == source_id for record in records
        )
        for source_id in AGGREGATOR_SOURCE_IDS
    }
    if any(count == 0 for count in counts.values()):
        raise AggregatorBaselineLoadError(
            "approved aggregator PostgreSQL baseline is incomplete"
        )
    descriptors = tuple(
        BaselineDescriptor(
            source_id=source_id,
            snapshot_id=manifests[source_id].snapshot_id,
            snapshot_collected_at=manifests[source_id].completed_at,
            snapshot_policy_count=manifests[source_id].item_count,
            database_checked_at=checked_at,
            database_policy_count=counts[source_id],
        )
        for source_id in sorted(AGGREGATOR_SOURCE_IDS)
    )
    try:
        return AggregatorBaseline(descriptors=descriptors, records=records)
    except CrossSourceDuplicateError as exc:
        raise AggregatorBaselineLoadError(str(exc)) from None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
