"""Versioned, side-effect-free admission rules for stored review candidates."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlsplit


RULE_VERSION = "review-admission-v1"
TAXONOMY_VERSION = "2.0.0"
AUDIT_SCHEMA_VERSION = "1.0.0"


def _character_tokens(value: str):
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return (character for character in normalized if character.isalnum())

YOUTH_TAXONOMY_GROUPS: dict[str, tuple[str, ...]] = {
    "direct": ("청년", "청소년", "대학생"),
    "family_parent": (
        "신혼부부",
        "예비신혼부부",
        "미혼모",
        "미혼부",
        "청소년부모",
    ),
    "care_independence": (
        "가족돌봄청년",
        "가족돌봄청소년",
        "영케어러",
        "자립준비청년",
        "보호종료아동",
    ),
    "vulnerable_transition": (
        "고립청년",
        "은둔청년",
        "학교밖청소년",
        "가정밖청소년",
        "쉼터퇴소청소년",
        "경계선지능청년",
        "장애청년",
        "저소득청년",
        "주거취약청년",
        "다문화청년",
        "탈북청년",
        "니트청년",
        "구직단념청년",
        "장기미취업청년",
        "전입청년",
        "지역정착청년",
    ),
    "employment_education": (
        "취업준비생",
        "구직자",
        "미취업자",
        "졸업생",
        "졸업예정자",
        "대학원생",
        "학자금",
        "장학생",
        "사회초년생",
        "신입사원",
    ),
    "household_business": (
        "1인가구",
        "예비창업자",
        "초기창업",
        "스타트업",
        "귀농",
        "후계농",
        "청년농업인",
        "청년창업자",
    ),
    "cohort_military": (
        "2030세대",
        "ROTC",
        "학군사관후보생",
        "사관후보생",
        "군복무",
        "전역자",
        "전역청년",
    ),
}

_NORMALIZED_TAXONOMY = tuple(
    (group, marker, "".join(_character_tokens(marker)))
    for group, markers in YOUTH_TAXONOMY_GROUPS.items()
    for marker in markers
)
_ITEM_REGION_REASONS = frozenset(
    {
        "source_region_confirmed",
        "target_region_confirmed",
        "implementing_region_confirmed",
    }
)
_REGION_BLOCKERS = frozenset(
    {
        "insufficient_regional_evidence",
        "nationwide_republication",
        "region_conflict",
        "ambiguous_parent_region",
    }
)
_OPEN_REASONS = frozenset(
    {
        "application_period_open",
        "application_explicitly_open",
        "source_scope_application_open",
    }
)
_HARD_EXCLUSION_OUTCOMES = frozenset(
    {"exclude_closed", "exclude_duplicate", "exclude_invalid", "exclude_failed"}
)


class AdmissionOutcome(str, Enum):
    PROMOTE_PARTIAL = "promote_partial"
    HOLD_REVIEW = "hold_review"
    EXCLUDE_CLOSED = "exclude_closed"
    EXCLUDE_DUPLICATE = "exclude_duplicate"
    EXCLUDE_INVALID = "exclude_invalid"
    EXCLUDE_FAILED = "exclude_failed"


@dataclass(frozen=True, slots=True)
class ReviewAdmissionCandidate:
    source_id: str
    external_id: str
    source_url: str | None
    provenance_ids: tuple[str, ...]
    checkpoint_outcome: str
    regionality: str
    application: str
    original_reason_codes: tuple[str, ...]
    item_texts: tuple[str, ...]
    normalization_status: str | None = None
    residual_unknown_codes: tuple[str, ...] = ()
    policy_fingerprint: str | None = None
    duplicate_outcome: str | None = None
    duplicate_reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewAdmissionDecision:
    source_id: str
    external_id: str
    checkpoint_outcome: str
    outcome: AdmissionOutcome
    admission_reason_codes: tuple[str, ...]
    original_reason_codes: tuple[str, ...]
    taxonomy_markers: tuple[str, ...]
    taxonomy_groups: tuple[str, ...]
    residual_unknown_codes: tuple[str, ...]
    provenance_ids: tuple[str, ...]
    policy_fingerprint: str | None
    duplicate_outcome: str | None
    duplicate_reason_codes: tuple[str, ...]

    @property
    def hard_excluded(self) -> bool:
        return self.outcome.value in _HARD_EXCLUSION_OUTCOMES

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "external_id": self.external_id,
            "checkpoint_outcome": self.checkpoint_outcome,
            "outcome": self.outcome.value,
            "admission_reason_codes": list(self.admission_reason_codes),
            "original_reason_codes": list(self.original_reason_codes),
            "taxonomy_version": TAXONOMY_VERSION,
            "taxonomy_markers": list(self.taxonomy_markers),
            "taxonomy_groups": list(self.taxonomy_groups),
            "residual_unknown_codes": list(self.residual_unknown_codes),
            "provenance_ids": list(self.provenance_ids),
            "policy_fingerprint": self.policy_fingerprint,
            "duplicate_outcome": self.duplicate_outcome,
            "duplicate_reason_codes": list(self.duplicate_reason_codes),
        }


def match_youth_taxonomy(values: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Return stable group/marker matches without treating 2030 as an age year."""

    normalized_values = tuple(
        "".join(_character_tokens(value)) for value in values if value
    )
    matches = {
        (group, marker)
        for group, marker, normalized_marker in _NORMALIZED_TAXONOMY
        if any(normalized_marker in value for value in normalized_values)
    }
    return tuple(sorted(matches))


