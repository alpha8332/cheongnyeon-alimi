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
class RegionalPolicyEvidence:
    implementing_organization_text: str | None
    region_eligibility_text: str | None
    application_channel_text: str | None
    additional_benefit_text: str | None
    source_region_text: str | None
    application_period_text: str | None
    field_locators: tuple[tuple[str, str], ...]
    provenance: tuple[SourceProvenance, ...]

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

    def to_dict(self) -> dict[str, object]:
        return {
            field_name: getattr(self, field_name)
            for field_name in sorted(_EVIDENCE_FIELDS)
        } | {
            "field_locators": dict(self.field_locators),
            "provenance": [item.to_dict() for item in self.provenance],
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
    return (
        RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
        ("insufficient_regional_evidence",),
    )


def _application_availability(
    value: str | None,
    *,
    as_of: date,
) -> tuple[ApplicationAvailability, str]:
    if value is None:
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
    return (
        ApplicationAvailability.REVIEW_REQUIRED,
        "application_period_unresolved",
    )


def _mentions_any(value: str | None, aliases: frozenset[str]) -> bool:
    return value is not None and any(alias in value for alias in aliases)


def _is_nationwide(value: str | None) -> bool:
    return value is not None and "전국" in value
