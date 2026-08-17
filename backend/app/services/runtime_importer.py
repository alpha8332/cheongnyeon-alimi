from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.services.seed_importer import ImportResult, import_programs
from app.services.aggregator_baseline import load_aggregator_baseline
from collectors.cross_source_duplicate import (
    CrossSourceDecisionManifestStore,
)
from collectors.runtime import RuntimeReplayResult, replay_runtime_raw
from collectors.regional_expansion import EXPANDED_CAPTURE_SOURCE_IDS
from collectors.supplemental_official import SUPPLEMENTAL_SOURCE_IDS
from collectors.regional_expansion import (
    RegionalBatchCheckpoint,
    RegionalCheckpointStore,
    RegionalOutcome,
    outcome_from_decisions,
)


REGIONAL_DUPLICATE_SOURCE_IDS = frozenset(
    {
        "regional-gyeongbuk-youth-platform",
        "regional-busan-youth-platform",
        "regional-seoul-youth-platform",
        *EXPANDED_CAPTURE_SOURCE_IDS,
    }
)
DUPLICATE_GATE_SOURCE_IDS = frozenset(
    {*REGIONAL_DUPLICATE_SOURCE_IDS, *SUPPLEMENTAL_SOURCE_IDS}
)


@dataclass(frozen=True)
class RuntimeImportResult:
    replay: RuntimeReplayResult
    database: ImportResult
    decision_manifest_id: str | None = None
    pruned: int = 0


def import_runtime_raw(
    db: Session,
    *,
    raw_root: str | Path,
    source_id: str,
    limit: int,
    snapshot_id: str | None = None,
    dry_run: bool = False,
    decision_root: str | Path | None = None,
    checkpoint_root: str | Path | None = None,
    regional_redecision_audit: Mapping[str, Any] | None = None,
) -> RuntimeImportResult:
    """Replay one source batch and pass accepted programs to the importer."""
    replay = replay_runtime_raw(
        raw_root=raw_root,
        source_id=source_id,
        limit=limit,
        snapshot_id=snapshot_id,
        checkpoint_root=checkpoint_root,
    )
    if source_id in DUPLICATE_GATE_SOURCE_IDS and replay.duplicate_decisions:
        baseline = load_aggregator_baseline(db, raw_root=raw_root)
        # SQLAlchemy autobegins a transaction for the read-only baseline query.
        # End it before seed_importer opens the isolated write transaction.
        if db.in_transaction():
            db.rollback()
        replay = replay_runtime_raw(
            raw_root=raw_root,
            source_id=source_id,
            limit=limit,
            snapshot_id=snapshot_id,
            duplicate_baseline=baseline,
            checkpoint_root=checkpoint_root,
        )
    decision_manifest_id = None
    if replay.duplicate_manifest is not None and decision_root is not None:
        CrossSourceDecisionManifestStore(decision_root).save(
            replay.duplicate_manifest
        )
        decision_manifest_id = replay.duplicate_manifest.manifest_id
    normalization_issues = replay.normalization_issues or tuple(
        () for _ in replay.programs
    )
    if len(normalization_issues) != len(replay.programs):
        raise ValueError(
            "runtime normalization issues must align with programs"
        )
    database = import_programs(
        db,
        replay.programs,
        dry_run=dry_run,
        normalization_issues=normalization_issues,
    )
    pruned = 0
    if checkpoint_root is not None and source_id in REGIONAL_DUPLICATE_SOURCE_IDS:
        checkpoint = _finalize_regional_checkpoint(
            replay,
            checkpoint_root=checkpoint_root,
            redecision_audit=regional_redecision_audit,
            persist=not dry_run,
        )
        if not dry_run:
            accepted_ids = {
                external_id
                for external_id, outcome in checkpoint.decisions
                if outcome is RegionalOutcome.ACCEPTED
            }
            pruned = _prune_regional_policies(
                db,
                source_id=source_id,
                accepted_ids=accepted_ids,
            )
    return RuntimeImportResult(
        replay=replay,
        database=database,
        decision_manifest_id=decision_manifest_id,
        pruned=pruned,
    )


