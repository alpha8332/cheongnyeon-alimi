"""RYP6 regional Browser capture and resumable decision checkpoints."""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.parse
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from collectors.base import CollectionResult
from collectors.cross_source_duplicate import DuplicateEvidence
from collectors.errors import CollectorConfigurationError
from collectors.extracted import ExtractedPolicy, ExtractionError, SourceProvenance
from collectors.http import TransportResponse
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
    utc_now,
)
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalPolicyDecision,
    RegionalPolicyEvidence,
    RegionalityStatus,
    enforce_youth_target,
    evaluate_regional_policy,
)
from collectors.regional_profile import load_approved_regional_profile
from collectors.source_common import response_content_type
from collectors.storage import RawDocumentStore


CAPTURE_VERSION = "regional-browser-capture/1.0"
_EXTERNAL_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_DETAIL_FIELDS = (
    "title",
    "organization",
    "category",
    "application_period",
    "source_region",
    "eligibility",
    "support_content",
    "application_method",
    "contact",
    "required_documents",
    "exclusions",
    "age",
)
_OBSERVABLE_DETAIL_FIELDS = tuple(
    value for value in _DETAIL_FIELDS if value != "title"
)
_CAPTURE_TO_EVIDENCE_FIELD = {
    "organization": "implementing_organization_text",
    "eligibility": "region_eligibility_text",
    "application_method": "application_channel_text",
    "support_content": "additional_benefit_text",
    "source_region": "source_region_text",
    "application_period": "application_period_text",
}


@dataclass(frozen=True, slots=True)
class RegionalExpansionSpec:
    source_name: str
    expected_region_text: str
    identity_query: str | None = None
    identity_path: bool = False
    request_identity: bool = False


class RegionalPaginationTermination(str, Enum):
    """Authoritative condition used to finish one approved Source traversal."""

    REPORTED_TOTAL = "reported_total"
    LAST_PAGE = "last_page"
    NEXT_ABSENT = "next_absent"


@dataclass(frozen=True, slots=True)
class RegionalPaginationSpec:
    """Operational pagination scope, separate from the bounded RYP1 pilot."""

    page_parameter: str
    page_size: int | None
    safety_max_pages: int
    termination: RegionalPaginationTermination
    scope: str = "full_list"
    fixed_parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if (
            not self.page_parameter
            or self.page_size is not None
            and self.page_size < 1
            or self.safety_max_pages < 1
            or self.scope not in {"full_list", "official_current_filter"}
            or len(self.fixed_parameters) != len(dict(self.fixed_parameters))
        ):
            raise ValueError("regional pagination specification is invalid")

    def validate_page(
        self,
        *,
        page: int,
        discovered_count: int,
        total_count: int | None,
        has_next: bool,
    ) -> None:
        """Reject premature or unbounded termination claims."""

        if page > self.safety_max_pages or (
            has_next and page == self.safety_max_pages
        ):
            raise ExtractionError("regional pagination safety limit reached")
        if discovered_count < 1:
            raise ExtractionError("regional pagination page is empty")
        if self.page_size is not None and discovered_count > self.page_size:
            raise ExtractionError(
                "regional pagination page size drifted: "
                f"observed={discovered_count} allowed={self.page_size}"
            )
        if self.termination is RegionalPaginationTermination.REPORTED_TOTAL:
            if total_count is None:
                raise ExtractionError("regional pagination total is required")
            if not has_next and discovered_count > total_count:
                raise ExtractionError("regional pagination total drifted")


REGIONAL_EXPANSION_SPECS: dict[str, RegionalExpansionSpec] = {
    "regional-seoul-youth-platform": RegionalExpansionSpec(
        "청년몽땅정보통", "서울특별시", "plcyBizId"
    ),
    "regional-busan-youth-platform": RegionalExpansionSpec(
        "부산청년플랫폼", "부산광역시", "bizSid"
    ),
    "regional-daegu-youth-platform": RegionalExpansionSpec(
        "대구청년커뮤니티포털 젊프", "대구광역시", "ap_seq"
    ),
    "regional-incheon-youth-platform": RegionalExpansionSpec(
        "인천유스톡톡", "인천광역시", "poly_seq"
    ),
    "regional-gwangju-integrated-youth-platform": RegionalExpansionSpec(
        "전남광주통합특별시 청년정책플랫폼",
        "전남광주통합특별시",
        "policyId",
    ),
    "regional-daejeon-youth-platform": RegionalExpansionSpec(
        "대전청년포털", "대전광역시", identity_path=True
    ),
    "regional-ulsan-youth-platform": RegionalExpansionSpec(
        "울산청년정책플랫폼", "울산광역시", "dataId"
    ),
    "regional-gangwon-youth-platform": RegionalExpansionSpec(
        "강원청년포털", "강원특별자치도", request_identity=True
    ),
    "regional-chungbuk-youth-platform": RegionalExpansionSpec(
        "충청북도 청년포털", "충청북도", "nttNo"
    ),
    "regional-jeonbuk-youth-platform": RegionalExpansionSpec(
        "전북청년허브", "전북특별자치도", "id"
    ),
    "regional-gyeongbuk-youth-platform": RegionalExpansionSpec(
        "경북청년포털", "경상북도", "no"
    ),
    "regional-gyeongnam-youth-platform": RegionalExpansionSpec(
        "경남청년정보플랫폼", "경상남도", "policy_no"
    ),
    "regional-jeju-youth-platform": RegionalExpansionSpec(
        "제주청년센터", "제주특별자치도", "wr_id"
    ),
}


