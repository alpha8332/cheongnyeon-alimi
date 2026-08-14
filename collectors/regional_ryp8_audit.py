"""Deterministic RYP8 completion and closed-history audit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


AUDIT_SCHEMA_VERSION = "1.0.0"
CLOSED_HISTORY_SOURCE_IDS = (
    "regional-gyeongnam-youth-platform",
    "regional-jeju-youth-platform",
)
OUTCOMES = ("accepted", "duplicate", "review", "closed", "failed")
PROVENANCE_ROLES = {"list_response", "list_item", "detail_response"}


class RegionalRyp8AuditError(ValueError):
    """Stored RYP8 evidence cannot produce a completion audit."""


def build_regional_ryp8_audit(
    *,
    review_audit: Mapping[str, Any],
    checkpoints: Mapping[str, Mapping[str, Any]],
    closed_replays: Mapping[str, Sequence[Mapping[str, Any]]],
    expected_outcomes: Mapping[str, int],
    max_legacy_null_slots: int | None,
) -> dict[str, Any]:
    """Reconcile field states, closed history, failures, and outcome baseline."""

    totals = review_audit.get("totals")
    sources = review_audit.get("sources")
    if not isinstance(totals, Mapping) or not isinstance(sources, list):
        raise RegionalRyp8AuditError("regional review audit is invalid")
    if set(expected_outcomes) != set(OUTCOMES) or any(
        not isinstance(expected_outcomes[name], int)
        or isinstance(expected_outcomes[name], bool)
        or expected_outcomes[name] < 0
        for name in OUTCOMES
    ):
        raise RegionalRyp8AuditError("RYP8 expected outcomes are invalid")
    if (
        max_legacy_null_slots is not None
        and (
            not isinstance(max_legacy_null_slots, int)
            or isinstance(max_legacy_null_slots, bool)
            or max_legacy_null_slots < 0
        )
    ):
        raise RegionalRyp8AuditError("RYP8 legacy null target is invalid")

    field_states = [_source_field_states(source) for source in sources]
    source_ids = [source["source_id"] for source in field_states]
    approved_sources_complete = (
        len(source_ids) == len(set(source_ids))
        and set(source_ids) == set(checkpoints)
    )
    field_state_reconciled = all(
        source["field_slots"] == source["reconciled_slots"]
        for source in field_states
    )
    legacy_null_slots = sum(source["null_unverifiable"] for source in field_states)
    legacy_within_target = (
        None
        if max_legacy_null_slots is None
        else legacy_null_slots <= max_legacy_null_slots
    )

    closed_history = [
        _closed_history(
            source_id,
            checkpoints.get(source_id),
            closed_replays.get(source_id),
        )
        for source_id in CLOSED_HISTORY_SOURCE_IDS
    ]
    failures = _failure_classification(checkpoints)
    actual_outcomes = {name: _integer(totals.get(name), name) for name in OUTCOMES}
    outcome_unchanged = actual_outcomes == dict(expected_outcomes)

    criteria: dict[str, bool | None] = {
        "approved_sources_complete": approved_sources_complete,
        "field_states_reconciled": field_state_reconciled,
        "legacy_null_within_target": legacy_within_target,
        "detail_failures_classified": (
            failures["failed_count"] == failures["classified_count"]
        ),
        "closed_history_complete": all(
            source["complete"] for source in closed_history
        ),
        "checkpoint_outcomes_unchanged": outcome_unchanged,
    }
    blockers = [
        name for name, value in criteria.items() if value is not True
    ]
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "source_count": len(field_states),
        "outcomes": {
            "expected": dict(expected_outcomes),
            "actual": actual_outcomes,
        },
        "field_states": field_states,
        "legacy_null_slots": legacy_null_slots,
        "max_legacy_null_slots": max_legacy_null_slots,
        "closed_history": closed_history,
        "failure_classification": failures,
        "criteria": criteria,
        "data_ready": not blockers,
        "blockers": blockers,
    }


def _source_field_states(source: Mapping[str, Any]) -> dict[str, Any]:
    source_id = source.get("source_id")
    counts = source.get("checkpoint_counts")
    coverage = source.get("review_evidence_coverage")
    if (
        not isinstance(source_id, str)
        or not isinstance(counts, Mapping)
        or not isinstance(coverage, Mapping)
    ):
        raise RegionalRyp8AuditError("RYP8 Source field audit is invalid")
    review = _integer(counts.get("review"), "review")
    totals = {
        "value_extracted": 0,
        "label_present_value_empty": 0,
        "label_not_found": 0,
        "null_unverifiable": 0,
    }
    for field in coverage.values():
        if not isinstance(field, Mapping):
            raise RegionalRyp8AuditError("RYP8 field coverage is invalid")
        totals["value_extracted"] += _integer(field.get("present"), "present")
        totals["label_present_value_empty"] += _integer(
            field.get("source_value_absent"), "source_value_absent"
        )
        totals["label_not_found"] += _integer(
            field.get("capture_contract_gap"), "capture_contract_gap"
        )
        totals["null_unverifiable"] += _integer(
            field.get("null_unverifiable"), "null_unverifiable"
        )
    return {
        "source_id": source_id,
        "review": review,
        "field_slots": review * len(coverage),
        "reconciled_slots": sum(totals.values()),
        **totals,
    }


def _closed_history(
    source_id: str,
    checkpoint: Mapping[str, Any] | None,
    replay: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if not isinstance(checkpoint, Mapping) or replay is None:
        raise RegionalRyp8AuditError("RYP8 closed history input is missing")
    decisions = checkpoint.get("decisions")
    if not isinstance(decisions, list):
        raise RegionalRyp8AuditError("RYP8 checkpoint decisions are invalid")
    expected = {
        str(item["external_id"])
        for item in decisions
        if isinstance(item, Mapping) and item.get("outcome") == "closed"
    }
    all_replay_closed = {
        str(item.get("external_id"))
        for item in replay
        if item.get("application") == "closed"
    }
    replay_closed = all_replay_closed & expected
    provenance_complete = set()
    reason_counts = {"explicitly_closed": 0, "period_ended": 0}
    for item in replay:
        external_id = str(item.get("external_id"))
        if external_id not in expected:
            continue
        evidence = item.get("evidence")
        provenance = evidence.get("provenance") if isinstance(evidence, Mapping) else None
        roles = {
            value.get("document_role")
            for value in provenance or ()
            if isinstance(value, Mapping)
        }
        if PROVENANCE_ROLES.issubset(roles):
            provenance_complete.add(external_id)
        reasons = item.get("reason_codes")
        if isinstance(reasons, list):
            if "application_explicitly_closed" in reasons:
                reason_counts["explicitly_closed"] += 1
            if "application_period_ended" in reasons:
                reason_counts["period_ended"] += 1
    return {
        "source_id": source_id,
        "checkpoint_closed": len(expected),
        "replay_closed": len(replay_closed),
        "review_now_closed": len(all_replay_closed - expected),
        "provenance_complete": len(provenance_complete),
        "reason_counts": reason_counts,
        "complete": expected == replay_closed == provenance_complete,
    }


def _failure_classification(
    checkpoints: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    failed_count = 0
    classified = []
    unclassified = []
    for source_id, checkpoint in checkpoints.items():
        discovered = checkpoint.get("discovered_ids")
        decisions = checkpoint.get("decisions")
        if not isinstance(discovered, list) or not isinstance(decisions, list):
            raise RegionalRyp8AuditError("RYP8 checkpoint is invalid")
        positions = {str(external_id): index for index, external_id in enumerate(discovered)}
        for item in decisions:
            if not isinstance(item, Mapping) or item.get("outcome") != "failed":
                continue
            failed_count += 1
            external_id = str(item.get("external_id"))
            index = positions.get(external_id)
            if (
                source_id == "regional-gangwon-youth-platform"
                and index is not None
                and index >= 12
            ):
                classified.append(
                    {
                        "source_id": source_id,
                        "external_id": external_id,
                        "page": index // 12 + 1,
                        "classification": "detail_click_or_post_contract",
                    }
                )
            else:
                unclassified.append(
                    {"source_id": source_id, "external_id": external_id}
                )
    return {
        "failed_count": failed_count,
        "classified_count": len(classified),
        "unclassified_count": len(unclassified),
        "classification_basis": (
            "checkpoint discovery position plus the reproduced page-context failure"
        ),
        "individual_current_detail_state_verified": 0,
        "recommended_rotating_canary_count": 3,
        "categories": {
            "detail_click_or_post_contract": len(classified),
        },
        "unclassified": unclassified,
    }


def _integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RegionalRyp8AuditError(f"RYP8 {name} count is invalid")
    return value
