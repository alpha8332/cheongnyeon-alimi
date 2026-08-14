"""Deterministic audit for an explicit RYP9 checkpoint redecision."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

from collectors.regional_expansion import outcome_from_decisions


AUDIT_SCHEMA_VERSION = "1.0.0"
PROVENANCE_ROLES = {"list_response", "list_item", "detail_response"}
ALLOWED_TRANSITIONS = {
    ("review", "closed"),
    ("duplicate", "review"),
    ("review", "accepted"),
    ("review", "duplicate"),
}


class RegionalRyp9AuditError(ValueError):
    """Stored RYP9 evidence cannot produce a redecision audit."""


def build_regional_ryp9_audit(
    *,
    checkpoints: Mapping[str, Mapping[str, Any]],
    replays: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare completed checkpoints with current deterministic replay."""

    if set(checkpoints) != set(replays):
        raise RegionalRyp9AuditError("RYP9 Source sets do not match")
    old_totals: Counter[str] = Counter()
    proposed_totals: Counter[str] = Counter()
    transition_totals: Counter[str] = Counter()
    sources = []
    existing_accepted_preserved = True
    failed_preserved = True
    closed_evidence_complete = True
    promotion_evidence_complete = True
    transition_scope_valid = True

    for source_id in sorted(checkpoints):
        source = _source_audit(
            source_id,
            checkpoints[source_id],
            replays[source_id],
        )
        sources.append(source)
        old_totals.update(source["old_counts"])
        proposed_totals.update(source["proposed_counts"])
        transition_totals.update(source["transition_counts"])
        existing_accepted_preserved &= source["existing_accepted_preserved"]
        failed_preserved &= source["failed_identity_preserved"]
        closed_evidence_complete &= source["closed_evidence_complete"]
        promotion_evidence_complete &= source["promotion_evidence_complete"]
        transition_scope_valid &= source["transition_scope_valid"]

    counts_reconciled = sum(proposed_totals.values()) == sum(old_totals.values())
    criteria = {
        "source_sets_match": True,
        "counts_reconciled": counts_reconciled,
        "existing_accepted_preserved": existing_accepted_preserved,
        "failed_identity_preserved": failed_preserved,
        "closed_evidence_complete": closed_evidence_complete,
        "promotion_evidence_complete": promotion_evidence_complete,
        "transition_scope_valid": transition_scope_valid,
    }
    blockers = [name for name, value in criteria.items() if not value]
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "source_count": len(sources),
        "old_outcomes": dict(sorted(old_totals.items())),
        "proposed_outcomes": dict(sorted(proposed_totals.items())),
        "transition_counts": dict(sorted(transition_totals.items())),
        "transition_count": sum(transition_totals.values()),
        "sources": sources,
        "criteria": criteria,
        "ready_for_redecision": not blockers,
        "blockers": blockers,
    }


def _source_audit(
    source_id: str,
    checkpoint: Mapping[str, Any],
    replay: Mapping[str, Any],
) -> dict[str, Any]:
    decisions = checkpoint.get("decisions")
    regional = replay.get("regional_decisions")
    duplicate = replay.get("duplicate_decisions")
    if not isinstance(decisions, list) or not isinstance(regional, list):
        raise RegionalRyp9AuditError("RYP9 checkpoint or replay is invalid")
    if not isinstance(duplicate, list):
        raise RegionalRyp9AuditError("RYP9 duplicate replay is invalid")
    old = {
        str(item["external_id"]): str(item["outcome"])
        for item in decisions
        if isinstance(item, Mapping)
    }
    if len(old) != len(decisions):
        raise RegionalRyp9AuditError("RYP9 checkpoint decisions are invalid")
    duplicate_by_id = {
        str(item["candidate"]["external_id"]): item
        for item in duplicate
        if isinstance(item, Mapping) and isinstance(item.get("candidate"), Mapping)
    }
    proposed = dict(old)
    regional_by_id = {}
    for item in regional:
        if not isinstance(item, Mapping) or not isinstance(item.get("external_id"), str):
            raise RegionalRyp9AuditError("RYP9 regional decision is invalid")
        external_id = item["external_id"]
        regional_by_id[external_id] = item
        if old.get(external_id) == "failed":
            continue
        proposed[external_id] = outcome_from_decisions(
            item,
            duplicate_by_id.get(external_id),
        ).value
    transitions = []
    for external_id, old_outcome in old.items():
        new_outcome = proposed.get(external_id)
        if new_outcome == old_outcome:
            continue
        regional_decision = regional_by_id.get(external_id, {})
        evidence = regional_decision.get("evidence")
        provenance = evidence.get("provenance") if isinstance(evidence, Mapping) else ()
        roles = {
            item.get("document_role")
            for item in provenance or ()
            if isinstance(item, Mapping)
        }
        reason_codes = regional_decision.get("reason_codes")
        reason_codes = reason_codes if isinstance(reason_codes, list) else []
        closed_evidence = new_outcome != "closed" or (
            bool(
                {"application_explicitly_closed", "application_period_ended"}
                & set(reason_codes)
            )
            and PROVENANCE_ROLES.issubset(roles)
        )
        duplicate_decision = duplicate_by_id.get(external_id)
        promotion_evidence = new_outcome not in {"accepted", "duplicate"} or (
            regional_decision.get("accepted") is True
            and PROVENANCE_ROLES.issubset(roles)
            and any(
                reason in reason_codes
                for reason in (
                    "source_region_confirmed",
                    "target_region_confirmed",
                    "implementing_region_confirmed",
                    "source_scope_region_confirmed",
                )
            )
            and any(reason.startswith("application_") for reason in reason_codes)
            and any(reason.startswith("youth_target_confirmed") for reason in reason_codes)
            and (
                new_outcome != "duplicate"
                or isinstance(duplicate_decision, Mapping)
                and duplicate_decision.get("accepted") is False
            )
        )
        transitions.append(
            {
                "external_id": external_id,
                "from": old_outcome,
                "to": new_outcome,
                "reason_codes": reason_codes,
                "closed_evidence_complete": closed_evidence,
                "promotion_evidence_complete": promotion_evidence,
            }
        )
    old_accepted = {key for key, value in old.items() if value == "accepted"}
    new_accepted = {key for key, value in proposed.items() if value == "accepted"}
    old_failed = {key for key, value in old.items() if value == "failed"}
    new_failed = {key for key, value in proposed.items() if value == "failed"}
    transition_counts = Counter(
        f"{item['from']}->{item['to']}" for item in transitions
    )
    return {
        "source_id": source_id,
        "old_counts": dict(sorted(Counter(old.values()).items())),
        "proposed_counts": dict(sorted(Counter(proposed.values()).items())),
        "transition_counts": dict(sorted(transition_counts.items())),
        "transitions": transitions,
        "existing_accepted_preserved": old_accepted.issubset(new_accepted),
        "failed_identity_preserved": old_failed == new_failed,
        "closed_evidence_complete": all(
            item["closed_evidence_complete"] for item in transitions
        ),
        "promotion_evidence_complete": all(
            item["promotion_evidence_complete"] for item in transitions
        ),
        "transition_scope_valid": all(
            (item["from"], item["to"]) in ALLOWED_TRANSITIONS
            for item in transitions
        ),
    }