# These are operational safety/termination contracts, not the one-page RYP1
# discovery budgets retained in the Source inventory.  Counts are deliberately
# not frozen because public lists change; a run reconciles its observed total in
# RegionalBatchCheckpoint.
REGIONAL_PAGINATION_SPECS: dict[str, RegionalPaginationSpec] = {
    "regional-seoul-youth-platform": RegionalPaginationSpec(
        "pageIndex", 5, 80, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-busan-youth-platform": RegionalPaginationSpec(
        "pageIndex",
        12,
        30,
        RegionalPaginationTermination.REPORTED_TOTAL,
        scope="official_current_filter",
        fixed_parameters=(("endstat", "Y"),),
    ),
    "regional-daegu-youth-platform": RegionalPaginationSpec(
        "page",
        None,
        200,
        RegionalPaginationTermination.NEXT_ABSENT,
        scope="official_current_filter",
        fixed_parameters=(("search_flag", "1"),),
    ),
    "regional-incheon-youth-platform": RegionalPaginationSpec(
        "pgno",
        10,
        50,
        RegionalPaginationTermination.REPORTED_TOTAL,
        scope="official_current_filter",
        fixed_parameters=(("acptrun", "ing"),),
    ),
    "regional-gwangju-integrated-youth-platform": RegionalPaginationSpec(
        "pageIndex",
        10,
        100,
        RegionalPaginationTermination.REPORTED_TOTAL,
        scope="official_current_filter",
        fixed_parameters=(("status", "ing"),),
    ),
    "regional-daejeon-youth-platform": RegionalPaginationSpec(
        "pageIndex", 10, 20, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-ulsan-youth-platform": RegionalPaginationSpec(
        "page", 11, 100, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-gangwon-youth-platform": RegionalPaginationSpec(
        "pageIndex", 12, 100, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-chungbuk-youth-platform": RegionalPaginationSpec(
        "pageIndex", 10, 100, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-jeonbuk-youth-platform": RegionalPaginationSpec(
        "offset",
        12,
        100,
        RegionalPaginationTermination.LAST_PAGE,
        scope="official_current_filter",
        fixed_parameters=(("strstate", "ing"),),
    ),
    "regional-gyeongbuk-youth-platform": RegionalPaginationSpec(
        "pageIndex",
        9,
        30,
        RegionalPaginationTermination.REPORTED_TOTAL,
        scope="official_current_filter",
        fixed_parameters=(("searchAplyPeriod", "1"),),
    ),
    "regional-gyeongnam-youth-platform": RegionalPaginationSpec(
        "page_no", 9, 250, RegionalPaginationTermination.REPORTED_TOTAL
    ),
    "regional-jeju-youth-platform": RegionalPaginationSpec(
        "page", None, 200, RegionalPaginationTermination.LAST_PAGE
    ),
}

EXPANDED_CAPTURE_SOURCE_IDS = frozenset(
    set(REGIONAL_EXPANSION_SPECS)
    - {
        "regional-seoul-youth-platform",
        "regional-busan-youth-platform",
        "regional-gyeongbuk-youth-platform",
    }
)