def classify_review_candidate(
    candidate: ReviewAdmissionCandidate,
) -> ReviewAdmissionDecision:
    matches = match_youth_taxonomy(candidate.item_texts)
    markers = tuple(sorted({marker for _, marker in matches}))
    groups = tuple(sorted({group for group, _ in matches}))
    original = frozenset(candidate.original_reason_codes)

    outcome: AdmissionOutcome
    reasons: tuple[str, ...]
    if not _valid_identity(candidate):
        outcome = AdmissionOutcome.EXCLUDE_INVALID
        reasons = ("invalid_identity_url_or_provenance",)
    elif candidate.checkpoint_outcome == "failed":
        outcome = AdmissionOutcome.EXCLUDE_FAILED
        reasons = ("checkpoint_failed",)
    elif candidate.checkpoint_outcome == "closed" or candidate.application == "closed":
        outcome = AdmissionOutcome.EXCLUDE_CLOSED
        reasons = ("application_closed",)
    elif candidate.checkpoint_outcome == "duplicate":
        outcome = AdmissionOutcome.EXCLUDE_DUPLICATE
        reasons = ("checkpoint_duplicate",)
    elif candidate.checkpoint_outcome != "review":
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("checkpoint_not_review",)
    elif not markers and not any(
        reason.startswith("youth_target_confirmed") for reason in original
    ):
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("youth_target_unconfirmed",)
    elif original & _REGION_BLOCKERS or not original & _ITEM_REGION_REASONS:
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("regional_evidence_not_admissible",)
    elif candidate.application != "open" or not original & _OPEN_REASONS:
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("current_application_unconfirmed",)
    elif candidate.normalization_status == "invalid":
        outcome = AdmissionOutcome.EXCLUDE_INVALID
        reasons = ("normalized_program_invalid",)
    elif candidate.normalization_status != "partial":
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("partial_contract_not_satisfied",)
    elif candidate.policy_fingerprint is None:
        outcome = AdmissionOutcome.EXCLUDE_INVALID
        reasons = ("policy_fingerprint_missing",)
    elif candidate.duplicate_outcome in {
        "excluded_aggregator_duplicate",
        "excluded_intra_batch_duplicate",
    }:
        outcome = AdmissionOutcome.EXCLUDE_DUPLICATE
        reasons = ("duplicate_confirmed",)
    elif candidate.duplicate_outcome == "duplicate_review_required":
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("duplicate_review_required",)
    elif candidate.duplicate_outcome != "accepted_regional":
        outcome = AdmissionOutcome.HOLD_REVIEW
        reasons = ("duplicate_gate_unconfirmed",)
    else:
        outcome = AdmissionOutcome.PROMOTE_PARTIAL
        reasons = ("all_admission_conditions_satisfied",)

    return ReviewAdmissionDecision(
        source_id=candidate.source_id,
        external_id=candidate.external_id,
        checkpoint_outcome=candidate.checkpoint_outcome,
        outcome=outcome,
        admission_reason_codes=reasons,
        original_reason_codes=tuple(sorted(original)),
        taxonomy_markers=markers,
        taxonomy_groups=groups,
        residual_unknown_codes=tuple(sorted(set(candidate.residual_unknown_codes))),
        provenance_ids=tuple(sorted(set(candidate.provenance_ids))),
        policy_fingerprint=candidate.policy_fingerprint,
        duplicate_outcome=candidate.duplicate_outcome,
        duplicate_reason_codes=tuple(sorted(set(candidate.duplicate_reason_codes))),
    )


def policy_fingerprint(program: dict[str, Any]) -> str:
    payload = json.dumps(
        program,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def manifest_hash(value: dict[str, Any]) -> str:
    selected = dict(value)
    selected.pop("manifest_sha256", None)
    payload = json.dumps(
        selected,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _valid_identity(candidate: ReviewAdmissionCandidate) -> bool:
    if (
        not candidate.source_id
        or not candidate.external_id
        or not candidate.provenance_ids
        or candidate.source_url is None
    ):
        return False
    parsed = urlsplit(candidate.source_url)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
