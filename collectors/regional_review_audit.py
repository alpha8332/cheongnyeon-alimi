"""Deterministic RYP7 review reason and evidence coverage audit."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any


AUDIT_SCHEMA_VERSION = "1.1.0"
REVIEW_SAMPLE_LIMIT = 20
REGIONAL_EVIDENCE_FIELDS = (
    "implementing_organization_text",
    "region_eligibility_text",
    "application_channel_text",
    "additional_benefit_text",
    "source_region_text",
    "application_period_text",
)
REVIEW_OUTCOME = "review"
FAILED_OUTCOME = "failed"
VALID_OUTCOMES = frozenset(
    {"accepted", "duplicate", REVIEW_OUTCOME, "closed", FAILED_OUTCOME}
)


class RegionalReviewAuditError(ValueError):
    """Stored decisions cannot produce an auditable RYP7 report."""


@dataclass(frozen=True, slots=True)
class RegionalReviewAuditInput:
    source_id: str
    checkpoint_complete: bool
    discovered_count: int
    captured_count: int
    checkpoint_outcomes: tuple[tuple[str, str], ...]
    regional_decisions: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        if (
            not self.source_id
            or not self.checkpoint_complete
            or self.discovered_count < 0
            or self.captured_count < 0
            or self.captured_count > self.discovered_count
        ):
            raise RegionalReviewAuditError("regional audit input is invalid")
        outcome_ids = [
            external_id for external_id, _ in self.checkpoint_outcomes
        ]
        if (
            len(outcome_ids) != self.discovered_count
            or len(outcome_ids) != len(set(outcome_ids))
            or any(
                outcome not in VALID_OUTCOMES
                for _, outcome in self.checkpoint_outcomes
            )
        ):
            raise RegionalReviewAuditError(
                "regional audit checkpoint outcomes are incomplete"
            )
        decision_ids: list[str] = []
        for decision in self.regional_decisions:
            external_id = decision.get("external_id")
            if not isinstance(external_id, str) or not external_id:
                raise RegionalReviewAuditError(
                    "regional audit decision identity is invalid"
                )
            decision_ids.append(external_id)
        expected_decision_ids = {
            external_id
            for external_id, outcome in self.checkpoint_outcomes
            if outcome != FAILED_OUTCOME
        }
        if (
            len(decision_ids) != len(set(decision_ids))
            or set(decision_ids) != expected_decision_ids
            or len(decision_ids) != self.captured_count
        ):
            raise RegionalReviewAuditError(
                "regional audit replay does not match checkpoint"
            )
        outcomes = dict(self.checkpoint_outcomes)
        for decision in self.regional_decisions:
            external_id = str(decision["external_id"])
            outcome = outcomes[external_id]
            accepted = decision.get("accepted")
            application = decision.get("application")
            if (
                not isinstance(accepted, bool)
                or (outcome == "accepted" and not accepted)
                or (outcome == REVIEW_OUTCOME and accepted)
                or (outcome == "closed" and application != "closed")
            ):
                raise RegionalReviewAuditError(
                    "regional audit replay outcome drifted from checkpoint"
                )


def build_regional_review_audit(
    inputs: Iterable[RegionalReviewAuditInput],
    *,
    audit_date: date,
) -> dict[str, Any]:
    """Build one stable report without treating null as confirmed absence."""

    selected = tuple(inputs)
    if not selected or len({value.source_id for value in selected}) != len(
        selected
    ):
        raise RegionalReviewAuditError(
            "regional audit requires unique Source inputs"
        )
    sources = tuple(
        _audit_source(value)
        for value in sorted(selected, key=lambda item: item.source_id)
    )
    totals = {
        "source_count": len(sources),
        "discovered": sum(
            value["checkpoint_counts"]["discovered"] for value in sources
        ),
        "captured": sum(
            value["checkpoint_counts"]["captured"] for value in sources
        ),
        **{
            outcome: sum(
                value["checkpoint_counts"][outcome] for value in sources
            )
            for outcome in sorted(VALID_OUTCOMES)
        },
    }
    totals["classified"] = sum(
        totals[outcome] for outcome in VALID_OUTCOMES
    )
    totals["classification_reconciled"] = (
        totals["classified"] == totals["discovered"]
    )
    totals["capture_evidence_gap_sources"] = sum(
        value["capture_evidence_gap"] for value in sources
    )
    totals["checkpoint_decision_drift"] = sum(
        value["checkpoint_decision_drift"]["total"] for value in sources
    )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_date": audit_date.isoformat(),
        "totals": totals,
        "sources": list(sources),
    }


def _audit_source(value: RegionalReviewAuditInput) -> dict[str, Any]:
    outcomes = dict(value.checkpoint_outcomes)
    outcome_counts = Counter(outcomes.values())
    decisions = {
        str(decision["external_id"]): decision
        for decision in value.regional_decisions
    }
    review_decisions = tuple(
        decisions[external_id]
        for external_id, outcome in value.checkpoint_outcomes
        if outcome == REVIEW_OUTCOME
    )
    reason_counts: Counter[str] = Counter()
    review_reason_counts: Counter[str] = Counter()
    combinations: Counter[str] = Counter()
    for decision in value.regional_decisions:
        reasons = _reason_codes(decision)
        reason_counts.update(reasons)
        if outcomes[str(decision["external_id"])] == REVIEW_OUTCOME:
            review_reason_counts.update(reasons)
            combinations["+".join(sorted(reasons))] += 1

    coverage: dict[str, dict[str, int]] = {}
    for field_name in REGIONAL_EVIDENCE_FIELDS:
        status_counts = Counter(
            {
                "present": 0,
                "source_value_absent": 0,
                "capture_contract_gap": 0,
                "null_unverifiable": 0,
            }
        )
        for decision in review_decisions:
            evidence = _evidence(decision)
            if evidence.get(field_name) is not None:
                status_counts["present"] += 1
                continue
            observations = evidence.get("field_observations")
            observed = (
                observations.get(field_name)
                if isinstance(observations, Mapping)
                else None
            )
            if observed == "label_present_value_empty":
                status_counts["source_value_absent"] += 1
            elif observed == "label_not_found":
                status_counts["capture_contract_gap"] += 1
            else:
                status_counts["null_unverifiable"] += 1
        coverage[field_name] = dict(status_counts)
    source_scope_attached = sum(
        _evidence(decision).get("source_scope") is not None
        for decision in review_decisions
    )
    capture_gap = any(
        coverage[field_name]["null_unverifiable"] > 0
        or coverage[field_name]["capture_contract_gap"] > 0
        for field_name in (
            "implementing_organization_text",
            "region_eligibility_text",
            "source_region_text",
            "application_period_text",
        )
    )
    duplicate_now_unaccepted = sum(
        outcomes[str(decision["external_id"])] == "duplicate"
        and not bool(decision.get("accepted"))
        for decision in value.regional_decisions
    )
    return {
        "source_id": value.source_id,
        "checkpoint_counts": {
            "discovered": value.discovered_count,
            "captured": value.captured_count,
            **{
                outcome: outcome_counts[outcome]
                for outcome in sorted(VALID_OUTCOMES)
            },
        },
        "reason_counts": dict(sorted(reason_counts.items())),
        "review_reason_counts": dict(sorted(review_reason_counts.items())),
        "review_reason_samples": _review_reason_samples(review_decisions),
        "review_reason_combinations": dict(sorted(combinations.items())),
        "review_evidence_coverage": coverage,
        "source_scope_attached_review_count": source_scope_attached,
        "checkpoint_decision_drift": {
            "duplicate_now_unaccepted": duplicate_now_unaccepted,
            "total": duplicate_now_unaccepted,
        },
        "review_routes": {
            "regional_evidence": _reason_route(
                review_decisions, {"insufficient_regional_evidence"}
            ),
            "application_state": _reason_route(
                review_decisions,
                {
                    "application_period_missing",
                    "application_period_unresolved",
                    "application_period_invalid",
                    "budget_exhaustion_state_unknown",
                },
            ),
            "youth_target": _reason_route(
                review_decisions, {"youth_target_unconfirmed"}
            ),
            "capture_failure": outcome_counts[FAILED_OUTCOME],
        },
        "capture_evidence_gap": capture_gap,
        "capture_evidence_note": (
            "one or more null fields are either legacy-unverifiable or "
            "explicit capture-contract gaps; only label_present_value_empty "
            "is treated as source value absence"
            if capture_gap
            else None
        ),
    }


def _reason_codes(decision: Mapping[str, Any]) -> tuple[str, ...]:
    values = decision.get("reason_codes")
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(value, str) and value for value in values)
    ):
        raise RegionalReviewAuditError(
            "regional audit decision reasons are invalid"
        )
    return tuple(values)


def _review_reason_samples(
    decisions: Iterable[Mapping[str, Any]],
) -> dict[str, list[str]]:
    """Return stable, identity-only samples without copying Raw text."""

    samples: dict[str, list[str]] = {}
    ordered = sorted(decisions, key=lambda item: str(item["external_id"]))
    for decision in ordered:
        external_id = str(decision["external_id"])
        for reason in sorted(_reason_codes(decision)):
            selected = samples.setdefault(reason, [])
            if len(selected) < REVIEW_SAMPLE_LIMIT:
                selected.append(external_id)
    return dict(sorted(samples.items()))


def _evidence(decision: Mapping[str, Any]) -> Mapping[str, Any]:
    value = decision.get("evidence")
    if not isinstance(value, Mapping):
        raise RegionalReviewAuditError(
            "regional audit decision evidence is invalid"
        )
    return value


def _reason_route(
    decisions: Iterable[Mapping[str, Any]],
    reasons: set[str],
) -> int:
    return sum(
        bool(set(_reason_codes(decision)) & reasons)
        for decision in decisions
    )