class RegionalBrowserCaptureStore:
    """Validate actual Browser observations and persist replayable Raw."""

    def __init__(
        self,
        source_id: str,
        *,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        try:
            self._spec = REGIONAL_EXPANSION_SPECS[source_id]
        except KeyError:
            raise CollectorConfigurationError(
                "regional Browser capture source is unsupported"
            ) from None
        self.source_id = source_id
        self._profile = load_approved_regional_profile(source_id)
        self._store = store or RawDocumentStore()
        self._now = now

    def save(self, capture: Mapping[str, Any]) -> CollectionResult:
        page, total_count, has_next, discovered_ids, items = self._validate(
            capture
        )
        collected_at = self._now()
        list_payload = {
            "capture_mode": "browser",
            "list_url": capture["list_url"],
            "action_trace": deepcopy(capture["action_trace"]),
            "page": page,
            "total_count": total_count,
            "has_next": has_next,
            "discovered_ids": list(discovered_ids),
            "discovered_count": len(discovered_ids),
            "captured_detail_count": len(items),
        }
        list_response = _json_response(list_payload)
        list_document = _raw(
            source_id=self.source_id,
            response=list_response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=_queryless_url(str(capture["list_url"])),
            payload=list_response.body,
            collected_at=collected_at,
        )
        documents = [list_document]
        detail_document_ids: list[str] = []
        for value in items:
            item = deepcopy(value)
            detail = item.pop("detail")
            external_id = item["external_id"]
            item_response = _json_response(item)
            documents.append(
                _raw(
                    source_id=self.source_id,
                    response=item_response,
                    role=RawDocumentRole.LIST_ITEM,
                    external_id=external_id,
                    parent_document_id=list_document.document_id,
                    source_url=_queryless_url(str(capture["list_url"])),
                    payload=item_response.body,
                    collected_at=collected_at,
                )
            )
            detail_response = _json_response(detail)
            detail_document = _raw(
                source_id=self.source_id,
                response=detail_response,
                role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=external_id,
                parent_document_id=None,
                source_url=_queryless_url(item["detail_url"]),
                payload=detail_response.body,
                collected_at=collected_at,
            )
            documents.append(detail_document)
            detail_document_ids.append(detail_document.document_id)
        stored_paths: list[Path] = []
        try:
            for document in documents:
                stored_paths.append(self._store.save(document))
        except Exception:
            self._remove_created_raw(stored_paths)
            raise
        paths = tuple(stored_paths)
        return CollectionResult(
            source_id=self.source_id,
            request_count=0,
            item_count=len(items),
            detail_count=len(items),
            stored_paths=paths,
            page=page,
            page_size=len(items),
            total_count=total_count,
            external_ids=tuple(item["external_id"] for item in items),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_document_ids),
        )

    def checkpoint_metadata(
        self, capture: Mapping[str, Any]
    ) -> tuple[int, int | None, bool, tuple[str, ...]]:
        """Validate a capture and return its complete list-page identity set."""

        page, total_count, has_next, discovered_ids, _ = self._validate(
            capture
        )
        return page, total_count, has_next, discovered_ids

    def remove_result(self, result: CollectionResult) -> None:
        """Remove only Raw files created by one failed CLI transaction."""

        self._remove_created_raw(list(result.stored_paths))

    def _remove_created_raw(self, paths: list[Path]) -> None:
        for path in reversed(paths):
            path.unlink(missing_ok=True)
            parent = path.parent
            while parent != self._store.root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent

    def _validate(
        self, capture: Mapping[str, Any]
    ) -> tuple[
        int,
        int | None,
        bool,
        tuple[str, ...],
        tuple[dict[str, Any], ...],
    ]:
        if capture.get("source_id") != self.source_id:
            raise ExtractionError("regional Browser capture source drift")
        list_url = capture.get("list_url")
        if not _matches_list_url(list_url, self._profile.approved_list_urls):
            raise ExtractionError("regional Browser list URL is not approved")
        page = capture.get("page")
        total_count = capture.get("total_count")
        has_next = capture.get("has_next")
        trace = capture.get("action_trace")
        items = capture.get("items")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or page < 1
            or (
                total_count is not None
                and (
                    not isinstance(total_count, int)
                    or isinstance(total_count, bool)
                    or total_count < 0
                )
            )
            or not isinstance(has_next, bool)
            or not isinstance(trace, list)
            or not 1 <= len(trace) <= 30
            or not all(isinstance(value, str) and value.strip() for value in trace)
            or not isinstance(items, list)
            or not 1 <= len(items) <= self._profile.request_budget.max_detail_requests
        ):
            raise ExtractionError("regional Browser capture is incomplete")
        seen: set[str] = set()
        validated: list[dict[str, Any]] = []
        for value in items:
            if not isinstance(value, dict):
                raise ExtractionError("regional Browser item is invalid")
            external_id = value.get("external_id")
            title = _text(value.get("title"))
            detail = value.get("detail")
            if (
                not isinstance(external_id, str)
                or not _EXTERNAL_ID.fullmatch(external_id)
                or external_id in seen
                or title is None
                or not isinstance(detail, dict)
                or set(_DETAIL_FIELDS) - set(detail)
                or _text(detail.get("title")) != title
                or not _matches_detail_identity(
                    value.get("detail_url"),
                    value.get("request_identity"),
                    external_id,
                    self._profile.approved_detail_url_patterns,
                    self._spec,
                )
                or any(
                    detail.get(field) is not None
                    and _text(detail.get(field)) is None
                    for field in _DETAIL_FIELDS
                )
                or not _valid_detail_observations(detail)
            ):
                raise ExtractionError("regional Browser item contract drift")
            seen.add(external_id)
            validated.append(deepcopy(value))
        discovered_value = capture.get("discovered_ids")
        if discovered_value is None:
            discovered_ids = tuple(item["external_id"] for item in validated)
        elif (
            not isinstance(discovered_value, list)
            or not discovered_value
            or not all(
                isinstance(value, str) and _EXTERNAL_ID.fullmatch(value)
                for value in discovered_value
            )
            or len(discovered_value) != len(set(discovered_value))
        ):
            raise ExtractionError(
                "regional Browser discovered identities are invalid"
            )
        else:
            discovered_ids = tuple(discovered_value)
        if not seen.issubset(discovered_ids):
            raise ExtractionError(
                "regional Browser detail is absent from discovered identities"
            )
        if total_count is not None and total_count < len(discovered_ids):
            raise ExtractionError(
                "regional Browser total is smaller than discovered identities"
            )
        try:
            pagination = REGIONAL_PAGINATION_SPECS[self.source_id]
        except KeyError:
            raise ExtractionError(
                "regional pagination contract is missing"
            ) from None
        pagination.validate_page(
            page=page,
            discovered_count=len(discovered_ids),
            total_count=total_count,
            has_next=has_next,
        )
        return page, total_count, has_next, discovered_ids, tuple(validated)


