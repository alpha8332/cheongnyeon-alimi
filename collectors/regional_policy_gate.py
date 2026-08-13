"""Source-backed regionality and current-application gate."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date, timedelta, timezone
from enum import Enum
from functools import lru_cache

from collectors.extracted import (
    ExtractedCoverageScope,
    ExtractedPolicy,
    ExtractedRegionRelation,
    SourceProvenance,
    SourceRegionEvidence,
)
from collectors.regions import (
    RegionReference,
    RegionResolutionStatus,
    default_region_reference,
)


KOREA_TIMEZONE = timezone(timedelta(hours=9))
_DATE_TOKEN = re.compile(
    r"(?<!\d)(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})(?:일)?"
)
_EVIDENCE_FIELDS = frozenset(
    {
        "implementing_organization_text",
        "region_eligibility_text",
        "application_channel_text",
        "additional_benefit_text",
        "source_region_text",
        "application_period_text",
    }
)
_SOURCE_SCOPE_FIELDS = frozenset(
    {
        "jurisdiction_text",
        "operator_text",
        "youth_policy_scope_text",
        "application_scope_text",
    }
)
_YOUTH_MARKERS = ("청년", "청소년", "대학생")
_FIELD_OBSERVATION_STATUSES = frozenset(
    {
        "value_extracted",
        "label_present_value_empty",
        "label_not_found",
    }
)


class RegionalityStatus(str, Enum):
    REGIONAL_CONFIRMED = "regional_confirmed"
    REGIONAL_REVIEW_REQUIRED = "regional_review_required"
    NON_REGIONAL = "non_regional"


class ApplicationAvailability(str, Enum):
    OPEN = "open"
    SCHEDULED = "scheduled"
    CLOSED = "closed"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True, slots=True)
class RegionalSourceScopeEvidence:
    """Approved list-scope evidence; never sufficient without item evidence."""

    jurisdiction_text: str
    operator_text: str
    youth_policy_scope_text: str | None
    application_scope_text: str | None
    field_locators: tuple[tuple[str, str], ...]
    provenance: tuple[SourceProvenance, ...]

    def __post_init__(self) -> None:
        if self.jurisdiction_text is None or self.operator_text is None:
            raise ValueError(
                "regional Source scope requires jurisdiction and operator"
            )
        for field_name in _SOURCE_SCOPE_FIELDS:
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be normalized text or null"
                )
        locator_names = [name for name, _ in self.field_locators]
        if (
            len(locator_names) != len(set(locator_names))
            or any(name not in _SOURCE_SCOPE_FIELDS for name in locator_names)
            or any(
                not isinstance(locator, str)
                or not locator
                or locator != locator.strip()
                for _, locator in self.field_locators
            )
        ):
            raise ValueError("regional Source scope locators are invalid")
        populated = {
            field_name
            for field_name in _SOURCE_SCOPE_FIELDS
            if getattr(self, field_name) is not None
        }
        if populated != set(locator_names):
            raise ValueError(
                "each regional Source scope value requires one locator"
            )
        if not self.provenance or not any(
            value.document_role.value == "list_response"
            for value in self.provenance
        ):
            raise ValueError(
                "regional Source scope requires list_response provenance"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            field_name: getattr(self, field_name)
            for field_name in sorted(_SOURCE_SCOPE_FIELDS)
        } | {
            "field_locators": dict(self.field_locators),
            "provenance": [item.to_dict() for item in self.provenance],
        }


@dataclass(frozen=True, slots=True)
class RegionalPolicyEvidence:
    implementing_organization_text: str | None
    region_eligibility_text: str | None
    application_channel_text: str | None
    additional_benefit_text: str | None
    source_region_text: str | None
    application_period_text: str | None
    field_locators: tuple[tuple[str, str], ...]
    provenance: tuple[SourceProvenance, ...]
    source_scope: RegionalSourceScopeEvidence | None = None
    field_observations: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for field_name in _EVIDENCE_FIELDS:
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be normalized text or null"
                )
        locator_names = [name for name, _ in self.field_locators]
        if (
            len(locator_names) != len(set(locator_names))
            or any(name not in _EVIDENCE_FIELDS for name in locator_names)
            or any(
                not isinstance(locator, str)
                or not locator
                or locator != locator.strip()
                for _, locator in self.field_locators
            )
        ):
            raise ValueError("regional evidence locators are invalid")
        populated = {
            field_name
            for field_name in _EVIDENCE_FIELDS
            if getattr(self, field_name) is not None
        }
        if populated != set(locator_names):
            raise ValueError(
                "each regional evidence value requires one locator"
            )
        if not self.provenance:
            raise ValueError("regional evidence requires provenance")
        if self.source_scope is not None:
            if not isinstance(self.source_scope, RegionalSourceScopeEvidence):
                raise ValueError("regional Source scope evidence is invalid")
            policy_raw_ids = {
                value.raw_document_id for value in self.provenance
            }
            scope_raw_ids = {
                value.raw_document_id
                for value in self.source_scope.provenance
            }
            if not scope_raw_ids.issubset(policy_raw_ids):
                raise ValueError(
                    "regional Source scope provenance must belong to policy"
                )
        observation_names = [name for name, _ in self.field_observations]
        if (
            len(observation_names) != len(set(observation_names))
            or any(name not in _EVIDENCE_FIELDS for name in observation_names)
            or any(
                status not in _FIELD_OBSERVATION_STATUSES
                for _, status in self.field_observations
            )
        ):
            raise ValueError("regional field observations are invalid")
        for field_name, status in self.field_observations:
            value = getattr(self, field_name)
            if (status == "value_extracted") != (value is not None):
                raise ValueError(
                    "regional field observation does not match its value"
                )

    def to_dict(self) -> dict[str, object]:
        return {
            field_name: getattr(self, field_name)
            for field_name in sorted(_EVIDENCE_FIELDS)
        } | {
            "field_locators": dict(self.field_locators),
            "provenance": [item.to_dict() for item in self.provenance],
            "source_scope": (
                self.source_scope.to_dict()
                if self.source_scope is not None
                else None
            ),
            "field_observations": dict(self.field_observations),
        }


@dataclass(frozen=True, slots=True)
class RegionalPolicyDecision:
    source_id: str
    external_id: str
    regionality: RegionalityStatus
    application: ApplicationAvailability
    reason_codes: tuple[str, ...]
    evidence: RegionalPolicyEvidence
    accepted_policy: ExtractedPolicy | None

    def __post_init__(self) -> None:
        accepted = (
            self.regionality is RegionalityStatus.REGIONAL_CONFIRMED
            and self.application is ApplicationAvailability.OPEN
        )
        if accepted != (self.accepted_policy is not None):
            raise ValueError("regional decision acceptance is inconsistent")
        if not self.reason_codes or len(self.reason_codes) != len(
            set(self.reason_codes)
        ):
            raise ValueError("regional decision requires unique reasons")

    @property
    def accepted(self) -> bool:
        return self.accepted_policy is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "external_id": self.external_id,
            "regionality": self.regionality.value,
            "application": self.application.value,
            "accepted": self.accepted,
            "reason_codes": list(self.reason_codes),
            "evidence": self.evidence.to_dict(),
        }


def evaluate_regional_policy(
    policy: ExtractedPolicy,
    evidence: RegionalPolicyEvidence,
    *,
    expected_region_text: str,
    as_of: date | None = None,
    region_reference: RegionReference | None = None,
) -> RegionalPolicyDecision:
    """Classify one policy without inferring region from its portal."""
    if evidence.provenance != policy.provenance:
        raise ValueError("regional evidence provenance must match the policy")
    reference = region_reference or default_region_reference()
    (
        expected_region_full_name,
        territorial_codes,
        aliases,
    ) = _regional_context(reference, expected_region_text)

    canonical_region_text = expected_region_full_name
    source_region = evidence.source_region_text
    if source_region is not None:
        source_resolution = reference.resolve_alias(source_region)
        if (
            source_resolution.status is RegionResolutionStatus.MATCHED
            and source_resolution.candidates[0].code in territorial_codes
        ):
            canonical_region_text = source_resolution.candidates[0].full_name

    regionality, regional_reasons = _regionality(
        evidence,
        territorial_codes=territorial_codes,
        expected_aliases=aliases,
        reference=reference,
    )
    application, application_reason = _application_availability(
        evidence.application_period_text,
        as_of=(
            as_of
            if as_of is not None
            else policy.collected_at.astimezone(KOREA_TIMEZONE).date()
        ),
        source_scope=evidence.source_scope,
    )
    accepted_policy = None
    if (
        regionality is RegionalityStatus.REGIONAL_CONFIRMED
        and application is ApplicationAvailability.OPEN
    ):
        accepted_policy = replace(
            policy,
            region_text=policy.region_text or canonical_region_text,
            coverage_scope_hint=ExtractedCoverageScope.REGIONAL,
            region_evidence=(
                SourceRegionEvidence(
                    relation=ExtractedRegionRelation.INCLUDE,
                    external_scheme=None,
                    source_code=None,
                    source_text=canonical_region_text,
                ),
            ),
        )
    return RegionalPolicyDecision(
        source_id=policy.source_id,
        external_id=policy.external_id,
        regionality=regionality,
        application=application,
        reason_codes=(*regional_reasons, application_reason),
        evidence=evidence,
        accepted_policy=accepted_policy,
    )


@lru_cache(maxsize=32)
def _regional_context(
    reference: RegionReference,
    expected_region_text: str,
) -> tuple[str, frozenset[str], frozenset[str]]:
    expected = reference.resolve_alias(expected_region_text)
    if expected.status is not RegionResolutionStatus.MATCHED:
        raise ValueError("expected regional jurisdiction is not canonical")
    expected_region = expected.candidates[0]
    territorial_codes = {
        region.code
        for region in reference.regions
        if region.code == expected_region.code
        or any(
            ancestor.code == expected_region.code
            for ancestor in reference.ancestors(region.code)
        )
    }
    aliases = frozenset(
        {
            alias.alias
            for alias in reference.aliases
            if alias.region_code in territorial_codes
            and (
                resolution := reference.resolve_alias(alias.alias)
            ).status is RegionResolutionStatus.MATCHED
            and resolution.candidates[0].code in territorial_codes
        }
        | {expected_region.name, expected_region.full_name}
    )
    return (
        expected_region.full_name,
        frozenset(territorial_codes),
        aliases,
    )


def _regionality(
    evidence: RegionalPolicyEvidence,
    *,
    territorial_codes: frozenset[str],
    expected_aliases: frozenset[str],
    reference: RegionReference,
) -> tuple[RegionalityStatus, tuple[str, ...]]:
    source_region = evidence.source_region_text
    eligibility = evidence.region_eligibility_text
    implementing = evidence.implementing_organization_text
    expected_in_region = _mentions_any(source_region, expected_aliases)
    expected_in_target = _mentions_any(eligibility, expected_aliases)
    expected_in_organization = _mentions_any(implementing, expected_aliases)
    source_scope = evidence.source_scope

    if _is_nationwide(source_region) or _is_nationwide(eligibility):
        return (
            RegionalityStatus.NON_REGIONAL,
            ("nationwide_republication",),
        )
    if source_region is not None:
        resolution = reference.resolve_alias(source_region)
        if (
            resolution.status is RegionResolutionStatus.MATCHED
            and resolution.candidates[0].code not in territorial_codes
        ):
            return (
                RegionalityStatus.NON_REGIONAL,
                ("other_region_policy",),
            )
    if (
        expected_in_region
        and expected_in_target
        and expected_in_organization
    ):
        return (
            RegionalityStatus.REGIONAL_CONFIRMED,
            (
                "source_region_confirmed",
                "target_region_confirmed",
                "implementing_region_confirmed",
            ),
        )
    if source_scope is not None:
        scoped_region = _mentions_any(
            source_scope.jurisdiction_text, expected_aliases
        )
        scoped_operator = _mentions_any(
            source_scope.operator_text, expected_aliases
        )
        if scoped_region and scoped_operator and (
            expected_in_target or expected_in_organization
        ):
            return (
                RegionalityStatus.REGIONAL_CONFIRMED,
                tuple(
                    reason
                    for confirmed, reason in (
                        (scoped_region, "source_scope_region_confirmed"),
                        (scoped_operator, "source_scope_operator_confirmed"),
                        (expected_in_target, "target_region_confirmed"),
                        (
                            expected_in_organization,
                            "implementing_region_confirmed",
                        ),
                    )
                    if confirmed
                ),
            )
    return (
        RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
        ("insufficient_regional_evidence",),
    )


def _application_availability(
    value: str | None,
    *,
    as_of: date,
    source_scope: RegionalSourceScopeEvidence | None = None,
) -> tuple[ApplicationAvailability, str]:
    if value is None:
        if _scope_confirms_current_application(source_scope):
            return (
                ApplicationAvailability.OPEN,
                "source_scope_application_open",
            )
        return (
            ApplicationAvailability.REVIEW_REQUIRED,
            "application_period_missing",
        )
    normalized = " ".join(value.split())
    closed_markers = ("마감", "접수 종료", "신청 종료")
    if any(marker in normalized for marker in closed_markers):
        return ApplicationAvailability.CLOSED, "application_explicitly_closed"
    if "상시" in normalized:
        return ApplicationAvailability.OPEN, "application_always_open"
    if "예산" in normalized and "소진" in normalized:
        if any(marker in normalized for marker in ("접수중", "모집중")):
            return ApplicationAvailability.OPEN, "application_open_until_budget"
        return (
            ApplicationAvailability.REVIEW_REQUIRED,
            "budget_exhaustion_state_unknown",
        )

    dates: list[date] = []
    try:
        for year, month, day in _DATE_TOKEN.findall(normalized):
            dates.append(date(int(year), int(month), int(day)))
    except ValueError:
        return (
            ApplicationAvailability.REVIEW_REQUIRED,
            "application_period_invalid",
        )
    if len(dates) >= 2:
        start, end = dates[:2]
        if start > end:
            return (
                ApplicationAvailability.REVIEW_REQUIRED,
                "application_period_invalid",
            )
        if as_of < start:
            return ApplicationAvailability.SCHEDULED, "application_not_started"
        if as_of > end:
            return ApplicationAvailability.CLOSED, "application_period_ended"
        return ApplicationAvailability.OPEN, "application_period_open"
    if any(marker in normalized for marker in ("접수중", "모집중", "신청 가능")):
        return ApplicationAvailability.OPEN, "application_explicitly_open"
    if _scope_confirms_current_application(source_scope):
        return (
            ApplicationAvailability.OPEN,
            "source_scope_application_open",
        )
    return (
        ApplicationAvailability.REVIEW_REQUIRED,
        "application_period_unresolved",
    )


def _mentions_any(value: str | None, aliases: frozenset[str]) -> bool:
    return value is not None and any(alias in value for alias in aliases)


def _is_nationwide(value: str | None) -> bool:
    return value is not None and "전국" in value


def enforce_youth_target(
    policy: ExtractedPolicy,
    decision: RegionalPolicyDecision,
) -> RegionalPolicyDecision:
    """Require item evidence even when an approved youth list scope exists."""

    values = (
        policy.title,
        policy.eligibility_text,
        policy.age_text,
        policy.category_text,
    )
    policy_text = " ".join(value for value in values if value is not None)
    reason = None
    if any(marker in policy_text for marker in _YOUTH_MARKERS):
        reason = "youth_target_confirmed"
    else:
        scope = decision.evidence.source_scope
        if (
            scope is not None
            and scope.youth_policy_scope_text is not None
            and any(
                marker in scope.youth_policy_scope_text
                for marker in _YOUTH_MARKERS
            )
            and policy.age_text is not None
            and bool(
                re.search(r"(?<!\d)\d{1,3}\s*세(?!\w)", policy.age_text)
            )
        ):
            reason = "youth_target_confirmed_by_scope_and_age"
    if reason is not None:
        if reason in decision.reason_codes:
            return decision
        return replace(
            decision,
            reason_codes=(*decision.reason_codes, reason),
        )

    reasons = (
        decision.reason_codes
        if "youth_target_unconfirmed" in decision.reason_codes
        else (*decision.reason_codes, "youth_target_unconfirmed")
    )
    return replace(
        decision,
        regionality=(
            RegionalityStatus.REGIONAL_REVIEW_REQUIRED
            if decision.accepted
            else decision.regionality
        ),
        reason_codes=reasons,
        accepted_policy=None,
    )


def _scope_confirms_current_application(
    source_scope: RegionalSourceScopeEvidence | None,
) -> bool:
    if source_scope is None or source_scope.application_scope_text is None:
        return False
    normalized = " ".join(source_scope.application_scope_text.split())
    return any(
        marker in normalized
        for marker in ("접수중", "모집중", "신청 가능", "현재 신청 가능")
    )
