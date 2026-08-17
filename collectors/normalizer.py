"""Deterministic source-neutral normalization of extracted policies."""

from __future__ import annotations

import re
from calendar import monthrange
from collections.abc import Iterable
from datetime import date, timedelta, timezone
from html.parser import HTMLParser
from typing import Any

from collectors.extracted import (
    ExtractedCoverageScope,
    ExtractedPolicy,
    ExtractedRegionRelation,
)
from collectors.eligibility import empty_eligibility_summary
from collectors.eligibility_mapping import (
    ELIGIBILITY_SOURCE_IDS,
    map_eligibility,
)
from collectors.normalized import (
    ApplicationSchedule,
    ApplicationStatus,
    Category,
    CoverageScope,
    DataQualityStatus,
    NormalizedProgram,
    RegionRelation,
)
from collectors.regions import (
    RegionReference,
    RegionResolutionStatus,
    default_region_reference,
)
from collectors.validation import (
    NormalizedProgramValidator,
    ValidationIssue,
    ValidationPartition,
    ValidationResult,
    partition_validation_results,
)


KOREA_TIMEZONE = timezone(timedelta(hours=9))

_DATE_TOKEN = re.compile(
    r"(?<!\d)(?:"
    r"(\d{4})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{1,2})"
    r"|(\d{4})(\d{2})(\d{2})"
    r")(?!\d)"
)
_MONTH_RANGE = re.compile(
    r"(?<!\d)(\d{4})\s*[.\-/년]\s*(\d{1,2})(?:월|\.)?\s*~\s*"
    r"(\d{4})\s*[.\-/년]\s*(\d{1,2})(?:월|\.)?(?!\d)"
)
_SAME_YEAR_MONTH_RANGE = re.compile(
    r"(?<!\d)(\d{4})\s*[.\-/년]\s*(\d{1,2})(?:월|\.)?\s*~\s*"
    r"(\d{1,2})(?:월|\.)?(?!\d)"
)
_NUMBER = re.compile(r"(?<!\d)(\d{1,3})(?!\d)")
_RANGE_MARKER = re.compile(r"~|～|이상.*이하")
_REGION_CODES = re.compile(r"^\d{5}(?:\s*,\s*\d{5})*$")

_CATEGORY_MAP: dict[str, tuple[Category, ...]] = {
    "주거": (Category.HOUSING,),
    "금융": (Category.FINANCE,),
    "서민금융": (Category.FINANCE,),
    "금융·생활지원": (Category.FINANCE,),
    "복지": (Category.WELFARE,),
    "복지·문화": (Category.WELFARE,),
    "생활지원": (Category.WELFARE,),
    "신체건강": (Category.WELFARE,),
    "정신건강": (Category.WELFARE,),
    "문화·여가": (Category.WELFARE,),
    "안전·위기": (Category.WELFARE,),
    "보육": (Category.WELFARE,),
    "보호·돌봄": (Category.WELFARE,),
    "취업": (Category.EMPLOYMENT,),
    "일자리": (Category.EMPLOYMENT,),
    "취업·일자리": (Category.EMPLOYMENT,),
    "창업": (Category.STARTUP,),
    "교육": (Category.EDUCATION,),
    "장학금": (Category.EDUCATION,),
    "직업훈련": (Category.EDUCATION,),
    "교육·직업훈련": (Category.EDUCATION,),
    "금융·복지·문화": (Category.FINANCE, Category.WELFARE),
    "기타": (Category.OTHER,),
}

_REGION_ALIASES = {
    "서울": "서울특별시",
    "서울시": "서울특별시",
    "부산": "부산광역시",
    "부산시": "부산광역시",
    "대구": "대구광역시",
    "대구시": "대구광역시",
    "인천": "인천광역시",
    "인천시": "인천광역시",
    "광주": "광주광역시",
    "광주시": "광주광역시",
    "대전": "대전광역시",
    "대전시": "대전광역시",
    "울산": "울산광역시",
    "울산시": "울산광역시",
    "세종": "세종특별자치시",
    "세종시": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
    "제주도": "제주특별자치도",
    "포항": "포항시",
    "전국": "전국",
}
_STANDARD_REGION_SUFFIXES = (
    "특별시",
    "광역시",
    "특별자치시",
    "특별자치도",
    "도",
    "시",
    "군",
    "구",
)