class RegionalBrowserExtractor:
    def __init__(self, source_id: str) -> None:
        try:
            self._spec = REGIONAL_EXPANSION_SPECS[source_id]
        except KeyError:
            raise ExtractionError("regional Browser extractor is unsupported") from None
        self.source_id = source_id
        self._profile = load_approved_regional_profile(source_id)

    def extract(
        self, documents: Iterable[RawPolicyDocument]
    ) -> tuple[ExtractedPolicy, ...]:
        selected = tuple(documents)
        if not selected or any(value.source_id != self.source_id for value in selected):
            raise ExtractionError("regional Browser Raw source drift")
        parents = {
            value.document_id: value
            for value in selected
            if value.document_role is RawDocumentRole.LIST_RESPONSE
            and _matches_list_url(
                _json_document(value).get("list_url"),
                self._profile.approved_list_urls,
            )
        }
        items = [
            value for value in selected if value.document_role is RawDocumentRole.LIST_ITEM
        ]
        details = {
            value.external_id: value
            for value in selected
            if value.document_role is RawDocumentRole.DETAIL_RESPONSE
        }
        if not parents or not items or len(details) != len(items):
            raise ExtractionError("regional Browser Raw batch is incomplete")
        policies: list[ExtractedPolicy] = []
        seen: set[str] = set()
        for item_document in items:
            item = _json_document(item_document)
            external_id = _text(item.get("external_id"))
            detail_document = details.get(external_id)
            if (
                external_id is None
                or external_id != item_document.external_id
                or external_id in seen
                or item_document.parent_document_id not in parents
                or detail_document is None
            ):
                raise ExtractionError("regional Browser Raw identity drift")
            seen.add(external_id)
            detail = _json_document(detail_document)
            if _text(item.get("title")) != _text(detail.get("title")):
                raise ExtractionError("regional Browser detail title drift")
            provenance_documents = (
                parents[item_document.parent_document_id],
                item_document,
                detail_document,
            )
            provenance = tuple(
                SourceProvenance.from_raw(value) for value in provenance_documents
            )
            policies.append(
                ExtractedPolicy(
                    source_id=self.source_id,
                    source_name=self._spec.source_name,
                    external_id=external_id,
                    title=_text(detail.get("title")),
                    organization=_text(detail.get("organization")),
                    summary=_text(item.get("summary")),
                    category_text=_text(detail.get("category"))
                    or _text(item.get("category")),
                    application_period_text=_text(detail.get("application_period")),
                    region_text=_text(detail.get("source_region")),
                    age_text=_text(detail.get("age")),
                    eligibility_text=_text(detail.get("eligibility")),
                    support_content=_text(detail.get("support_content")),
                    application_method=_text(detail.get("application_method")),
                    source_url=str(item["detail_url"]),
                    collected_at=max(value.collected_at for value in provenance),
                    provenance=provenance,
                    extra={
                        "selector_contract": CAPTURE_VERSION,
                        "source_fields": {
                            "list_item": deepcopy(item),
                            "detail_response": deepcopy(detail),
                        },
                        "institutional_contact": _text(detail.get("contact")),
                        "required_documents": _text(detail.get("required_documents")),
                        "exclusion_conditions": _text(detail.get("exclusions")),
                    },
                )
            )
        if set(details) != seen:
            raise ExtractionError("regional Browser Raw has orphan detail")
        return tuple(policies)