def _prune_regional_policies(
    db: Session, *, source_id: str, accepted_ids: set[str]
) -> int:
    """Make a completed regional Source projection match accepted decisions."""

    statement = delete(Policy).where(Policy.source_id == source_id)
    if accepted_ids:
        statement = statement.where(
            or_(
                Policy.external_id.is_(None),
                Policy.external_id.not_in(accepted_ids),
            )
        )
    try:
        result = db.execute(statement)
        pruned = result.rowcount or 0
        db.commit()
    except Exception:
        db.rollback()
        raise
    return pruned


def _finalize_regional_checkpoint(
    replay: RuntimeReplayResult,
    *,
    checkpoint_root: str | Path,
    redecision_audit: Mapping[str, Any] | None = None,
    persist: bool = True,
) -> RegionalBatchCheckpoint:
    store = RegionalCheckpointStore(checkpoint_root)
    checkpoint = store.load(replay.source_id)
    if checkpoint is None or not checkpoint.discovery_complete:
        raise ValueError("regional checkpoint discovery is incomplete")
    duplicate_by_external_id = {
        decision["candidate"]["external_id"]: decision
        for decision in replay.duplicate_decisions
    }
    outcomes: dict[str, RegionalOutcome] = {
        external_id: outcome
        for external_id, outcome in checkpoint.decisions
    }
    for decision in replay.regional_decisions:
        external_id = decision["external_id"]
        if outcomes.get(external_id) is RegionalOutcome.FAILED:
            continue
        outcomes[external_id] = outcome_from_decisions(
            decision,
            duplicate_by_external_id.get(external_id),
        )
    missing = set(checkpoint.captured_ids) - set(outcomes)
    for external_id in missing:
        outcomes[external_id] = RegionalOutcome.FAILED
    existing = dict(checkpoint.decisions)
    drifted = any(
        external_id in outcomes and outcomes[external_id] != outcome
        for external_id, outcome in existing.items()
    )
    if drifted and not _matches_redecision_audit(
        replay.source_id,
        existing,
        outcomes,
        redecision_audit,
    ):
        raise ValueError("regional checkpoint decisions drifted")
    pending = {
        external_id: outcome
        for external_id, outcome in outcomes.items()
        if external_id not in existing
    }
    finalized = (
        checkpoint.redecide(outcomes)
        if drifted
        else checkpoint if not pending else checkpoint.decide(pending)
    )
    if not finalized.complete:
        raise ValueError("regional checkpoint decision set is incomplete")
    if persist:
        store.save(finalized)
    return finalized


def _matches_redecision_audit(
    source_id: str,
    existing: Mapping[str, RegionalOutcome],
    outcomes: Mapping[str, RegionalOutcome],
    audit: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(audit, Mapping) or audit.get("ready_for_redecision") is not True:
        return False
    sources = audit.get("sources")
    if not isinstance(sources, list):
        return False
    source = next(
        (
            value
            for value in sources
            if isinstance(value, Mapping) and value.get("source_id") == source_id
        ),
        None,
    )
    if source is None:
        return False
    expected = {
        (
            str(item.get("external_id")),
            str(item.get("from")),
            str(item.get("to")),
        )
        for item in source.get("transitions", ())
        if isinstance(item, Mapping)
    }
    actual = {
        (external_id, old.value, outcomes[external_id].value)
        for external_id, old in existing.items()
        if outcomes.get(external_id) != old
    }
    return (
        bool(actual)
        and actual == expected
        and source.get("transition_scope_valid") is True
        and source.get("closed_evidence_complete") is True
        and source.get("existing_accepted_preserved") is True
        and source.get("failed_identity_preserved") is True
        and source.get("promotion_evidence_complete") is True
    )