class Normalizer:
    def __init__(
        self,
        validator: NormalizedProgramValidator | None = None,
        region_reference: RegionReference | None = None,
    ) -> None:
        self.validator = validator or NormalizedProgramValidator()
        self.region_reference = (
            region_reference or default_region_reference()
        )

    def normalize(self, policy: ExtractedPolicy) -> ValidationResult:
        issues: list[ValidationIssue] = []
        category_text = normalize_text(policy.category_text)
        categories, category_issues = _normalize_categories(category_text)
        issues.extend(category_issues)

        application_period_text = normalize_text(
            policy.application_period_text
        )
        (
            application_start,
            application_end,
            application_schedule,
            application_status,
            application_issues,
        ) = _normalize_application_period(
            application_period_text,
            policy.collected_at.astimezone(KOREA_TIMEZONE).date(),
        )
        issues.extend(application_issues)

        region_text = normalize_text(policy.region_text)
        (
            regions,
            coverage_scope,
            region_rules,
            region_issues,
        ) = _normalize_region_contract(
            policy,
            region_text,
            self.region_reference,
        )
        issues.extend(region_issues)

        age_condition_text = normalize_text(policy.age_text)
        age_min, age_max, age_issues = _normalize_age(
            age_condition_text,
            zero_only_is_placeholder=(
                policy.source_id == "youthcenter-api"
            ),
        )
        issues.extend(age_issues)

        eligibility_summary = (
            map_eligibility(policy)
            if policy.source_id in ELIGIBILITY_SOURCE_IDS
            else empty_eligibility_summary()
        )

        candidate: dict[str, Any] = {
            "schema_version": NormalizedProgram.SCHEMA_VERSION,
            "source_id": policy.source_id,
            "source_name": normalize_text(policy.source_name),
            "external_id": policy.external_id,
            "title": normalize_text(policy.title),
            "organization": normalize_text(policy.organization),
            "summary": normalize_text(policy.summary),
            "category_text": category_text,
            "categories": [item.value for item in categories],
            "keywords": list(_normalize_string_values(policy.keywords)),
            "life_stages": list(
                _normalize_string_values(policy.life_stages)
            ),
            "target_groups": list(
                _normalize_string_values(policy.target_groups)
            ),
            "application_period_text": application_period_text,
            "application_start": (
                application_start.isoformat()
                if application_start is not None
                else None
            ),
            "application_end": (
                application_end.isoformat()
                if application_end is not None
                else None
            ),
            "application_schedule": (
                application_schedule.value
                if application_schedule is not None
                else None
            ),
            "application_status": (
                application_status.value
                if application_status is not None
                else None
            ),
            "region_text": region_text,
            "regions": list(regions),
            "coverage_scope": coverage_scope.value,
            "region_rules": region_rules,
            "age_min": age_min,
            "age_max": age_max,
            "age_condition_text": age_condition_text,
            "eligibility_text": normalize_text(policy.eligibility_text),
            "eligibility_summary": eligibility_summary.to_dict(),
            "support_content": normalize_text(policy.support_content),
            "application_method": normalize_text(
                policy.application_method
            ),
            "education_statuses": [],
            "employment_statuses": [],
            "required_conditions": [],
            "preferred_conditions": [],
            "excluded_conditions": [],
            "source_url": policy.source_url,
            "collected_at": policy.collected_at.isoformat(),
            "provenance": [
                item.to_dict()
                for item in policy.provenance
            ],
            "data_quality_status": DataQualityStatus.VALID.value,
        }
        candidate["data_quality_status"] = self.validator.classify(
            candidate,
            issues,
        ).value
        return self.validator.validate(candidate, issues)

    def normalize_many(
        self,
        policies: Iterable[ExtractedPolicy],
    ) -> ValidationPartition:
        return partition_validation_results(
            self.normalize(policy)
            for policy in policies
        )


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    parser = _VisibleTextParser()
    parser.feed(value)
    parser.close()
    normalized = re.sub(r"\s+", " ", "".join(parser.parts)).strip()
    return normalized or None