def decide_expanded_regional_policy(
    policy: ExtractedPolicy, *, as_of: date | None = None
) -> RegionalPolicyDecision:
    try:
        spec = REGIONAL_EXPANSION_SPECS[policy.source_id]
    except KeyError:
        raise ExtractionError("expanded regional decision source is unsupported") from None
    source_fields = policy.extra.get("source_fields")
    detail = (
        source_fields.get("detail_response")
        if isinstance(source_fields, Mapping)
        else None
    )
    if not isinstance(detail, Mapping):
        raise ExtractionError("expanded regional detail evidence is missing")
    values = {
        "implementing_organization_text": policy.organization,
        "region_eligibility_text": policy.eligibility_text,
        "application_channel_text": policy.application_method,
        "additional_benefit_text": policy.support_content,
        "source_region_text": policy.region_text,
        "application_period_text": policy.application_period_text,
    }
    evidence = RegionalPolicyEvidence(
        **values,
        field_locators=tuple(
            (name, f"detail:{name}")
            for name, value in values.items()
            if value is not None
        ),
        provenance=policy.provenance,
        field_observations=_regional_field_observations(detail),
    )
    decision = evaluate_regional_policy(
        policy,
        evidence,
        expected_region_text=spec.expected_region_text,
        as_of=as_of,
    )
    return enforce_youth_target(policy, decision)


