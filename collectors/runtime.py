"""Replay stored Raw documents without making source API requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.cheonan_youthcenter import (
    SOURCE_ID as CHEONAN_YOUTHCENTER_SOURCE_ID,
    CheonanYouthCenterExtractor,
)
from collectors.cross_source_duplicate import (
    AggregatorBaseline,
    CrossSourceDecisionManifest,
    evaluate_cross_source_duplicate,
)
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.gyeongbuk_youth import (
    SOURCE_ID as GYEONGBUK_YOUTH_SOURCE_ID,
    GyeongbukYouthExtractor,
    decide_gyeongbuk_regional_policy,
    map_gyeongbuk_duplicate_evidence,
)
from collectors.regional_pilot import (
    BUSAN_SOURCE_ID,
    SEOUL_SOURCE_ID,
    BusanYouthExtractor,
    SeoulYouthExtractor,
    decide_representative_regional_policy,
    map_representative_duplicate_evidence,
)
from collectors.regional_expansion import (
    EXPANDED_CAPTURE_SOURCE_IDS,
    RegionalCheckpointStore,
    RegionalBrowserExtractor,
    decide_expanded_regional_policy,
    map_expanded_duplicate_evidence,
)
from collectors.normalized import DataQualityStatus
from collectors.normalizer import Normalizer
from collectors.raw import RawDocumentRole, RawPolicyDocument
from collectors.snapshot import (
    SnapshotError,
    SnapshotManifest,
    SnapshotManifestStore,
)
from collectors.supplemental_official import (
    SUPPLEMENTAL_SOURCE_IDS,
    SupplementalOfficialExtractor,
    decide_supplemental_policy,
    map_supplemental_duplicate_evidence,
)
from collectors.storage import RawDocumentStore, RawStorageError
from collectors.validation import ValidationResult
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID


SUPPORTED_SOURCE_IDS = (
    BOKJIRO_SOURCE_ID,
    CHEONAN_YOUTHCENTER_SOURCE_ID,
    GYEONGBUK_YOUTH_SOURCE_ID,
    BUSAN_SOURCE_ID,
    SEOUL_SOURCE_ID,
    YOUTHCENTER_SOURCE_ID,
    *tuple(sorted(EXPANDED_CAPTURE_SOURCE_IDS)),
    *tuple(sorted(SUPPLEMENTAL_SOURCE_IDS)),
)

REGIONAL_RUNTIME_SOURCE_IDS = frozenset(
    {
        GYEONGBUK_YOUTH_SOURCE_ID,
        BUSAN_SOURCE_ID,
        SEOUL_SOURCE_ID,
        *EXPANDED_CAPTURE_SOURCE_IDS,
    }
)

_EXTRACTOR_TYPES = {
    BOKJIRO_SOURCE_ID: BokjiroExtractor,
    CHEONAN_YOUTHCENTER_SOURCE_ID: CheonanYouthCenterExtractor,
    GYEONGBUK_YOUTH_SOURCE_ID: GyeongbukYouthExtractor,
    BUSAN_SOURCE_ID: BusanYouthExtractor,
    SEOUL_SOURCE_ID: SeoulYouthExtractor,
    YOUTHCENTER_SOURCE_ID: YouthCenterExtractor,
    **{
        source_id: (lambda value=source_id: RegionalBrowserExtractor(value))
        for source_id in EXPANDED_CAPTURE_SOURCE_IDS
    },
    **{
        source_id: (lambda value=source_id: SupplementalOfficialExtractor(value))
        for source_id in SUPPLEMENTAL_SOURCE_IDS
    },
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
    regional_decisions: tuple[dict[str, Any], ...] = ()
    duplicate_decisions: tuple[dict[str, Any], ...] = ()
    duplicate_baseline: dict[str, Any] | None = None
    duplicate_manifest: CrossSourceDecisionManifest | None = None
    supplemental_decisions: tuple[dict[str, Any], ...] = ()

    @property
    def accepted_count(self) -> int:
        return len(self.programs)

    @property
    def regional_skipped_count(self) -> int:
        return sum(
            not decision["accepted"]
            for decision in self.regional_decisions
        )

    @property
    def cross_source_skipped_count(self) -> int:
        return sum(
            not decision["accepted"]
            for decision in self.duplicate_decisions
        )


def replay_runtime_raw(
    *,
    raw_root: str | Path,
    source_id: str,
    limit: int,
    snapshot_id: str | None = None,
    normalizer: Normalizer | None = None,
    duplicate_baseline: AggregatorBaseline | None = None,
    checkpoint_root: str | Path | None = None,
) -> RuntimeReplayResult:
    """Load the latest source batch and normalize its policies."""
    if source_id not in _EXTRACTOR_TYPES:
        raise RuntimeReplayError("unsupported runtime source")
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 5000
    ):
        raise RuntimeReplayError("limit must be an integer from 1 to 5000")

    documents = _load_source_documents(raw_root, source_id)
    try:
        manifest_store = SnapshotManifestStore(raw_root)
        manifest = (
            manifest_store.load(source_id, snapshot_id)
            if snapshot_id is not None
            else manifest_store.latest(source_id)
        )
    except SnapshotError as exc:
        raise RuntimeReplayError(str(exc)) from None
    checkpoint = (
        RegionalCheckpointStore(checkpoint_root).load(source_id)
        if checkpoint_root is not None
        and source_id in REGIONAL_RUNTIME_SOURCE_IDS
        else None
    )
    selected_documents = (
        _checkpoint_batch(documents, checkpoint, limit)
        if checkpoint is not None
        else _snapshot_batch(documents, manifest, limit)
        if manifest is not None
        else _latest_batch(documents, limit)
    )
    browser_checkpoint_replay = (
        checkpoint is not None and source_id == SEOUL_SOURCE_ID
    )
    extractor = (
        RegionalBrowserExtractor(source_id)
        if browser_checkpoint_replay
        else _EXTRACTOR_TYPES[source_id]()
    )
    try:
        extracted = extractor.extract(selected_documents)
    except Exception as exc:
        raise RuntimeReplayError(
            f"runtime extraction failed ({type(exc).__name__}: {exc})"
        ) from None

    regional_decisions = ()
    supplemental_decisions = ()
    policies = extracted
    regional_deciders = {
        GYEONGBUK_YOUTH_SOURCE_ID: decide_gyeongbuk_regional_policy,
        BUSAN_SOURCE_ID: decide_representative_regional_policy,
        SEOUL_SOURCE_ID: decide_representative_regional_policy,
        **{
            source_id: decide_expanded_regional_policy
            for source_id in EXPANDED_CAPTURE_SOURCE_IDS
        },
    }
    selected_regional_decider = (
        decide_expanded_regional_policy
        if browser_checkpoint_replay
        else regional_deciders.get(source_id)
    )
    if selected_regional_decider is not None:
        decisions = tuple(
            selected_regional_decider(policy)
            for policy in extracted
        )
        regional_decisions = tuple(
            decision.to_dict() for decision in decisions
        )
        policies = tuple(
            decision.accepted_policy
            for decision in decisions
            if decision.accepted_policy is not None
        )
    if source_id in SUPPLEMENTAL_SOURCE_IDS:
        decisions = tuple(
            decide_supplemental_policy(policy) for policy in extracted
        )
        supplemental_decisions = tuple(
            decision.to_dict() for decision in decisions
        )
        policies = tuple(
            decision.accepted_policy
            for decision in decisions
            if decision.accepted_policy is not None
        )

    selected_normalizer = normalizer or Normalizer()
    policy_results = tuple(
        (policy, selected_normalizer.normalize(policy))
        for policy in policies
    )
    results = tuple(result for _, result in policy_results)
    normalized_pairs = tuple(
        (policy, result)
        for policy, result in policy_results
        if result.program is not None
    )
    accepted_results = tuple(
        result for result in results if result.program is not None
    )
    duplicate_decisions = ()
    duplicate_manifest = None
    duplicate_mappers = {
        GYEONGBUK_YOUTH_SOURCE_ID: map_gyeongbuk_duplicate_evidence,
        BUSAN_SOURCE_ID: map_representative_duplicate_evidence,
        SEOUL_SOURCE_ID: map_representative_duplicate_evidence,
        **{
            source_id: map_expanded_duplicate_evidence
            for source_id in EXPANDED_CAPTURE_SOURCE_IDS
        },
        **{
            source_id: map_supplemental_duplicate_evidence
            for source_id in SUPPLEMENTAL_SOURCE_IDS
        },
    }
    selected_duplicate_mapper = (
        map_expanded_duplicate_evidence
        if browser_checkpoint_replay
        else duplicate_mappers.get(source_id)
    )
    if selected_duplicate_mapper is not None:
        decisions = tuple(
            evaluate_cross_source_duplicate(
                result.program,
                selected_duplicate_mapper(policy),
                duplicate_baseline,
            )
            for policy, result in normalized_pairs
            if result.program is not None
        )
        duplicate_decisions = tuple(
            decision.to_dict() for decision in decisions
        )
        if decisions and duplicate_baseline is not None:
            duplicate_manifest = CrossSourceDecisionManifest(
                source_id=source_id,
                baseline=duplicate_baseline,
                decisions=decisions,
            )
        accepted_results = tuple(
            result
            for (_, result), decision in zip(
                normalized_pairs, decisions, strict=True
            )
            if decision.accepted
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
        regional_decisions=regional_decisions,
        duplicate_decisions=duplicate_decisions,
        duplicate_baseline=(
            duplicate_baseline.to_dict()
            if duplicate_decisions and duplicate_baseline is not None
            else None
        ),
        duplicate_manifest=duplicate_manifest,
        supplemental_decisions=supplemental_decisions,
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


def _checkpoint_batch(
    documents: tuple[RawPolicyDocument, ...],
    checkpoint: Any,
    limit: int,
) -> tuple[RawPolicyDocument, ...]:
    """Select the latest complete Raw triple for every captured checkpoint ID."""

    if not checkpoint.captured_ids:
        raise RuntimeReplayError("regional checkpoint has no captured details")
    selected_ids = checkpoint.captured_ids[:limit]
    selected_set = set(selected_ids)
    responses = {
        document.document_id: document
        for document in documents
        if document.document_role is RawDocumentRole.LIST_RESPONSE
    }

    def newest(
        role: RawDocumentRole,
    ) -> dict[str, RawPolicyDocument]:
        values: dict[str, RawPolicyDocument] = {}
        for document in documents:
            external_id = document.external_id
            if document.document_role is not role or external_id not in selected_set:
                continue
            current = values.get(external_id)
            if current is None or (
                document.collected_at,
                document.document_id,
            ) > (current.collected_at, current.document_id):
                values[external_id] = document
        return values

    items = newest(RawDocumentRole.LIST_ITEM)
    details = newest(RawDocumentRole.DETAIL_RESPONSE)
    if set(items) != selected_set or set(details) != selected_set:
        raise RuntimeReplayError(
            "regional checkpoint Raw details are incomplete"
        )
    parents: dict[str, RawPolicyDocument] = {}
    for item in items.values():
        parent_id = item.parent_document_id
        if parent_id is None or parent_id not in responses:
            raise RuntimeReplayError(
                "regional checkpoint list parent is missing"
            )
        parents[parent_id] = responses[parent_id]
    ordered_items = tuple(items[external_id] for external_id in selected_ids)
    ordered_details = tuple(details[external_id] for external_id in selected_ids)
    return (*parents.values(), *ordered_items, *ordered_details)


def _snapshot_batch(
    documents: tuple[RawPolicyDocument, ...],
    manifest: SnapshotManifest,
    limit: int,
) -> tuple[RawPolicyDocument, ...]:
    documents_by_id = {
        document.document_id: document for document in documents
    }
    try:
        list_responses = tuple(
            documents_by_id[document_id]
            for document_id in manifest.list_response_document_ids
        )
        manifest_details = tuple(
            documents_by_id[document_id]
            for document_id in manifest.detail_document_ids
        )
    except KeyError:
        raise RuntimeReplayError(
            "snapshot references a missing Raw document"
        ) from None
    if any(
        document.document_role is not RawDocumentRole.LIST_RESPONSE
        for document in list_responses
    ) or any(
        document.document_role is not RawDocumentRole.DETAIL_RESPONSE
        for document in manifest_details
    ):
        raise RuntimeReplayError("snapshot document roles do not match")

    response_order = {
        document.document_id: index
        for index, document in enumerate(list_responses)
    }
    items = sorted(
        (
            document
            for document in documents
            if document.document_role is RawDocumentRole.LIST_ITEM
            and document.parent_document_id in response_order
        ),
        key=lambda document: (
            response_order[document.parent_document_id or ""],
            document.external_id or "",
            document.document_id,
        ),
    )
    external_ids = [document.external_id for document in items]
    if (
        len(items) != manifest.item_count
        or any(external_id is None for external_id in external_ids)
        or len(set(external_ids)) != len(external_ids)
    ):
        raise RuntimeReplayError("snapshot list items are incomplete or duplicate")

    selected_items = tuple(items[:limit])
    selected_external_ids = {
        document.external_id for document in selected_items
    }
    selected_details = tuple(
        document
        for document in manifest_details
        if document.external_id in selected_external_ids
    )
    return (*list_responses, *selected_items, *selected_details)


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
