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


@dataclass(frozen=True, slots=True)
class RegionalExpansionSpec:
    source_name: str
    expected_region_text: str
    identity_query: str | None = None
    identity_path: bool = False
    request_identity: bool = False


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
        page, total_count, has_next, items = self._validate(capture)
        collected_at = self._now()
        list_payload = {
            "capture_mode": "browser",
            "list_url": capture["list_url"],
            "action_trace": deepcopy(capture["action_trace"]),
            "page": page,
            "total_count": total_count,
            "has_next": has_next,
            "item_count": len(items),
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
        paths = tuple(self._store.save(document) for document in documents)
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

    def _validate(
        self, capture: Mapping[str, Any]
    ) -> tuple[int, int | None, bool, tuple[dict[str, Any], ...]]:
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
            ):
                raise ExtractionError("regional Browser item contract drift")
            seen.add(external_id)
            validated.append(deepcopy(value))
        if total_count is not None and total_count < len(items):
            raise ExtractionError("regional Browser total is smaller than batch")
        return page, total_count, has_next, tuple(validated)


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
    )
    decision = evaluate_regional_policy(
        policy,
        evidence,
        expected_region_text=spec.expected_region_text,
        as_of=as_of,
    )
    youth_evidence = " ".join(
        value
        for value in (
            policy.title,
            policy.eligibility_text,
            policy.age_text,
        )
        if value is not None
    )
    if decision.accepted and not any(
        marker in youth_evidence for marker in ("청년", "청소년", "대학생")
    ):
        return RegionalPolicyDecision(
            source_id=decision.source_id,
            external_id=decision.external_id,
            regionality=RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
            application=decision.application,
            reason_codes=(
                *decision.reason_codes,
                "youth_target_unconfirmed",
            ),
            evidence=decision.evidence,
            accepted_policy=None,
        )
    return decision


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
        if (
            len(decision_ids) != len(set(decision_ids))
            or set(decision_ids) - set(discovered)
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
            or set(ids) & set(self.discovered_ids)
        ):
            raise ValueError("regional checkpoint discovery page is invalid")
        known_total = self.total_count
        discovered = (*self.discovered_ids, *ids)
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
        ).decide(outcomes)

    def counts(self) -> dict[str, int]:
        return {
            outcome.value: sum(value is outcome for _, value in self.decisions)
            for outcome in RegionalOutcome
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "source_id": self.source_id,
            "collection_mode": self.collection_mode,
            "next_page": self.next_page,
            "total_count": self.total_count,
            "discovery_complete": self.discovery_complete,
            "complete": self.complete,
            "discovered_ids": list(self.discovered_ids),
            "decisions": [
                {"external_id": external_id, "outcome": outcome.value}
                for external_id, outcome in self.decisions
            ],
            "counts": self.counts(),
            "pending_count": len(self.discovered_ids) - len(self.decisions),
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
            decisions = tuple(
                (item["external_id"], RegionalOutcome(item["outcome"]))
                for item in value["decisions"]
            )
            checkpoint = RegionalBatchCheckpoint(
                source_id=value["source_id"],
                collection_mode=value["collection_mode"],
                next_page=value["next_page"],
                total_count=value["total_count"],
                discovery_complete=value["discovery_complete"],
                complete=value["complete"],
                discovered_ids=tuple(value["discovered_ids"]),
                decisions=decisions,
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise ValueError("regional checkpoint is invalid") from None
        if checkpoint.source_id != source_id or checkpoint.to_dict() != value:
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