def _normalize_string_values(values: Iterable[str]) -> tuple[str, ...]:
    selected: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized is not None and normalized not in selected:
            selected.append(normalized)
    return tuple(selected)


def _normalize_application_period(
    value: str | None,
    as_of: date,
) -> tuple[
    date | None,
    date | None,
    ApplicationSchedule | None,
    ApplicationStatus | None,
    list[ValidationIssue],
]:
    if value is None:
        return None, None, None, None, []
    if "상시" in value:
        return (
            None,
            None,
            ApplicationSchedule.ALWAYS,
            ApplicationStatus.OPEN,
            [],
        )
    if "마감" in value:
        return None, None, None, ApplicationStatus.CLOSED, []
    if "예산" in value and "소진" in value:
        return (
            None,
            None,
            ApplicationSchedule.UNTIL_BUDGET_EXHAUSTED,
            None,
            [],
        )
    if value == "특정기간":
        return (
            None,
            None,
            ApplicationSchedule.FIXED_PERIOD,
            None,
            [],
        )

    parsed_dates: list[date] = []
    invalid_date = False
    for match in _DATE_TOKEN.finditer(value):
        year, month, day = (
            match.group(1, 2, 3)
            if match.group(1) is not None
            else match.group(4, 5, 6)
        )
        try:
            parsed_dates.append(
                date(int(year), int(month), int(day))
            )
        except ValueError:
            invalid_date = True
    if invalid_date:
        return None, None, None, None, [
            _warning(
                "$.application_period_text",
                "invalid_application_date",
                "application period contains an invalid calendar date",
            )
        ]
    if len(parsed_dates) >= 2:
        start, end = parsed_dates[:2]
        if start > end:
            return None, None, None, None, [
                _warning(
                    "$.application_period_text",
                    "invalid_application_date_order",
                    "application period start is after its end",
                )
            ]
        status = (
            ApplicationStatus.SCHEDULED
            if as_of < start
            else (
                ApplicationStatus.CLOSED
                if as_of > end
                else ApplicationStatus.OPEN
            )
        )
        issues = (
            [
                _warning(
                    "$.application_period_text",
                    "extra_application_dates",
                    "more than two application dates were present",
                )
            ]
            if len(parsed_dates) > 2
            else []
        )
        return (
            start,
            end,
            ApplicationSchedule.FIXED_PERIOD,
            status,
            issues,
        )
    if len(parsed_dates) == 1:
        boundary = parsed_dates[0]
        if "까지" in value:
            status = (
                ApplicationStatus.CLOSED
                if as_of > boundary
                else ApplicationStatus.OPEN
            )
            return (
                None,
                boundary,
                ApplicationSchedule.FIXED_PERIOD,
                status,
                [],
            )
        start = boundary
        status = (
            ApplicationStatus.SCHEDULED
            if as_of < start
            else None
        )
        return (
            start,
            None,
            ApplicationSchedule.FIXED_PERIOD,
            status,
            [],
        )
    month_range = _MONTH_RANGE.search(value)
    same_year_month_range = _SAME_YEAR_MONTH_RANGE.search(value)
    if month_range is not None:
        start_year, start_month, end_year, end_month = map(
            int, month_range.groups()
        )
    elif same_year_month_range is not None:
        start_year, start_month, end_month = map(
            int, same_year_month_range.groups()
        )
        end_year = start_year
    else:
        start_year = start_month = end_year = end_month = None
    if start_year is not None:
        try:
            start = date(start_year, start_month, 1)
            end = date(
                end_year,
                end_month,
                monthrange(end_year, end_month)[1],
            )
        except ValueError:
            return None, None, None, None, [
                _warning(
                    "$.application_period_text",
                    "invalid_application_date",
                    "application period contains an invalid calendar month",
                )
            ]
        if start > end:
            return None, None, None, None, [
                _warning(
                    "$.application_period_text",
                    "invalid_application_date_order",
                    "application period start is after its end",
                )
            ]
        status = (
            ApplicationStatus.SCHEDULED
            if as_of < start
            else (
                ApplicationStatus.CLOSED
                if as_of > end
                else ApplicationStatus.OPEN
            )
        )
        return (
            start,
            end,
            ApplicationSchedule.FIXED_PERIOD,
            status,
            [],
        )
    return None, None, None, None, [
        _warning(
            "$.application_period_text",
            "unparsed_application_period",
            "application period text could not be structured",
        )
    ]