def _regional_field_observations(
    detail: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    observations = detail.get("evidence_observations")
    if not isinstance(observations, Mapping):
        return ()
    selected: list[tuple[str, str]] = []
    for capture_field, evidence_field in _CAPTURE_TO_EVIDENCE_FIELD.items():
        observation = observations.get(capture_field)
        if not isinstance(observation, Mapping):
            continue
        status = observation.get("status")
        if isinstance(status, str):
            selected.append((evidence_field, status))
    return tuple(selected)


def _valid_detail_observations(detail: Mapping[str, Any]) -> bool:
    observations = detail.get("evidence_observations")
    if observations is None:
        return True
    if (
        not isinstance(observations, Mapping)
        or set(observations) != set(_OBSERVABLE_DETAIL_FIELDS)
    ):
        return False
    for field_name in _OBSERVABLE_DETAIL_FIELDS:
        observation = observations[field_name]
        if not isinstance(observation, Mapping):
            return False
        status = observation.get("status")
        label = observation.get("label")
        if (
            status
            not in {
                "value_extracted",
                "label_present_value_empty",
                "label_not_found",
            }
            or label is not None
            and (not isinstance(label, str) or not label.strip())
            or (status == "value_extracted")
            != (detail.get(field_name) is not None)
            or (status == "label_not_found") != (label is None)
        ):
            return False
    return True


def map_expanded_duplicate_evidence(policy: ExtractedPolicy) -> DuplicateEvidence:
    if policy.source_id not in REGIONAL_EXPANSION_SPECS:
        raise ExtractionError("expanded duplicate source is unsupported")
    urls = [policy.source_url]
    if policy.application_method and policy.application_method.startswith(
        ("http://", "https://")
    ):
        urls.append(policy.application_method)
    return DuplicateEvidence(
        canonical_urls=tuple(urls),
        field_locators=(("canonical_urls", "detail:canonical_urls"),),
        provenance=policy.provenance,
    )


class RegionalOutcome(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    REVIEW = "review"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RegionalBatchCheckpoint:
    source_id: str
    collection_mode: str
    next_page: int
    total_count: int | None
    discovery_complete: bool
    complete: bool
    discovered_ids: tuple[str, ...] = ()
    captured_ids: tuple[str, ...] = ()
    decisions: tuple[tuple[str, RegionalOutcome], ...] = ()

    def __post_init__(self) -> None:
        if self.source_id not in REGIONAL_EXPANSION_SPECS:
            raise ValueError("regional checkpoint source is unsupported")
        profile = load_approved_regional_profile(self.source_id)
        if (
            self.collection_mode != profile.collection_mode
            or not isinstance(self.next_page, int)
            or isinstance(self.next_page, bool)
            or self.next_page < 1
            or (
                self.total_count is not None
                and (
                    not isinstance(self.total_count, int)
                    or isinstance(self.total_count, bool)
                    or self.total_count < 0
                )
            )
            or not isinstance(self.discovery_complete, bool)
            or not isinstance(self.complete, bool)
        ):
            raise ValueError("regional checkpoint state is invalid")
        discovered = self.discovered_ids
        if (
            len(discovered) != len(set(discovered))
            or any(not _EXTERNAL_ID.fullmatch(value) for value in discovered)
        ):
            raise ValueError("regional checkpoint identities are invalid")
        decision_ids = tuple(external_id for external_id, _ in self.decisions)
        nonfailed_decision_ids = {
            external_id
            for external_id, outcome in self.decisions
            if outcome is not RegionalOutcome.FAILED
        }
        if (
            len(self.captured_ids) != len(set(self.captured_ids))
            or set(self.captured_ids) - set(discovered)
            or any(
                not _EXTERNAL_ID.fullmatch(value)
                for value in self.captured_ids
            )
            or set(decision_ids) - set(discovered)
            or nonfailed_decision_ids - set(self.captured_ids)
            or len(decision_ids) != len(set(decision_ids))
            or any(not isinstance(outcome, RegionalOutcome) for _, outcome in self.decisions)
        ):
            raise ValueError("regional checkpoint decisions are invalid")
        if self.total_count is not None and len(discovered) > self.total_count:
            raise ValueError("regional checkpoint total is too small")
        if (
            self.discovery_complete
            and self.total_count is not None
            and len(discovered) != self.total_count
        ):
            raise ValueError("regional checkpoint total is not reconciled")
        expected_complete = self.discovery_complete and len(self.decisions) == len(
            discovered
        )
        if self.complete != expected_complete:
            raise ValueError("regional checkpoint completion state drifted")

    @classmethod
    def initial(cls, source_id: str) -> "RegionalBatchCheckpoint":
        profile = load_approved_regional_profile(source_id)
        return cls(
            source_id=source_id,
            collection_mode=profile.collection_mode,
            next_page=1,
            total_count=None,
            discovery_complete=False,
            complete=False,
        )

    def discover(
        self,
        *,
        page: int,
        external_ids: Iterable[str],
        total_count: int | None,
        has_next: bool,
    ) -> "RegionalBatchCheckpoint":
        ids = tuple(external_ids)
        if (
            self.discovery_complete
            or page != self.next_page
            or not ids
            or len(ids) != len(set(ids))
            or any(not _EXTERNAL_ID.fullmatch(value) for value in ids)
        ):
            raise ValueError("regional checkpoint discovery page is invalid")
        new_ids = tuple(
            external_id
            for external_id in ids
            if external_id not in set(self.discovered_ids)
        )
        if has_next and not new_ids:
            raise ValueError("regional checkpoint discovery made no progress")
        known_total = self.total_count
        discovered = (*self.discovered_ids, *new_ids)
        if total_count is not None:
            if total_count < len(discovered):
                raise ValueError("regional checkpoint total is too small")
            if known_total is not None and known_total != total_count:
                raise ValueError("regional checkpoint total drifted")
            known_total = total_count
        discovery_complete = not has_next
        if (
            discovery_complete
            and known_total is not None
            and len(discovered) != known_total
        ):
            raise ValueError("regional checkpoint discovery ended before total")
        return RegionalBatchCheckpoint(
            source_id=self.source_id,
            collection_mode=self.collection_mode,
            next_page=page + 1,
            total_count=known_total,
            discovery_complete=discovery_complete,
            complete=discovery_complete
            and len(self.decisions) == len(discovered),
            discovered_ids=discovered,
            captured_ids=self.captured_ids,
            decisions=self.decisions,
        )

    def capture(self, external_ids: Iterable[str]) -> "RegionalBatchCheckpoint":
        """Record a successfully persisted bounded detail batch."""

        selected = tuple(external_ids)
        existing = set(self.captured_ids)
        if (
            not selected
            or len(selected) != len(set(selected))
            or set(selected) - set(self.discovered_ids)
            or set(selected) & existing
        ):
            raise ValueError("regional checkpoint capture batch is invalid")
        captured = (
            *self.captured_ids,
            *(
                external_id
                for external_id in self.discovered_ids
                if external_id in set(selected)
            ),
        )
        return RegionalBatchCheckpoint(
            source_id=self.source_id,
            collection_mode=self.collection_mode,
            next_page=self.next_page,
            total_count=self.total_count,
            discovery_complete=self.discovery_complete,
            complete=self.discovery_complete
            and len(self.decisions) == len(self.discovered_ids),
            discovered_ids=self.discovered_ids,
            captured_ids=captured,
            decisions=self.decisions,
        )

    def amend_discovery(
        self,
        *,
        page: int,
        external_ids: Iterable[str],
        total_count: int | None,
        has_next: bool,
    ) -> "RegionalBatchCheckpoint":
        """Add identities missed on the most recently persisted open page."""

        ids = tuple(external_ids)
        existing = set(self.discovered_ids)
        new_ids = tuple(value for value in ids if value not in existing)
        if (
            self.discovery_complete
            or page != self.next_page - 1
            or not has_next
            or not ids
            or len(ids) != len(set(ids))
            or any(not _EXTERNAL_ID.fullmatch(value) for value in ids)
            or not new_ids
            or total_count != self.total_count
        ):
            raise ValueError("regional checkpoint discovery amendment is invalid")
        discovered = (*self.discovered_ids, *new_ids)
        if self.total_count is not None and len(discovered) > self.total_count:
            raise ValueError("regional checkpoint total is too small")
        return RegionalBatchCheckpoint(
            source_id=self.source_id,
            collection_mode=self.collection_mode,
            next_page=self.next_page,
            total_count=self.total_count,
            discovery_complete=False,
            complete=False,
            discovered_ids=discovered,
            captured_ids=self.captured_ids,
            decisions=self.decisions,
        )

    def decide(
        self, outcomes: Mapping[str, RegionalOutcome | str]
    ) -> "RegionalBatchCheckpoint":
        if not outcomes:
            raise ValueError("regional checkpoint decisions cannot be empty")
        existing = dict(self.decisions)
        if set(outcomes) - set(self.discovered_ids) or set(outcomes) & set(existing):
            raise ValueError("regional checkpoint decision identity is invalid")
        normalized: dict[str, RegionalOutcome] = {}
        try:
            for external_id, outcome in outcomes.items():
                normalized[external_id] = RegionalOutcome(outcome)
        except (TypeError, ValueError):
            raise ValueError("regional checkpoint outcome is invalid") from None
        if any(
            outcome is not RegionalOutcome.FAILED
            and external_id not in set(self.captured_ids)
            for external_id, outcome in normalized.items()
        ):
            raise ValueError("regional checkpoint decision requires captured detail")
        merged = (
            *self.decisions,
            *(
                (external_id, normalized[external_id])
                for external_id in self.discovered_ids
                if external_id in normalized
            ),
        )
        return RegionalBatchCheckpoint(
            source_id=self.source_id,
            collection_mode=self.collection_mode,
            next_page=self.next_page,
            total_count=self.total_count,
            discovery_complete=self.discovery_complete,
            complete=self.discovery_complete
            and len(merged) == len(self.discovered_ids),
            discovered_ids=self.discovered_ids,
            captured_ids=self.captured_ids,
            decisions=merged,
        )

    def advance(
        self,
        *,
        page: int,
        external_ids: Iterable[str],
        outcomes: Mapping[str, RegionalOutcome | str],
        total_count: int | None,
        has_next: bool,
    ) -> "RegionalBatchCheckpoint":
        ids = tuple(external_ids)
        if self.complete:
            raise ValueError("regional checkpoint is already complete")
        if set(ids) != set(outcomes):
            raise ValueError("every discovered regional identity needs one outcome")
        return self.discover(
            page=page,
            external_ids=ids,
            total_count=total_count,
            has_next=has_next,
        ).capture(ids).decide(outcomes)

    def counts(self) -> dict[str, int]:
        return {
            outcome.value: sum(value is outcome for _, value in self.decisions)
            for outcome in RegionalOutcome
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.2.0",
            "source_id": self.source_id,
            "collection_mode": self.collection_mode,
            "next_page": self.next_page,
            "total_count": self.total_count,
            "discovery_complete": self.discovery_complete,
            "complete": self.complete,
            "discovered_ids": list(self.discovered_ids),
            "captured_ids": list(self.captured_ids),
            "decisions": [
                {"external_id": external_id, "outcome": outcome.value}
                for external_id, outcome in self.decisions
            ],
            "counts": self.counts(),
            "pending_count": len(self.discovered_ids) - len(self.decisions),
            "pending_detail_count": len(self.discovered_ids)
            - len(
                set(self.captured_ids)
                | {
                    external_id
                    for external_id, outcome in self.decisions
                    if outcome is RegionalOutcome.FAILED
                }
            ),
        }


class RegionalCheckpointStore:
    def __init__(self, root: str | Path = "runtime/decisions/regional-checkpoints") -> None:
        self.root = Path(root)

    def save(self, checkpoint: RegionalBatchCheckpoint) -> Path:
        self._validate_source_id(checkpoint.source_id)
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{checkpoint.source_id}.json"
        payload = json.dumps(
            checkpoint.to_dict(), ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        descriptor, temporary = tempfile.mkstemp(
            dir=self.root, prefix=f".{checkpoint.source_id}.", suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return target

    def load(self, source_id: str) -> RegionalBatchCheckpoint | None:
        self._validate_source_id(source_id)
        target = self.root / f"{source_id}.json"
        if not target.is_file():
            return None
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
            schema_version = value.get("schema_version")
            if schema_version not in {"1.0.0", "1.1.0", "1.2.0"}:
                raise ValueError
            decisions = tuple(
                (item["external_id"], RegionalOutcome(item["outcome"]))
                for item in value["decisions"]
            )
            captured_ids = tuple(
                value.get(
                    "captured_ids",
                    [external_id for external_id, _ in decisions],
                )
            )
            checkpoint = RegionalBatchCheckpoint(
                source_id=value["source_id"],
                collection_mode=value["collection_mode"],
                next_page=value["next_page"],
                total_count=value["total_count"],
                discovery_complete=value["discovery_complete"],
                complete=value["complete"],
                discovered_ids=tuple(value["discovered_ids"]),
                captured_ids=captured_ids,
                decisions=decisions,
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise ValueError("regional checkpoint is invalid") from None
        expected = checkpoint.to_dict()
        if schema_version == "1.1.0":
            # 1.1 counted failed-but-not-captured identities as pending detail.
            # Accept that derived counter only while loading, then migrate on save.
            expected["schema_version"] = "1.1.0"
            expected["pending_detail_count"] = len(checkpoint.discovered_ids) - len(
                checkpoint.captured_ids
            )
        if checkpoint.source_id != source_id or (
            schema_version in {"1.1.0", "1.2.0"} and expected != value
        ):
            raise ValueError("regional checkpoint contract drift")
        return checkpoint

    @staticmethod
    def _validate_source_id(source_id: str) -> None:
        if source_id not in REGIONAL_EXPANSION_SPECS:
            raise ValueError("regional checkpoint source is unsupported")


def outcome_from_decisions(
    regional: Mapping[str, Any], duplicate: Mapping[str, Any] | None
) -> RegionalOutcome:
    if regional.get("application") == ApplicationAvailability.CLOSED.value:
        return RegionalOutcome.CLOSED
    if not regional.get("accepted"):
        return RegionalOutcome.REVIEW
    if duplicate is not None and not duplicate.get("accepted"):
        return RegionalOutcome.DUPLICATE
    return RegionalOutcome.ACCEPTED


def _matches_list_url(value: Any, approved_urls: tuple[str, ...]) -> bool:
    if not isinstance(value, str):
        return False
    try:
        actual = urllib.parse.urlsplit(value)
    except ValueError:
        return False
    if actual.scheme != "https" or actual.username is not None or actual.password is not None:
        return False
    for approved_url in approved_urls:
        approved = urllib.parse.urlsplit(approved_url)
        if actual.netloc != approved.netloc or actual.path != approved.path:
            continue
        required = urllib.parse.parse_qs(approved.query, keep_blank_values=True)
        present = urllib.parse.parse_qs(actual.query, keep_blank_values=True)
        if all(present.get(name) == expected for name, expected in required.items()):
            return True
    return False


def _matches_detail_identity(
    detail_url: Any,
    request_identity: Any,
    external_id: str,
    approved_patterns: tuple[str, ...],
    spec: RegionalExpansionSpec,
) -> bool:
    if not isinstance(detail_url, str) or not approved_patterns:
        return False
    if spec.request_identity:
        approved_text = approved_patterns[0].removeprefix("POST ").split(" ", 1)[0]
        approved = urllib.parse.urlsplit(approved_text)
        try:
            actual = urllib.parse.urlsplit(detail_url)
        except ValueError:
            return False
        return (
            actual.scheme == "https"
            and actual.netloc == approved.netloc
            and actual.path == approved.path
            and isinstance(request_identity, str)
            and f"bizId={external_id}" in request_identity
            and "mode=gw" in request_identity
        )
    try:
        actual = urllib.parse.urlsplit(detail_url)
    except ValueError:
        return False
    if actual.scheme != "https" or actual.username is not None or actual.password is not None:
        return False
    approved_text = approved_patterns[0].removeprefix("POST ").split(" ", 1)[0]
    approved = urllib.parse.urlsplit(approved_text)
    if actual.netloc != approved.netloc:
        return False
    if spec.identity_path:
        return external_id in actual.path and actual.path.endswith("/cntPage.do")
    if spec.identity_query is None:
        return False
    query = urllib.parse.parse_qs(actual.query, keep_blank_values=True)
    if query.get(spec.identity_query) != [external_id]:
        return False
    if spec.identity_query == "no":
        return actual.path in {"/policy/list.tc", "/policy/detail.modal"}
    approved_path = approved.path
    if spec.identity_query == "dataId":
        return actual.path in {
            approved_path,
            approved_path.replace("view.do", "view.ulsan"),
        }
    return actual.path == approved_path


def _json_document(document: RawPolicyDocument) -> dict[str, Any]:
    try:
        value = json.loads(document.raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExtractionError("regional Browser JSON Raw is invalid") from None
    if not isinstance(value, dict):
        raise ExtractionError("regional Browser JSON Raw must be an object")
    return value


def _json_response(value: Mapping[str, Any]) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": "application/json; charset=utf-8"},
        body=json.dumps(
            value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8"),
    )


def _raw(
    *,
    source_id: str,
    response: TransportResponse,
    role: RawDocumentRole,
    external_id: str | None,
    parent_document_id: str | None,
    source_url: str,
    payload: bytes,
    collected_at: datetime,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        source_id=source_id,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=source_url,
        collected_at=collected_at,
        content_type=response_content_type(
            response, default="application/json; charset=utf-8"
        ),
        raw_format=RawFormat.JSON,
        raw_payload=payload,
        http_status=response.status,
        collector_version=CAPTURE_VERSION,
    )


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    selected = " ".join(value.split())
    return selected or None


def _queryless_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "", "")
    )
