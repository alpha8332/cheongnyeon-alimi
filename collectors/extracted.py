"""Common intermediate contract produced by source-specific extractors."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from collectors.raw import (
    CONTENT_HASH_PATTERN,
    DOCUMENT_ID_PATTERN,
    RawDocumentRole,
    RawPolicyDocument,
)
from collectors.registry import SOURCE_ID_PATTERN


class ExtractionError(ValueError):
    """Raw documents cannot be interpreted under a source contract."""


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Replay metadata for one Raw document that contributed to a policy."""

    raw_document_id: str
    document_role: RawDocumentRole
    content_hash: str
    collected_at: datetime
    source_url: str

    def __post_init__(self) -> None:
        if not DOCUMENT_ID_PATTERN.fullmatch(self.raw_document_id):
            raise ExtractionError("invalid provenance Raw document ID")
        if not isinstance(self.document_role, RawDocumentRole):
            raise ExtractionError("invalid provenance document role")
        if not CONTENT_HASH_PATTERN.fullmatch(self.content_hash):
            raise ExtractionError("invalid provenance content hash")
        _validate_datetime(self.collected_at, "provenance collected_at")
        _validate_url(self.source_url, "provenance source_url")

    @classmethod
    def from_raw(cls, document: RawPolicyDocument) -> SourceProvenance:
        return cls(
            raw_document_id=document.document_id,
            document_role=document.document_role,
            content_hash=document.content_hash,
            collected_at=document.collected_at,
            source_url=document.source_url,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "raw_document_id": self.raw_document_id,
            "document_role": self.document_role.value,
            "content_hash": self.content_hash,
            "collected_at": self.collected_at.isoformat(),
            "source_url": self.source_url,
        }


@dataclass(frozen=True, slots=True)
class ExtractedPolicy:
    """Source-neutral text fields with complete source-specific evidence."""

    source_id: str
    source_name: str
    external_id: str
    title: str | None
    organization: str | None
    category_text: str | None
    application_period_text: str | None
    region_text: str | None
    age_text: str | None
    eligibility_text: str | None
    support_content: str | None
    application_method: str | None
    source_url: str
    collected_at: datetime
    provenance: tuple[SourceProvenance, ...]
    extra: dict[str, Any]

    def __post_init__(self) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise ExtractionError("invalid ExtractedPolicy source ID")
        if not self.source_name or not self.source_name.strip():
            raise ExtractionError("source_name cannot be empty")
        if (
            not self.external_id
            or self.external_id != self.external_id.strip()
            or any(character.isspace() for character in self.external_id)
        ):
            raise ExtractionError("external_id must be a non-empty token")
        for field_name in (
            "title",
            "organization",
            "category_text",
            "application_period_text",
            "region_text",
            "age_text",
            "eligibility_text",
            "support_content",
            "application_method",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ExtractionError(
                    f"{field_name} must be a string or null"
                )
        _validate_url(self.source_url, "source_url")
        _validate_datetime(self.collected_at, "collected_at")
        if not self.provenance:
            raise ExtractionError("provenance cannot be empty")
        raw_ids = [
            item.raw_document_id
            for item in self.provenance
        ]
        if len(raw_ids) != len(set(raw_ids)):
            raise ExtractionError("provenance Raw document IDs must be unique")
        if self.collected_at != max(
            item.collected_at
            for item in self.provenance
        ):
            raise ExtractionError(
                "collected_at must match the latest provenance timestamp"
            )
        if not isinstance(self.extra, dict):
            raise ExtractionError("extra must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "external_id": self.external_id,
            "title": self.title,
            "organization": self.organization,
            "category_text": self.category_text,
            "application_period_text": self.application_period_text,
            "region_text": self.region_text,
            "age_text": self.age_text,
            "eligibility_text": self.eligibility_text,
            "support_content": self.support_content,
            "application_method": self.application_method,
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat(),
            "provenance": [
                item.to_dict()
                for item in self.provenance
            ],
            "extra": self.extra,
        }


def _validate_datetime(value: datetime, field_name: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ExtractionError(f"{field_name} must include a timezone")


def _validate_url(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise ExtractionError(f"{field_name} must be an HTTP(S) URL")
    parsed = urllib.parse.urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise ExtractionError(f"{field_name} must be an HTTP(S) URL") from None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and not 1 <= port <= 65535
    ):
        raise ExtractionError(f"{field_name} must be an HTTP(S) URL")