def _normalize_age(
    value: str | None,
    *,
    zero_only_is_placeholder: bool = False,
) -> tuple[int | None, int | None, list[ValidationIssue]]:
    if value is None:
        return None, None, []
    if "제한 없음" in value:
        return None, None, []
    numbers = [int(item) for item in _NUMBER.findall(value)]
    minimum: int | None = None
    maximum: int | None = None
    if len(numbers) >= 2 and _RANGE_MARKER.search(value):
        minimum, maximum = numbers[:2]
    elif len(numbers) == 1 and "이상" in value:
        minimum = numbers[0]
    elif len(numbers) == 1 and "이하" in value:
        maximum = numbers[0]
    else:
        return None, None, (
            [
                _warning(
                    "$.age_condition_text",
                    "unparsed_age_condition",
                    "age condition text could not be structured",
                )
            ]
            if numbers
            else []
        )
    if zero_only_is_placeholder and minimum == 0 and maximum == 0:
        return None, None, [
            _warning(
                "$.age_condition_text",
                "placeholder_age_range",
                "zero-only age range is treated as unknown",
            )
        ]
    if (
        minimum is not None
        and not 0 <= minimum <= 150
        or maximum is not None
        and not 0 <= maximum <= 150
        or minimum is not None
        and maximum is not None
        and minimum > maximum
    ):
        return None, None, [
            _warning(
                "$.age_condition_text",
                "invalid_age_range",
                "age condition contains an invalid range",
            )
        ]
    return minimum, maximum, []


def _normalize_categories(
    value: str | None,
) -> tuple[tuple[Category, ...], list[ValidationIssue]]:
    if value is None:
        return (), []
    tokens = [
        token.strip().replace("･", "·")
        for token in value.split(",")
        if token.strip()
    ]
    selected: list[Category] = []
    issues: list[ValidationIssue] = []
    for token in tokens:
        mapped = _CATEGORY_MAP.get(token)
        if mapped is None:
            mapped = (Category.OTHER,)
            issues.append(
                _warning(
                    "$.categories",
                    "unmapped_category",
                    "category text contains an unmapped value",
                )
            )
        for category in mapped:
            if category not in selected:
                selected.append(category)
    return tuple(selected), issues


def _normalize_regions(
    value: str | None,
) -> tuple[tuple[str, ...], list[ValidationIssue]]:
    if value is None:
        return (), []
    if _REGION_CODES.fullmatch(value):
        return (), [
            _warning(
                "$.regions",
                "unmapped_region_code",
                "region codes require an approved code-to-name table",
            )
        ]
    selected: list[str] = []
    issues: list[ValidationIssue] = []
    for token in (
        item.strip()
        for item in re.split(r"[,|/]", value)
        if item.strip()
    ):
        normalized = _REGION_ALIASES.get(token)
        if normalized is None and token.endswith(_STANDARD_REGION_SUFFIXES):
            normalized = token
        if normalized is None:
            issues.append(
                _warning(
                    "$.regions",
                    "unmapped_region",
                    "region text contains an unmapped value",
                )
            )
            continue
        if normalized not in selected:
            selected.append(normalized)
    return tuple(selected), issues


