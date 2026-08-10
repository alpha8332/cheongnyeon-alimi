"""Shared eligibility evidence contract for Data, Backend, and Frontend."""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from collectors.registry import SOURCE_ID_PATTERN


class EligibilityContractError(ValueError):
    """An eligibility summary violates the approved shared contract."""


class EligibilityCoverage(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class EligibilityCategory(str, Enum):
    AGE = "age"
    REGION = "region"
    INCOME = "income"
    ASSET = "asset"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    HOUSING = "housing"
    HOUSEHOLD = "household"
    OTHER = "other"


class EvidenceLocatorType(str, Enum):
    SOURCE_FIELD = "source_field"
    CSS_SELECTOR = "css_selector"


class InstitutionalContactKind(str, Enum):
    PHONE = "phone"
    OFFICIAL_CHANNEL = "official_channel"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Public, non-secret pointer to the source text behind one item."""

    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "source_id",
            "source_url",
            "collected_at",
            "locator_type",
            "locator",
        }
    )

    source_id: str
    source_url: str
    collected_at: datetime
    locator_type: EvidenceLocatorType
    locator: str

    def __post_init__(self) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise EligibilityContractError("invalid evidence source_id")
        _validate_http_url(self.source_url, "evidence source_url")
        if (
            not isinstance(self.collected_at, datetime)
            or self.collected_at.tzinfo is None
            or self.collected_at.utcoffset() is None
        ):
            raise EligibilityContractError(
                "evidence collected_at must include a timezone"
            )
        if not isinstance(self.locator_type, EvidenceLocatorType):
            raise EligibilityContractError("invalid evidence locator_type")
        _required_single_line(self.locator, "evidence locator", 1024)

    @classmethod
    def from_dict(cls, value: Any) -> EvidenceReference:
        _require_exact_fields(value, cls.FIELD_NAMES, "evidence")
        try:
            collected_at = datetime.fromisoformat(
                value["collected_at"].replace("Z", "+00:00")
            )
            return cls(
                source_id=value["source_id"],
                source_url=value["source_url"],
                collected_at=collected_at,
                locator_type=EvidenceLocatorType(value["locator_type"]),
                locator=value["locator"],
            )
        except (AttributeError, TypeError, ValueError):
            raise EligibilityContractError(
                "evidence contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat(),
            "locator_type": self.locator_type.value,
            "locator": self.locator,
        }


@dataclass(frozen=True, slots=True)
class EligibilityEvidenceItem:
    """One exact source condition and its comparison category."""

    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {"category", "text", "evidence"}
    )

    category: EligibilityCategory
    text: str
    evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.category, EligibilityCategory):
            raise EligibilityContractError("invalid eligibility category")
        _required_text(self.text, "eligibility item text", 10000)
        _validate_evidence(self.evidence)

    @classmethod
    def from_dict(cls, value: Any) -> EligibilityEvidenceItem:
        _require_exact_fields(value, cls.FIELD_NAMES, "eligibility item")
        try:
            return cls(
                category=EligibilityCategory(value["category"]),
                text=value["text"],
                evidence=_parse_evidence(value["evidence"]),
            )
        except (TypeError, ValueError):
            raise EligibilityContractError(
                "eligibility item contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "text": self.text,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class RequiredDocument:
    """One document explicitly requested by the source."""

    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset({"text", "evidence"})

    text: str
    evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        _required_text(self.text, "required document text", 4000)
        _validate_evidence(self.evidence)

    @classmethod
    def from_dict(cls, value: Any) -> RequiredDocument:
        _require_exact_fields(value, cls.FIELD_NAMES, "required document")
        try:
            return cls(
                text=value["text"],
                evidence=_parse_evidence(value["evidence"]),
            )
        except (TypeError, ValueError):
            raise EligibilityContractError(
                "required document contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class InstitutionalContact:
    """A public facility contact; personal contact fields are unsupported."""

    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {"kind", "label", "value", "evidence"}
    )

    kind: InstitutionalContactKind
    label: str
    value: str
    evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, InstitutionalContactKind):
            raise EligibilityContractError("invalid contact kind")
        _required_single_line(self.label, "contact label", 255)
        _required_single_line(self.value, "contact value", 1000)
        if "@" in self.value:
            raise EligibilityContractError(
                "email addresses are not part of the contact contract"
            )
        digits = re.sub(r"\D", "", self.value)
        if digits.startswith(
            (
                "010",
                "011",
                "016",
                "017",
                "018",
                "019",
                "8210",
                "8211",
                "8216",
                "8217",
                "8218",
                "8219",
            )
        ):
            raise EligibilityContractError(
                "personal mobile numbers are not allowed"
            )
        if self.kind is InstitutionalContactKind.PHONE and not digits:
            raise EligibilityContractError("phone contact requires digits")
        _validate_evidence(self.evidence)

    @classmethod
    def from_dict(cls, value: Any) -> InstitutionalContact:
        _require_exact_fields(value, cls.FIELD_NAMES, "institutional contact")
        try:
            return cls(
                kind=InstitutionalContactKind(value["kind"]),
                label=value["label"],
                value=value["value"],
                evidence=_parse_evidence(value["evidence"]),
            )
        except (TypeError, ValueError):
            raise EligibilityContractError(
                "institutional contact contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "label": self.label,
            "value": self.value,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class EligibilitySummary:
    """Version 1.0.0 shared nested contract for policy eligibility details."""

    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "coverage",
            "requirements",
            "exclusions",
            "preferences",
            "documents",
            "unknowns",
            "institutional_contacts",
        }
    )

    coverage: EligibilityCoverage
    requirements: tuple[EligibilityEvidenceItem, ...]
    exclusions: tuple[EligibilityEvidenceItem, ...]
    preferences: tuple[EligibilityEvidenceItem, ...]
    documents: tuple[RequiredDocument, ...]
    unknowns: tuple[EligibilityEvidenceItem, ...]
    institutional_contacts: tuple[InstitutionalContact, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, EligibilityCoverage):
            raise EligibilityContractError("invalid eligibility coverage")
        for field_name in (
            "requirements",
            "exclusions",
            "preferences",
            "unknowns",
        ):
            _validate_unique_tuple(
                getattr(self, field_name),
                EligibilityEvidenceItem,
                field_name,
            )
        _validate_unique_tuple(
            self.documents,
            RequiredDocument,
            "documents",
        )
        _validate_unique_tuple(
            self.institutional_contacts,
            InstitutionalContact,
            "institutional_contacts",
        )
        if self.coverage is EligibilityCoverage.COMPLETE and self.unknowns:
            raise EligibilityContractError(
                "complete coverage cannot contain unknown conditions"
            )
        if self.coverage is EligibilityCoverage.UNKNOWN and any(
            (
                self.requirements,
                self.exclusions,
                self.preferences,
                self.documents,
                self.unknowns,
            )
        ):
            raise EligibilityContractError(
                "unknown coverage cannot contain eligibility or document items"
            )

    @classmethod
    def from_dict(cls, value: Any) -> EligibilitySummary:
        _require_exact_fields(value, cls.FIELD_NAMES, "eligibility summary")
        try:
            return cls(
                coverage=EligibilityCoverage(value["coverage"]),
                requirements=_parse_items(
                    value["requirements"], EligibilityEvidenceItem
                ),
                exclusions=_parse_items(
                    value["exclusions"], EligibilityEvidenceItem
                ),
                preferences=_parse_items(
                    value["preferences"], EligibilityEvidenceItem
                ),
                documents=_parse_items(value["documents"], RequiredDocument),
                unknowns=_parse_items(
                    value["unknowns"], EligibilityEvidenceItem
                ),
                institutional_contacts=_parse_items(
                    value["institutional_contacts"], InstitutionalContact
                ),
            )
        except (TypeError, ValueError):
            raise EligibilityContractError(
                "eligibility summary contains an invalid field value"
            ) from None

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage": self.coverage.value,
            "requirements": [item.to_dict() for item in self.requirements],
            "exclusions": [item.to_dict() for item in self.exclusions],
            "preferences": [item.to_dict() for item in self.preferences],
            "documents": [item.to_dict() for item in self.documents],
            "unknowns": [item.to_dict() for item in self.unknowns],
            "institutional_contacts": [
                item.to_dict() for item in self.institutional_contacts
            ],
        }


def empty_eligibility_summary() -> EligibilitySummary:
    """Return the safe compatibility value for an unmapped legacy policy."""

    return EligibilitySummary(
        coverage=EligibilityCoverage.UNKNOWN,
        requirements=(),
        exclusions=(),
        preferences=(),
        documents=(),
        unknowns=(),
        institutional_contacts=(),
    )


def _require_exact_fields(
    value: Any,
    expected: frozenset[str],
    label: str,
) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise EligibilityContractError(f"{label} fields do not match the contract")


def _parse_items(value: Any, item_type: type[Any]) -> tuple[Any, ...]:
    if not isinstance(value, list):
        raise EligibilityContractError("contract collections must be arrays")
    return tuple(item_type.from_dict(item) for item in value)


def _parse_evidence(value: Any) -> tuple[EvidenceReference, ...]:
    return _parse_items(value, EvidenceReference)


def _validate_evidence(value: tuple[EvidenceReference, ...]) -> None:
    _validate_unique_tuple(value, EvidenceReference, "evidence", require_one=True)


def _validate_unique_tuple(
    value: Any,
    item_type: type[Any],
    field_name: str,
    *,
    require_one: bool = False,
) -> None:
    if (
        not isinstance(value, tuple)
        or not all(isinstance(item, item_type) for item in value)
        or (require_one and not value)
        or len(value) != len(set(value))
    ):
        raise EligibilityContractError(
            f"{field_name} must contain unique contract items"
        )


def _required_text(value: Any, field_name: str, max_length: int) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > max_length
        or "\r" in value
    ):
        raise EligibilityContractError(
            f"{field_name} must be non-empty normalized source text"
        )


def _required_single_line(value: Any, field_name: str, max_length: int) -> None:
    _required_text(value, field_name, max_length)
    if "\n" in value:
        raise EligibilityContractError(f"{field_name} must be a single line")


def _validate_http_url(value: Any, field_name: str) -> None:
    if not isinstance(value, str):
        raise EligibilityContractError(f"{field_name} must be an HTTP(S) URL")
    parsed = urllib.parse.urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise EligibilityContractError(
            f"{field_name} must be an HTTP(S) URL"
        ) from None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or any(character.isspace() for character in value)
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and not 1 <= port <= 65535
    ):
        raise EligibilityContractError(f"{field_name} must be an HTTP(S) URL")
