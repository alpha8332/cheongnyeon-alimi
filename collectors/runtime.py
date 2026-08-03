"""Replay stored Raw documents without making source API requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.normalized import DataQualityStatus
from collectors.normalizer import Normalizer
from collectors.raw import RawDocumentRole, RawPolicyDocument
from collectors.storage import RawDocumentStore, RawStorageError
from collectors.validation import ValidationResult
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID


SUPPORTED_SOURCE_IDS = (
    BOKJIRO_SOURCE_ID,
    YOUTHCENTER_SOURCE_ID,
)

_EXTRACTOR_TYPES = {
    BOKJIRO_SOURCE_ID: BokjiroExtractor,
    YOUTHCENTER_SOURCE_ID: YouthCenterExtractor,
}


class RuntimeReplayError(RuntimeError):
    """Stored Raw cannot be safely selected or processed."""


@dataclass(frozen=True, slots=True)
class RuntimeValidationIssue:
    index: int
    source_id: str | None
    external_id: str | None
    codes: tuple[str, ...]
    paths: tuple[str, ...]
    raw_document_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeReplayResult:
    source_id: str
    raw_document_count: int
    extracted_count: int
    valid_count: int
    partial_count: int
    invalid_count: int
    programs: tuple[dict[str, Any], ...]
    issues: tuple[RuntimeValidationIssue, ...]
    normalization_issues: tuple[tuple[ValidationIssue, ...], ...] = ()

    @property
    def accepted_count(self) -> int:
        return len(self.programs)


def replay_runtime_raw(
    *,
    raw_root: str | Path,
    source_id: str,
    limit: int,
    normalizer: Normalizer | None = None,
) -> RuntimeReplayResult:
    """Load the latest source batch and normalize its policies."""
    if source_id not in _EXTRACTOR_TYPES:
        raise RuntimeReplayError("unsupported runtime source")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 500
    ):
        raise RuntimeReplayError("limit must be an integer from 1 to 500")

    documents = _load_source_documents(raw_root, source_id)
    selected_documents = _latest_batch(documents, limit)
    try:
        extracted = _EXTRACTOR_TYPES[source_id]().extract(
            selected_documents
        )
    except Exception as exc:
        raise RuntimeReplayError(
            f"runtime extraction failed ({type(exc).__name__})"
        ) from None

    selected_normalizer = normalizer or Normalizer()
    results = [
        selected_normalizer.normalize(policy)
        for policy in extracted
    ]
    accepted_results = tuple(
        result for result in results if result.program is not None
    )
    programs = tuple(
        result.program.to_dict()
        for result in accepted_results
        if result.program is not None
    )
    issues = tuple(
        _validation_issue(index, result)
        for index, result in enumerate(results)
        if result.program is None
    )
    return RuntimeReplayResult(
        source_id=source_id,
        raw_document_count=len(selected_documents),
        extracted_count=len(extracted),
        valid_count=sum(
            result.status is DataQualityStatus.VALID
            for result in results
        ),
        partial_count=sum(
            result.status is DataQualityStatus.PARTIAL
            for result in results
        ),
        invalid_count=sum(
            result.status is DataQualityStatus.INVALID
            for result in results
        ),
        programs=programs,
        issues=issues,
        normalization_issues=tuple(
            result.issues for result in accepted_results
        ),
    )


def _load_source_documents(
    raw_root: str | Path,
    source_id: str,
) -> tuple[RawPolicyDocument, ...]:
    store = RawDocumentStore(raw_root)
    source_root = store.root / source_id
    if not source_root.is_dir():
        raise RuntimeReplayError("no stored Raw documents found for source")

    paths = sorted(source_root.rglob("*.json"))
    if not paths:
        raise RuntimeReplayError("no stored Raw documents found for source")
    try:
        documents = tuple(store.load(path) for path in paths)
    except RawStorageError:
        raise RuntimeReplayError(
            "stored Raw document could not be loaded"
        ) from None
    if any(document.source_id != source_id for document in documents):
        raise RuntimeReplayError("stored Raw source does not match its directory")
    return documents


def _latest_batch(
    documents: tuple[RawPolicyDocument, ...],
    limit: int,
) -> tuple[RawPolicyDocument, ...]:
    list_responses = [
        document
        for document in documents
        if document.document_role is RawDocumentRole.LIST_RESPONSE
    ]
    if not list_responses:
        raise RuntimeReplayError("source has no list_response Raw document")
    latest_response = max(
        list_responses,
        key=lambda document: (
            document.collected_at,
            document.document_id,
        ),
    )

    items = sorted(
        (
            document
            for document in documents
            if document.document_role is RawDocumentRole.LIST_ITEM
            and document.parent_document_id == latest_response.document_id
        ),
        key=lambda document: (
            document.external_id or "",
            document.document_id,
        ),
    )
    if not items:
        raise RuntimeReplayError(
            "latest list_response has no linked list_item Raw documents"
        )
    selected_items = items[:limit]
    selected_external_ids = {
        document.external_id
        for document in selected_items
        if document.external_id is not None
    }

    details_by_external_id: dict[str, RawPolicyDocument] = {}
    for document in documents:
        external_id = document.external_id
        if (
            document.document_role
            is not RawDocumentRole.DETAIL_RESPONSE
            or external_id not in selected_external_ids
            or document.collected_at < latest_response.collected_at
        ):
            continue
        current = details_by_external_id.get(external_id)
        if current is None or (
            document.collected_at,
            document.document_id,
        ) > (
            current.collected_at,
            current.document_id,
        ):
            details_by_external_id[external_id] = document

    selected_details = tuple(
        details_by_external_id[external_id]
        for external_id in sorted(details_by_external_id)
    )
    return (latest_response, *selected_items, *selected_details)


def _validation_issue(
    index: int,
    result: ValidationResult,
) -> RuntimeValidationIssue:
    error_issues = tuple(
        issue
        for issue in result.issues
        if issue.severity == "error"
    )
    provenance = result.candidate.get("provenance")
    raw_document_ids = (
        tuple(
            item["raw_document_id"]
            for item in provenance
            if isinstance(item, dict)
            and isinstance(item.get("raw_document_id"), str)
        )
        if isinstance(provenance, list)
        else ()
    )
    return RuntimeValidationIssue(
        index=index,
        source_id=_optional_string(result.candidate.get("source_id")),
        external_id=_optional_string(
            result.candidate.get("external_id")
        ),
        codes=(
            tuple(issue.code for issue in error_issues)
            or ("normalized_program_invalid",)
        ),
        paths=tuple(issue.path for issue in error_issues),
        raw_document_ids=raw_document_ids,
    )


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None