def _normalize_region_contract(
    policy: ExtractedPolicy,
    region_text: str | None,
    reference: RegionReference,
) -> tuple[
    tuple[str, ...],
    CoverageScope,
    list[dict[str, str | None]],
    list[ValidationIssue],
]:
    if not policy.region_evidence:
        regions, issues = _normalize_regions(region_text)
        scope = (
            CoverageScope.NATIONWIDE
            if policy.coverage_scope_hint
            is ExtractedCoverageScope.NATIONWIDE
            else CoverageScope.UNKNOWN
        )
        return regions, scope, [], issues

    regions: list[str] = []
    rules: list[dict[str, str | None]] = []
    issues: list[ValidationIssue] = []
    matched_rule_keys: set[tuple[str, str, str]] = set()
    unresolved_rule_keys: set[
        tuple[str, str | None, str | None, str | None]
    ] = set()

    for evidence in policy.region_evidence:
        source_text = normalize_text(evidence.source_text)
        if evidence.external_scheme is not None:
            assert evidence.source_code is not None
            resolution = reference.resolve_external_code(
                evidence.external_scheme,
                evidence.source_code,
                active_only=False,
            )
        else:
            assert source_text is not None
            resolution = reference.resolve_alias(source_text)

        relation = (
            RegionRelation.INCLUDE
            if evidence.relation is ExtractedRegionRelation.INCLUDE
            else RegionRelation.EXCLUDE
        )
        if resolution.status is RegionResolutionStatus.MATCHED:
            region = resolution.candidates[0]
            rule_key = (reference.scheme, region.code, relation.value)
            if rule_key in matched_rule_keys:
                continue
            matched_rule_keys.add(rule_key)
            rules.append(
                {
                    "relation": relation.value,
                    "resolution_status": "matched",
                    "region_scheme": reference.scheme,
                    "region_code": region.code,
                    "source_code": evidence.source_code,
                    "source_text": source_text,
                }
            )
            if (
                relation is RegionRelation.INCLUDE
                and region.full_name not in regions
            ):
                regions.append(region.full_name)
            continue

        unresolved_key = (
            relation.value,
            evidence.external_scheme,
            evidence.source_code,
            source_text,
        )
        if unresolved_key in unresolved_rule_keys:
            continue
        unresolved_rule_keys.add(unresolved_key)
        rules.append(
            {
                "relation": relation.value,
                "resolution_status": resolution.status.value,
                "region_scheme": None,
                "region_code": None,
                "source_code": evidence.source_code,
                "source_text": source_text,
            }
        )
        issues.append(
            _warning(
                "$.region_rules",
                (
                    "ambiguous_region"
                    if resolution.status
                    is RegionResolutionStatus.AMBIGUOUS
                    else "unmapped_region_code"
                ),
                "source region evidence could not be resolved exactly",
            )
        )

    has_matched_include = any(
        rule["relation"] == RegionRelation.INCLUDE.value
        and rule["resolution_status"] == "matched"
        for rule in rules
    )
    scope = (
        CoverageScope.REGIONAL
        if has_matched_include
        else CoverageScope.UNKNOWN
    )
    return tuple(regions), scope, rules, issues


def _warning(path: str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        path=path,
        code=code,
        message=message,
        severity="warning",
    )


class _VisibleTextParser(HTMLParser):
    _BLOCK_TAGS = {
        "br",
        "div",
        "li",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
    }
    _HIDDEN_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in self._HIDDEN_TAGS:
            self._hidden_depth += 1
        elif tag in self._BLOCK_TAGS and self._hidden_depth == 0:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._HIDDEN_TAGS and self._hidden_depth:
            self._hidden_depth -= 1
        elif tag in self._BLOCK_TAGS and self._hidden_depth == 0:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._hidden_depth == 0:
            self.parts.append(data)
