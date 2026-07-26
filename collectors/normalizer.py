"""Deterministic source-neutral normalization of extracted policies."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, timedelta, timezone
from html.parser import HTMLParser
from typing import Any

from collectors.extracted import ExtractedPolicy
from collectors.normalized import (
    ApplicationSchedule,
    ApplicationStatus,
    Category,
    DataQualityStatus,
    NormalizedProgram,
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
    ) -> None:
        self.validator = validator or NormalizedProgramValidator()

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
        regions, region_issues = _normalize_regions(region_text)
        issues.extend(region_issues)

        age_condition_text = normalize_text(policy.age_text)
        age_min, age_max, age_issues = _normalize_age(age_condition_text)
        issues.extend(age_issues)

        candidate: dict[str, Any] = {
            "schema_version": NormalizedProgram.SCHEMA_VERSION,
            "source_id": policy.source_id,
            "source_name": normalize_text(policy.source_name),
            "external_id": policy.external_id,
            "title": normalize_text(policy.title),
            "organization": normalize_text(policy.organization),
            "summary": None,
            "category_text": category_text,
            "categories": [item.value for item in categories],
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
            "age_min": age_min,
            "age_max": age_max,
            "age_condition_text": age_condition_text,
            "eligibility_text": normalize_text(policy.eligibility_text),
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
        start = parsed_dates[0]
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
    return None, None, None, None, [
        _warning(
            "$.application_period_text",
            "unparsed_application_period",
            "application period text could not be structured",
        )
    ]


def _normalize_age(
    value: str | None,
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
