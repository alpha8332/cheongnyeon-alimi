"""Deterministic field presence and empty-value profiling."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from collectors.raw import RawDocumentRole


@dataclass(frozen=True, slots=True)
class FieldStatistics:
    field_name: str
    present_count: int
    missing_count: int
    presence_rate: float
    empty_count: int
    empty_rate: float
    non_empty_count: int
    observed_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "present_count": self.present_count,
            "missing_count": self.missing_count,
            "presence_rate": self.presence_rate,
            "empty_count": self.empty_count,
            "empty_rate": self.empty_rate,
            "non_empty_count": self.non_empty_count,
            "observed_types": list(self.observed_types),
        }


@dataclass(frozen=True, slots=True)
class SourceFieldProfile:
    source_id: str
    document_role: RawDocumentRole
    document_count: int
    fields: tuple[FieldStatistics, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "document_role": self.document_role.value,
            "document_count": self.document_count,
            "fields": [
                field.to_dict()
                for field in self.fields
            ],
        }


def build_field_profile(
    *,
    source_id: str,
    document_role: RawDocumentRole,
    records: Iterable[Mapping[str, Any]],
) -> SourceFieldProfile:
    selected = list(records)
    present_counts: Counter[str] = Counter()
    empty_counts: Counter[str] = Counter()
    observed_types: dict[str, set[str]] = {}

    for record in selected:
        for field_name, value in record.items():
            present_counts[field_name] += 1
            if _is_empty(value):
                empty_counts[field_name] += 1
            observed_types.setdefault(field_name, set()).add(
                _json_type_name(value)
            )

    fields = tuple(
        FieldStatistics(
            field_name=field_name,
            present_count=present_counts[field_name],
            missing_count=len(selected) - present_counts[field_name],
            presence_rate=(
                present_counts[field_name] / len(selected)
                if selected
                else 0.0
            ),
            empty_count=empty_counts[field_name],
            empty_rate=(
                empty_counts[field_name] / len(selected)
                if selected
                else 0.0
            ),
            non_empty_count=(
                present_counts[field_name] - empty_counts[field_name]
            ),
            observed_types=tuple(sorted(observed_types[field_name])),
        )
        for field_name in sorted(present_counts)
    )
    return SourceFieldProfile(
        source_id=source_id,
        document_role=document_role,
        document_count=len(selected),
        fields=fields,
    )


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__
