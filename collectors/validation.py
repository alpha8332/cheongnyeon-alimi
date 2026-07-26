"""Standard-library JSON Schema checks and normalized quality partitioning."""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from collectors.normalized import (
    DataQualityStatus,
    NormalizedProgram,
    NormalizedProgramValidationError,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = ROOT / "data/schema/normalized_program.schema.json"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    code: str
    message: str
    severity: str

    def __post_init__(self) -> None:
        if self.severity not in {"warning", "error"}:
            raise ValueError("severity must be warning or error")

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: DataQualityStatus
    issues: tuple[ValidationIssue, ...]
    candidate: dict[str, Any]
    program: NormalizedProgram | None


@dataclass(frozen=True, slots=True)
class ValidationPartition:
    valid: tuple[ValidationResult, ...]
    partial: tuple[ValidationResult, ...]
    invalid: tuple[ValidationResult, ...]


class NormalizedProgramValidator:
    """Validate normalized JSON and classify usable versus rejected data."""

    def __init__(
        self,
        schema_path: str | Path = DEFAULT_SCHEMA_PATH,
    ) -> None:
        self.schema_path = Path(schema_path)
        self.schema = json.loads(
            self.schema_path.read_text(encoding="utf-8")
        )

    def schema_issues(
        self,
        candidate: Any,
    ) -> tuple[ValidationIssue, ...]:
        return tuple(
            _schema_issues(candidate, self.schema, self.schema, "$")
        )

    def classify(
        self,
        candidate: Mapping[str, Any],
        normalization_issues: Sequence[ValidationIssue] = (),
    ) -> DataQualityStatus:
        schema_issues = self.schema_issues(candidate)
        semantic_issues = _semantic_issues(candidate)
        if schema_issues or any(
            issue.severity == "error"
            for issue in (*semantic_issues, *normalization_issues)
        ):
            return DataQualityStatus.INVALID
        if normalization_issues or _quality_gap_issues(candidate):
            return DataQualityStatus.PARTIAL
        return DataQualityStatus.VALID

    def validate(
        self,
        candidate: Mapping[str, Any],
        normalization_issues: Sequence[ValidationIssue] = (),
    ) -> ValidationResult:
        selected = deepcopy(dict(candidate))
        schema_issues = list(self.schema_issues(selected))
        semantic_issues = _semantic_issues(selected)
        has_errors = bool(schema_issues) or any(
            issue.severity == "error"
            for issue in (*semantic_issues, *normalization_issues)
        )
        gap_issues = [] if has_errors else _quality_gap_issues(selected)
        expected_status = (
            DataQualityStatus.INVALID
            if has_errors
            else (
                DataQualityStatus.PARTIAL
                if normalization_issues or gap_issues
                else DataQualityStatus.VALID
            )
        )

        mismatch_issues: list[ValidationIssue] = []
        if selected.get("data_quality_status") != expected_status.value:
            mismatch_issues.append(
                ValidationIssue(
                    path="$.data_quality_status",
                    code="quality_status_mismatch",
                    message=(
                        "data_quality_status does not match validator "
                        f"classification {expected_status.value}"
                    ),
                    severity="error",
                )
            )

        issues = _deduplicate_issues(
            [
                *schema_issues,
                *semantic_issues,
                *normalization_issues,
                *gap_issues,
                *mismatch_issues,
            ]
        )
        final_status = (
            DataQualityStatus.INVALID
            if any(issue.severity == "error" for issue in issues)
            else expected_status
        )
        program: NormalizedProgram | None = None
        if final_status is not DataQualityStatus.INVALID:
            try:
                program = NormalizedProgram.from_dict(selected)
            except NormalizedProgramValidationError:
                issues = _deduplicate_issues(
                    [
                        *issues,
                        ValidationIssue(
                            path="$",
                            code="python_model_mismatch",
                            message=(
                                "candidate passed Schema but not the "
                                "Python model"
                            ),
                            severity="error",
                        ),
                    ]
                )
                final_status = DataQualityStatus.INVALID

        return ValidationResult(
            status=final_status,
            issues=tuple(issues),
            candidate=selected,
            program=program,
        )

    def validate_many(
        self,
        candidates: Iterable[Mapping[str, Any]],
    ) -> ValidationPartition:
        return partition_validation_results(
            self.validate(candidate)
            for candidate in candidates
        )


def partition_validation_results(
    results: Iterable[ValidationResult],
) -> ValidationPartition:
    valid: list[ValidationResult] = []
    partial: list[ValidationResult] = []
    invalid: list[ValidationResult] = []
    destinations = {
        DataQualityStatus.VALID: valid,
        DataQualityStatus.PARTIAL: partial,
        DataQualityStatus.INVALID: invalid,
    }
    for result in results:
        destinations[result.status].append(result)
    return ValidationPartition(
        valid=tuple(valid),
        partial=tuple(partial),
        invalid=tuple(invalid),
    )


def _schema_issues(
    instance: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    path: str,
) -> list[ValidationIssue]:
    if "$ref" in schema:
        schema = _resolve_local_ref(root_schema, schema["$ref"])

    expected_types = schema.get("type")
    if expected_types is not None:
        type_names = (
            [expected_types]
            if isinstance(expected_types, str)
            else expected_types
        )
        if not any(
            _matches_json_type(instance, type_name)
            for type_name in type_names
        ):
            return [
                _schema_issue(
                    path,
                    "type",
                    f"expected JSON type {type_names}",
                )
            ]

    issues: list[ValidationIssue] = []
    if "const" in schema and instance != schema["const"]:
        issues.append(
            _schema_issue(path, "const", "value does not match const")
        )
    if "enum" in schema and instance not in schema["enum"]:
        issues.append(
            _schema_issue(path, "enum", "value is not in the enum")
        )

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            issues.append(
                _schema_issue(path, "minLength", "string is too short")
            )
        if len(instance) > schema.get("maxLength", len(instance)):
            issues.append(
                _schema_issue(path, "maxLength", "string is too long")
            )
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            issues.append(
                _schema_issue(path, "pattern", "string pattern mismatch")
            )
        issues.extend(_format_issues(instance, schema.get("format"), path))

    if isinstance(instance, int) and not isinstance(instance, bool):
        if instance < schema.get("minimum", instance):
            issues.append(
                _schema_issue(path, "minimum", "number is too small")
            )
        if instance > schema.get("maximum", instance):
            issues.append(
                _schema_issue(path, "maximum", "number is too large")
            )

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            issues.append(
                _schema_issue(path, "minItems", "array has too few items")
            )
        if len(instance) > schema.get("maxItems", len(instance)):
            issues.append(
                _schema_issue(path, "maxItems", "array has too many items")
            )
        if schema.get("uniqueItems") and not _items_are_unique(instance):
            issues.append(
                _schema_issue(
                    path,
                    "uniqueItems",
                    "array items must be unique",
                )
            )
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(instance):
                issues.extend(
                    _schema_issues(
                        item,
                        item_schema,
                        root_schema,
                        f"{path}[{index}]",
                    )
                )

    if isinstance(instance, dict):
        required = set(schema.get("required", []))
        for field_name in sorted(required - set(instance)):
            issues.append(
                _schema_issue(
                    f"{path}.{field_name}",
                    "required",
                    "required field is missing",
                )
            )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for field_name in sorted(set(instance) - set(properties)):
                issues.append(
                    _schema_issue(
                        f"{path}.{field_name}",
                        "additionalProperties",
                        "additional field is not allowed",
                    )
                )
        for field_name, field_value in instance.items():
            if field_name in properties:
                issues.extend(
                    _schema_issues(
                        field_value,
                        properties[field_name],
                        root_schema,
                        f"{path}.{field_name}",
                    )
                )
    return issues


def _resolve_local_ref(
    root_schema: Mapping[str, Any],
    reference: str,
) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError("only local JSON Schema references are supported")
    selected: Any = root_schema
    for token in reference[2:].split("/"):
        selected = selected[token.replace("~1", "/").replace("~0", "~")]
    if not isinstance(selected, Mapping):
        raise ValueError("JSON Schema reference must resolve to an object")
    return selected


def _matches_json_type(instance: Any, expected_type: str) -> bool:
    checks = {
        "null": instance is None,
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "integer": (
            isinstance(instance, int)
            and not isinstance(instance, bool)
        ),
        "number": (
            isinstance(instance, (int, float))
            and not isinstance(instance, bool)
        ),
        "boolean": isinstance(instance, bool),
    }
    return checks.get(expected_type, False)


def _format_issues(
    value: str,
    format_name: str | None,
    path: str,
) -> list[ValidationIssue]:
    try:
        if format_name == "date":
            date.fromisoformat(value)
        elif format_name == "date-time":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError
        elif format_name == "uri":
            parsed_uri = urllib.parse.urlsplit(value)
            if not parsed_uri.scheme or not parsed_uri.netloc:
                raise ValueError
    except ValueError:
        return [
            _schema_issue(
                path,
                f"format_{format_name}",
                f"invalid {format_name} value",
            )
        ]
    return []


def _items_are_unique(items: list[Any]) -> bool:
    serialized = [
        json.dumps(
            item,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for item in items
    ]
    return len(serialized) == len(set(serialized))


def _schema_issue(
    path: str,
    keyword: str,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        path=path,
        code=f"schema_{keyword}",
        message=message,
        severity="error",
    )


def _semantic_issues(
    candidate: Mapping[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    application_start = _optional_iso_date(
        candidate.get("application_start")
    )
    application_end = _optional_iso_date(
        candidate.get("application_end")
    )
    if (
        application_start is not None
        and application_end is not None
        and application_start > application_end
    ):
        issues.append(
            ValidationIssue(
                path="$.application_end",
                code="date_order",
                message="application_end is before application_start",
                severity="error",
            )
        )
    age_min = candidate.get("age_min")
    age_max = candidate.get("age_max")
    if (
        isinstance(age_min, int)
        and not isinstance(age_min, bool)
        and isinstance(age_max, int)
        and not isinstance(age_max, bool)
        and age_min > age_max
    ):
        issues.append(
            ValidationIssue(
                path="$.age_max",
                code="age_order",
                message="age_max is less than age_min",
                severity="error",
            )
        )
    return issues


def _optional_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _quality_gap_issues(
    candidate: Mapping[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not candidate.get("categories"):
        issues.append(
            _quality_gap(
                "$.categories",
                "missing_categories",
                "no normalized category is available",
            )
        )
    if not candidate.get("regions"):
        issues.append(
            _quality_gap(
                "$.regions",
                "missing_regions",
                "no normalized region is available",
            )
        )
    age_text = candidate.get("age_condition_text")
    if age_text is None:
        issues.append(
            _quality_gap(
                "$.age_condition_text",
                "missing_age_condition",
                "no age condition is available",
            )
        )
    elif (
        candidate.get("age_min") is None
        and candidate.get("age_max") is None
        and "제한 없음" not in str(age_text)
    ):
        issues.append(
            _quality_gap(
                "$.age_condition_text",
                "unstructured_age_condition",
                "age condition could not be structured",
            )
        )
    if (
        candidate.get("application_period_text") is None
        and candidate.get("application_start") is None
        and candidate.get("application_end") is None
        and candidate.get("application_schedule") is None
        and candidate.get("application_status") is None
    ):
        issues.append(
            _quality_gap(
                "$.application_period_text",
                "missing_application_period",
                "no application period information is available",
            )
        )
    elif (
        candidate.get("application_schedule") == "fixed_period"
        and candidate.get("application_start") is None
        and candidate.get("application_end") is None
    ):
        issues.append(
            _quality_gap(
                "$.application_period_text",
                "missing_fixed_period_dates",
                "fixed application period has no dates",
            )
        )
    return issues


def _quality_gap(
    path: str,
    code: str,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        path=path,
        code=code,
        message=message,
        severity="warning",
    )


def _deduplicate_issues(
    issues: Iterable[ValidationIssue],
) -> list[ValidationIssue]:
    selected: list[ValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.path, issue.code, issue.severity)
        if key not in seen:
            selected.append(issue)
            seen.add(key)
    return selected
