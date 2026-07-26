"""Canonical normalized policy model shared with later pipeline stages."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, ClassVar

from collectors.extracted import SourceProvenance
from collectors.raw import RawDocumentRole
from collectors.registry import SOURCE_ID_PATTERN


class NormalizedProgramValidationError(ValueError):
    """A normalized program violates the Python contract."""


class Category(str, Enum):
    HOUSING = "housing"
    FINANCE = "finance"
    WELFARE = "welfare"
    EMPLOYMENT = "employment"
    STARTUP = "startup"
    EDUCATION = "education"
    OTHER = "other"


class ApplicationSchedule(str, Enum):
    FIXED_PERIOD = "fixed_period"
    ALWAYS = "always"
    UNTIL_BUDGET_EXHAUSTED = "until_budget_exhausted"


class ApplicationStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SCHEDULED = "scheduled"


class DataQualityStatus(str, Enum):
    VALID = "valid"
    PARTIAL = "partial"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class NormalizedProgram:
    """Schema-valid normalized policy ready for quality-aware consumers."""

    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "schema_version",
            "source_id",
            "source_name",
            "external_id",
            "title",
            "organization",
            "summary",
            "category_text",
            "categories",
            "application_period_text",
            "application_start",
            "application_end",
            "application_schedule",
            "application_status",
            "region_text",
            "regions",
            "age_min",
            "age_max",
            "age_condition_text",
            "eligibility_text",
            "support_content",
            "application_method",
            "education_statuses",
            "employment_statuses",
            "required_conditions",
            "preferred_conditions",
            "excluded_conditions",
            "source_url",
            "collected_at",
            "provenance",
            "data_quality_status",
        }
    )

    source_id: str
    source_name: str
    external_id: str | None
    title: str
    organization: str | None
    summary: str | None
    category_text: str | None
    categories: tuple[Category, ...]
    application_period_text: str | None
    application_start: date | None
    application_end: date | None
    application_schedule: ApplicationSchedule | None
    application_status: ApplicationStatus | None
    region_text: str | None
    regions: tuple[str, ...]
    age_min: int | None
    age_max: int | None
    age_condition_text: str | None
    eligibility_text: str | None
    support_content: str | None
    application_method: str | None
    education_statuses: tuple[str, ...]
    employment_statuses: tuple[str, ...]
    required_conditions: tuple[str, ...]
    preferred_conditions: tuple[str, ...]
    excluded_conditions: tuple[str, ...]
    source_url: str
    collected_at: datetime
    provenance: tuple[SourceProvenance, ...]
    data_quality_status: DataQualityStatus

    def __post_init__(self) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise NormalizedProgramValidationError("invalid source_id")
        _required_text(
            self.source_name,
            "source_name",
            max_length=255,
        )
        if self.external_id is not None:
            _required_text(
                self.external_id,
                "external_id",
                max_length=512,
            )
            if any(character.isspace() for character in self.external_id):
                raise NormalizedProgramValidationError(
                    "external_id cannot contain whitespace"
                )
        _required_text(self.title, "title", max_length=1000)
        for field_name in (
            "organization",
            "summary",
            "category_text",
            "application_period_text",
            "region_text",
            "age_condition_text",
            "eligibility_text",
            "support_content",
            "application_method",
        ):
            _optional_text(getattr(self, field_name), field_name)
        _enum_tuple(self.categories, Category, "categories")
        _optional_enum(
            self.application_schedule,
            ApplicationSchedule,
            "application_schedule",
        )
        _optional_enum(
            self.application_status,
            ApplicationStatus,
            "application_status",
        )
        if (
            self.application_start is not None
            and type(self.application_start) is not date
        ):
            raise NormalizedProgramValidationError(
                "application_start must be a date or null"
            )
        if (
            self.application_end is not None
            and type(self.application_end) is not date
        ):
            raise NormalizedProgramValidationError(
                "application_end must be a date or null"
            )
        if (
            self.application_start is not None
            and self.application_end is not None
            and self.application_start > self.application_end
        ):
            raise NormalizedProgramValidationError(
                "application_start cannot be after application_end"
            )
        _string_tuple(self.regions, "regions")
        for field_name in (
            "education_statuses",
            "employment_statuses",
            "required_conditions",
            "preferred_conditions",
            "excluded_conditions",
        ):
            _string_tuple(getattr(self, field_name), field_name)
        _optional_age(self.age_min, "age_min")
        _optional_age(self.age_max, "age_max")
        if (
            self.age_min is not None
            and self.age_max is not None
            and self.age_min > self.age_max
        ):
            raise NormalizedProgramValidationError(
                "age_min cannot be greater than age_max"
            )
        _validate_url(self.source_url)
        if (
            not isinstance(self.collected_at, datetime)
            or self.collected_at.tzinfo is None
            or self.collected_at.utcoffset() is None
        ):
            raise NormalizedProgramValidationError(
                "collected_at must include a timezone"
            )
        if (
            not isinstance(self.provenance, tuple)
            or not self.provenance
            or not all(
                isinstance(item, SourceProvenance)
                for item in self.provenance
            )
        ):
            raise NormalizedProgramValidationError(
                "provenance must contain SourceProvenance values"
            )
        raw_ids = [item.raw_document_id for item in self.provenance]
        if len(raw_ids) != len(set(raw_ids)):
            raise NormalizedProgramValidationError(
                "provenance Raw document IDs must be unique"
            )
        if self.collected_at != max(
            item.collected_at
            for item in self.provenance
        ):
            raise NormalizedProgramValidationError(
                "collected_at must match the latest provenance timestamp"
            )
        if not isinstance(self.data_quality_status, DataQualityStatus):
            raise NormalizedProgramValidationError(
                "invalid data_quality_status"
            )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> NormalizedProgram:
        if set(value) != cls.FIELD_NAMES:
            raise NormalizedProgramValidationError(
                "NormalizedProgram fields do not match schema version 1.0.0"
            )
        if value.get("schema_version") != cls.SCHEMA_VERSION:
            raise NormalizedProgramValidationError(
                "unsupported NormalizedProgram schema version"
            )
        try:
            return cls(
                source_id=value["source_id"],
                source_name=value["source_name"],
                external_id=value["external_id"],
                title=value["title"],
                organization=value["organization"],
                summary=value["summary"],
                category_text=value["category_text"],
                categories=_parse_category_array(value["categories"]),
                application_period_text=value[
                    "application_period_text"
                ],
                application_start=_parse_date(
                    value["application_start"]
                ),
                application_end=_parse_date(value["application_end"]),
                application_schedule=_parse_optional_enum(
                    value["application_schedule"],
                    ApplicationSchedule,
                ),
                application_status=_parse_optional_enum(
                    value["application_status"],
                    ApplicationStatus,
                ),
                region_text=value["region_text"],
                regions=_parse_string_array(value["regions"]),
                age_min=value["age_min"],
                age_max=value["age_max"],
                age_condition_text=value["age_condition_text"],
                eligibility_text=value["eligibility_text"],
                support_content=value["support_content"],
                application_method=value["application_method"],
                education_statuses=_parse_string_array(
                    value["education_statuses"]
                ),
                employment_statuses=_parse_string_array(
                    value["employment_statuses"]
                ),
                required_conditions=_parse_string_array(
                    value["required_conditions"]
                ),
                preferred_conditions=_parse_string_array(
                    value["preferred_conditions"]
                ),
                excluded_conditions=_parse_string_array(
                    value["excluded_conditions"]
                ),
                source_url=value["source_url"],
                collected_at=_parse_datetime(value["collected_at"]),
                provenance=_parse_provenance_array(value["provenance"]),
                data_quality_status=DataQualityStatus(
                    value["data_quality_status"]
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            NormalizedProgramValidationError,
        ):
            raise NormalizedProgramValidationError(
                "NormalizedProgram contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "external_id": self.external_id,
            "title": self.title,
            "organization": self.organization,
            "summary": self.summary,
            "category_text": self.category_text,
            "categories": [item.value for item in self.categories],
            "application_period_text": self.application_period_text,
            "application_start": (
                self.application_start.isoformat()
                if self.application_start is not None
                else None
            ),
            "application_end": (
                self.application_end.isoformat()
                if self.application_end is not None
                else None
            ),
            "application_schedule": (
                self.application_schedule.value
                if self.application_schedule is not None
                else None
            ),
            "application_status": (
                self.application_status.value
                if self.application_status is not None
                else None
            ),
            "region_text": self.region_text,
            "regions": list(self.regions),
            "age_min": self.age_min,
            "age_max": self.age_max,
            "age_condition_text": self.age_condition_text,
            "eligibility_text": self.eligibility_text,
            "support_content": self.support_content,
            "application_method": self.application_method,
            "education_statuses": list(self.education_statuses),
            "employment_statuses": list(self.employment_statuses),
            "required_conditions": list(self.required_conditions),
            "preferred_conditions": list(self.preferred_conditions),
            "excluded_conditions": list(self.excluded_conditions),
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat(),
            "provenance": [
                item.to_dict()
                for item in self.provenance
            ],
            "data_quality_status": self.data_quality_status.value,
        }


def _required_text(
    value: Any,
    field_name: str,
    *,
    max_length: int | None = None,
) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\r" in value
        or "\n" in value
        or (
            max_length is not None
            and len(value) > max_length
        )
    ):
        raise NormalizedProgramValidationError(
            f"{field_name} must be a non-empty normalized string"
        )


def _optional_text(value: Any, field_name: str) -> None:
    if value is not None:
        _required_text(value, field_name)


def _string_tuple(value: Any, field_name: str) -> None:
    if not isinstance(value, tuple) or not all(
        isinstance(item, str)
        and item
        and item == item.strip()
        and "\r" not in item
        and "\n" not in item
        for item in value
    ):
        raise NormalizedProgramValidationError(
            f"{field_name} must be a tuple of normalized strings"
        )
    if len(value) != len(set(value)):
        raise NormalizedProgramValidationError(
            f"{field_name} cannot contain duplicates"
        )


def _enum_tuple(
    value: Any,
    enum_type: type[Enum],
    field_name: str,
) -> None:
    if not isinstance(value, tuple) or not all(
        isinstance(item, enum_type)
        for item in value
    ):
        raise NormalizedProgramValidationError(
            f"{field_name} must contain the expected enum"
        )
    if len(value) != len(set(value)):
        raise NormalizedProgramValidationError(
            f"{field_name} cannot contain duplicates"
        )


def _optional_enum(
    value: Any,
    enum_type: type[Enum],
    field_name: str,
) -> None:
    if value is not None and not isinstance(value, enum_type):
        raise NormalizedProgramValidationError(
            f"{field_name} must contain the expected enum or null"
        )


def _optional_age(value: Any, field_name: str) -> None:
    if value is None:
        return
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 150
    ):
        raise NormalizedProgramValidationError(
            f"{field_name} must be an integer from 0 to 150 or null"
        )


def _validate_url(value: Any) -> None:
    if not isinstance(value, str):
        raise NormalizedProgramValidationError(
            "source_url must be an HTTP(S) URL"
        )
    parsed = urllib.parse.urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise NormalizedProgramValidationError(
            "source_url must be an HTTP(S) URL"
        ) from None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or any(character.isspace() for character in value)
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and not 1 <= port <= 65535
    ):
        raise NormalizedProgramValidationError(
            "source_url must be an HTTP(S) URL"
        )


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError
    return date.fromisoformat(value)


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError
    return parsed


def _parse_optional_enum(
    value: Any,
    enum_type: type[Enum],
) -> Any:
    return None if value is None else enum_type(value)


def _parse_string_array(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError
    return tuple(value)


def _parse_category_array(value: Any) -> tuple[Category, ...]:
    if not isinstance(value, list):
        raise TypeError
    return tuple(Category(item) for item in value)


def _parse_provenance_array(
    value: Any,
) -> tuple[SourceProvenance, ...]:
    if not isinstance(value, list):
        raise TypeError
    return tuple(_parse_provenance(item) for item in value)


def _parse_provenance(value: Any) -> SourceProvenance:
    if not isinstance(value, dict):
        raise TypeError
    return SourceProvenance(
        raw_document_id=value["raw_document_id"],
        document_role=RawDocumentRole(value["document_role"]),
        content_hash=value["content_hash"],
        collected_at=_parse_datetime(value["collected_at"]),
        source_url=value["source_url"],
    )
