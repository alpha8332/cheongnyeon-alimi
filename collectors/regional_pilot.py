"""RYP5 representative adapters for Busan HTML and Seoul Browser Raw."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any

from collectors.base import CollectionOptions, CollectionResult
from collectors.cheonan_youthcenter import web_http_config_from_environment
from collectors.cross_source_duplicate import DuplicateEvidence
from collectors.errors import CollectorConfigurationError, EmptyResponseError
from collectors.extracted import ExtractedPolicy, ExtractionError, SourceProvenance
from collectors.http import HttpClient, TransportResponse
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
    utc_now,
)
from collectors.regional_profile import (
    RegionalSourceProfile,
    load_approved_regional_profile,
)
from collectors.regional_policy_gate import (
    RegionalPolicyDecision,
    RegionalPolicyEvidence,
    enforce_youth_target,
    evaluate_regional_policy,
)
from collectors.source_common import response_content_type, safe_parse_error
from collectors.storage import RawDocumentStore


BUSAN_SOURCE_ID = "regional-busan-youth-platform"
BUSAN_SOURCE_NAME = "부산청년플랫폼"
BUSAN_HOME_URL = "https://young.busan.go.kr/index.nm"
BUSAN_LIST_URL = "https://young.busan.go.kr/policySupport/list.nm"
BUSAN_DETAIL_URL = "https://young.busan.go.kr/policySupport/view.nm"
BUSAN_VERSION = "regional-busan-youth-platform/1.0"
SEOUL_SOURCE_ID = "regional-seoul-youth-platform"
SEOUL_SOURCE_NAME = "청년몽땅정보통"
SEOUL_LIST_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/list.do"
SEOUL_DETAIL_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"
SEOUL_VERSION = "regional-seoul-youth-platform-browser/1.0"
_BUSAN_ID = re.compile(r"^SUP\d+$")
_SEOUL_ID = re.compile(r"^(?:[A-Z]\d+|\d+)$")


def _clean(value: str) -> str:
    return " ".join(html.unescape(value).split())


@dataclass(frozen=True, slots=True)
class _BusanList:
    items: tuple[dict[str, str], ...]
    total_count: int
    jurisdiction_text: str
    operator_text: str
    youth_policy_scope_text: str
    application_scope_text: str


class _BusanListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active: dict[str, str] | None = None
        self._field: str | None = None
        self._chunks: list[str] = []
        self.items: list[dict[str, str]] = []
        self.total_count: int | None = None
        self._total_pending = False
        self._scope_field: str | None = None
        self._scope_chunks: list[str] = []
        self._in_endstat_select = False
        self.jurisdiction_text: str | None = None
        self.youth_policy_scope_text: str | None = None
        self.application_scope_text: str | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if (
            tag == "meta"
            and values.get("name") == "author"
            and values.get("content")
        ):
            self.jurisdiction_text = _clean(values["content"] or "")
        elif tag == "title":
            self._scope_field = "title"
            self._scope_chunks = []
        elif tag == "select" and values.get("name") == "endstat":
            self._in_endstat_select = True
        elif (
            tag == "option"
            and self._in_endstat_select
            and "selected" in values
        ):
            self._scope_field = "application_scope"
            self._scope_chunks = []
        if tag == "a":
            href = values.get("href") or ""
            parsed = urllib.parse.urlsplit(href)
            query = urllib.parse.parse_qs(parsed.query)
            external_id = (query.get("bizSid") or [""])[0]
            if (
                parsed.path == "/policySupport/view.nm"
                and _BUSAN_ID.fullmatch(external_id)
            ):
                self._active = {"external_id": external_id}
        if self._active is not None:
            field_by_class = {
                "cd_state": "status",
                "card_cate": "category",
                "card_tit": "title",
                "card_dptmt": "organization",
                "period_num": "application_period",
            }
            for class_name, field in field_by_class.items():
                if class_name in classes:
                    self._field = field
                    self._chunks = []
                    break
        if tag == "span" and "blue" in classes:
            self._total_pending = True

    def handle_data(self, data: str) -> None:
        if self._field is not None:
            self._chunks.append(data)
        if self._scope_field is not None:
            self._scope_chunks.append(data)
        if self._total_pending and self.total_count is None:
            text = _clean(data)
            if text.isdigit():
                self.total_count = int(text)

    def handle_endtag(self, tag: str) -> None:
        if self._scope_field == "title" and tag == "title":
            value = _clean("".join(self._scope_chunks))
            self.youth_policy_scope_text = value.split(":", 1)[0].strip()
            self._scope_field = None
            self._scope_chunks = []
        elif self._scope_field == "application_scope" and tag == "option":
            self.application_scope_text = _clean("".join(self._scope_chunks))
            self._scope_field = None
            self._scope_chunks = []
        if tag == "select":
            self._in_endstat_select = False
        if self._field is not None and tag in {"div", "span"}:
            value = _clean("".join(self._chunks))
            if value and self._active is not None:
                self._active[self._field] = value
            self._field = None
            self._chunks = []
        if tag == "span":
            self._total_pending = False
        if tag == "a" and self._active is not None:
            if self._active.get("title"):
                self.items.append(self._active)
            self._active = None

    def payload(self) -> _BusanList:
        unique: dict[str, dict[str, str]] = {}
        for item in self.items:
            unique.setdefault(item["external_id"], item)
        if (
            not unique
            or self.total_count is None
            or not self.jurisdiction_text
            or not self.youth_policy_scope_text
            or not self.application_scope_text
        ):
            raise ExtractionError("Busan list selector drift")
        return _BusanList(
            tuple(unique.values()),
            self.total_count,
            self.jurisdiction_text,
            self.jurisdiction_text,
            self.youth_policy_scope_text,
            self.application_scope_text,
        )


class _BusanDetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._field: str | None = None
        self._chunks: list[str] = []
        self._pending_label: str | None = None
        self.fields: dict[str, str] = {}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        if "dt_tit" in classes:
            self._field = "title"
            self._chunks = []
        elif "dtif_atc" in classes:
            self._field = "label"
            self._chunks = []
        elif "dtif_cont" in classes:
            self._field = "value"
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._field is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._field is None or tag != "span":
            return
        value = _clean("".join(self._chunks))
        if self._field == "title" and value:
            self.fields["title"] = value
        elif self._field == "label":
            self._pending_label = value
        elif self._field == "value" and self._pending_label:
            self.fields[self._pending_label] = value
            self._pending_label = None
        self._field = None
        self._chunks = []

    def payload(self) -> dict[str, Any]:
        if not self.fields.get("title") or not self.fields.get("신청기간"):
            raise ExtractionError("Busan detail selector drift")
        observations = {
            "implementing_organization_text": _label_observation(
                self.fields, "담당기관"
            ),
            "region_eligibility_text": _label_observation(
                self.fields, "지원대상"
            ),
            "application_period_text": _label_observation(
                self.fields, "신청기간"
            ),
            "application_channel_text": _label_observation(
                self.fields, "신청방법"
            ),
            "additional_benefit_text": _label_observation(
                self.fields, "지원내용"
            ),
        }
        return self.fields | {"evidence_observations": observations}


def _label_observation(fields: Mapping[str, str], label: str) -> str:
    if label not in fields:
        return "label_not_found"
    return (
        "value_extracted"
        if _text(fields.get(label)) is not None
        else "label_present_value_empty"
    )


class BusanYouthCollector:
    """Collect one 모집중 Busan page and a bounded detail slice."""

    source_id = BUSAN_SOURCE_ID

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        profile: RegionalSourceProfile | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._profile = profile or load_approved_regional_profile(
            BUSAN_SOURCE_ID
        )
        _validate_busan_profile(self._profile)
        self._http_client = http_client or HttpClient(
            config=web_http_config_from_environment()
        )
        self._store = store or RawDocumentStore()
        self._now = now

    def collect(
        self, options: CollectionOptions | None = None
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        if selected.page > 30:
            raise CollectorConfigurationError(
                "Busan page exceeds the operational safety limit"
            )
        if selected.detail_limit > self._profile.request_budget.max_detail_requests:
            raise CollectorConfigurationError(
                "Busan detail limit exceeds the approved request budget"
            )
        response = self._http_client.get(
            source_id=self.source_id,
            url=BUSAN_LIST_URL,
            query={
                "menuCd": "12",
                "endstat": "Y",
                "pageIndex": str(selected.page),
            },
        )
        payload = _parse_busan_list(response)
        items = payload.items[: selected.limit]
        if not items:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=BUSAN_LIST_URL,
                reason="source returned an empty policy list",
                status=response.status,
            )
        if selected.detail_limit and selected.detail_offset >= len(items):
            raise CollectorConfigurationError(
                "Busan detail offset exceeds the page"
            )
        detail_items = items[
            selected.detail_offset : selected.detail_offset
            + selected.detail_limit
        ]
        stored_items = items if selected.detail_limit == 0 else detail_items
        collected_at = self._now()
        list_document = _raw(
            source_id=self.source_id,
            version=BUSAN_VERSION,
            response=response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=BUSAN_LIST_URL,
            payload=response.body,
            raw_format=RawFormat.HTML,
            collected_at=collected_at,
        )
        documents = [list_document]
        for item in stored_items:
            documents.append(
                _raw(
                    source_id=self.source_id,
                    version=BUSAN_VERSION,
                    response=response,
                    role=RawDocumentRole.LIST_ITEM,
                    external_id=item["external_id"],
                    parent_document_id=list_document.document_id,
                    source_url=BUSAN_LIST_URL,
                    payload=_json_bytes(item),
                    raw_format=RawFormat.JSON,
                    collected_at=collected_at,
                )
            )
        detail_ids: list[str] = []
        detail_count = len(detail_items)
        for item in detail_items:
            external_id = item["external_id"]
            detail_response = self._http_client.get(
                source_id=self.source_id,
                url=BUSAN_DETAIL_URL,
                query={"menuCd": "13", "bizSid": external_id},
            )
            detail = _parse_busan_detail(detail_response)
            if detail["title"] != item["title"]:
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=BUSAN_DETAIL_URL,
                    response=detail_response,
                    reason="detail title does not match the list item",
                )
            document = _raw(
                source_id=self.source_id,
                version=BUSAN_VERSION,
                response=detail_response,
                role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=external_id,
                parent_document_id=None,
                source_url=BUSAN_DETAIL_URL,
                payload=detail_response.body,
                raw_format=RawFormat.HTML,
                collected_at=self._now(),
            )
            documents.append(document)
            detail_ids.append(document.document_id)
        paths = tuple(self._store.save(document) for document in documents)
        return CollectionResult(
            source_id=self.source_id,
            request_count=1 + detail_count,
            item_count=len(items),
            detail_count=detail_count,
            stored_paths=paths,
            page=selected.page,
            page_size=len(items),
            total_count=payload.total_count,
            external_ids=tuple(item["external_id"] for item in items),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_ids),
        )


class BusanYouthExtractor:
    source_id = BUSAN_SOURCE_ID

    def extract(
        self, documents: Iterable[RawPolicyDocument]
    ) -> tuple[ExtractedPolicy, ...]:
        return _extract_structured_regional(
            documents,
            source_id=BUSAN_SOURCE_ID,
            source_name=BUSAN_SOURCE_NAME,
            list_url=BUSAN_LIST_URL,
            detail_url=BUSAN_DETAIL_URL,
            version=BUSAN_VERSION,
            parse_detail=lambda document: _parse_busan_detail_bytes(
                document.raw_bytes
            ),
            field_mapper=_busan_fields,
            list_scope_mapper=_busan_source_scope,
        )


class SeoulBrowserCaptureStore:
    """Validate and persist structured observations from the in-app Browser."""

    def __init__(
        self,
        *,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._store = store or RawDocumentStore()
        self._now = now
        profile = load_approved_regional_profile(SEOUL_SOURCE_ID)
        if profile.collection_mode != "browser":
            raise CollectorConfigurationError("Seoul Browser profile drifted")

    def save(self, capture: Mapping[str, Any]) -> CollectionResult:
        items = _validate_seoul_capture(capture)
        collected_at = self._now()
        list_payload = {
            "capture_mode": "browser",
            "list_url": capture["list_url"],
            "action_trace": deepcopy(capture["action_trace"]),
            "item_count": len(items),
        }
        response = TransportResponse(
            status=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
            body=_json_bytes(list_payload),
        )
        list_document = _raw(
            source_id=SEOUL_SOURCE_ID,
            version=SEOUL_VERSION,
            response=response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=SEOUL_LIST_URL,
            payload=response.body,
            raw_format=RawFormat.JSON,
            collected_at=collected_at,
        )
        documents = [list_document]
        detail_ids: list[str] = []
        for value in items:
            item = deepcopy(value)
            detail = item.pop("detail")
            external_id = item["external_id"]
            item_response = TransportResponse(
                status=200,
                headers={"Content-Type": "application/json; charset=utf-8"},
                body=_json_bytes(item),
            )
            documents.append(
                _raw(
                    source_id=SEOUL_SOURCE_ID,
                    version=SEOUL_VERSION,
                    response=item_response,
                    role=RawDocumentRole.LIST_ITEM,
                    external_id=external_id,
                    parent_document_id=list_document.document_id,
                    source_url=SEOUL_LIST_URL,
                    payload=item_response.body,
                    raw_format=RawFormat.JSON,
                    collected_at=collected_at,
                )
            )
            detail_response = TransportResponse(
                status=200,
                headers={"Content-Type": "application/json; charset=utf-8"},
                body=_json_bytes(detail),
            )
            document = _raw(
                source_id=SEOUL_SOURCE_ID,
                version=SEOUL_VERSION,
                response=detail_response,
                role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=external_id,
                parent_document_id=None,
                source_url=SEOUL_DETAIL_URL,
                payload=detail_response.body,
                raw_format=RawFormat.JSON,
                collected_at=collected_at,
            )
            documents.append(document)
            detail_ids.append(document.document_id)
        paths = tuple(self._store.save(document) for document in documents)
        return CollectionResult(
            source_id=SEOUL_SOURCE_ID,
            request_count=0,
            item_count=len(items),
            detail_count=len(items),
            stored_paths=paths,
            page=1,
            page_size=len(items),
            total_count=len(items),
            external_ids=tuple(item["external_id"] for item in items),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_ids),
        )


class SeoulYouthExtractor:
    source_id = SEOUL_SOURCE_ID

    def extract(
        self, documents: Iterable[RawPolicyDocument]
    ) -> tuple[ExtractedPolicy, ...]:
        return _extract_structured_regional(
            documents,
            source_id=SEOUL_SOURCE_ID,
            source_name=SEOUL_SOURCE_NAME,
            list_url=SEOUL_LIST_URL,
            detail_url=SEOUL_DETAIL_URL,
            version=SEOUL_VERSION,
            parse_detail=_json_document,
            field_mapper=_seoul_fields,
        )


def create_busan_youth_collector() -> BusanYouthCollector:
    return BusanYouthCollector()


def decide_representative_regional_policy(
    policy: ExtractedPolicy,
    *,
    as_of: date | None = None,
    require_youth_target: bool = True,
) -> RegionalPolicyDecision:
    expected = {
        BUSAN_SOURCE_ID: "부산광역시",
        SEOUL_SOURCE_ID: "서울특별시",
    }.get(policy.source_id)
    if expected is None:
        raise ExtractionError("unsupported representative regional source")
    source_fields = policy.extra.get("source_fields")
    if not isinstance(source_fields, dict):
        raise ExtractionError("representative regional evidence is missing")
    detail = source_fields.get("detail_response")
    if not isinstance(detail, dict):
        raise ExtractionError("representative detail evidence is missing")
    values = {
        "implementing_organization_text": policy.organization,
        "region_eligibility_text": policy.eligibility_text,
        "application_channel_text": policy.application_method,
        "additional_benefit_text": policy.support_content,
        "source_region_text": policy.region_text,
        "application_period_text": policy.application_period_text,
    }
    detail_observations = detail.get("evidence_observations")
    field_observations = tuple(
        (field_name, status)
        for field_name, status in (
            detail_observations.items()
            if isinstance(detail_observations, Mapping)
            else ()
        )
        if field_name in values
        and isinstance(status, str)
        and ((status == "value_extracted") == (values[field_name] is not None))
    )
    evidence = RegionalPolicyEvidence(
        **values,
        field_locators=tuple(
            (name, f"detail:{name}")
            for name, value in values.items()
            if value is not None
        ),
        provenance=policy.provenance,
        field_observations=field_observations,
    )
    decision = evaluate_regional_policy(
        policy,
        evidence,
        expected_region_text=expected,
        as_of=as_of,
    )
    if require_youth_target:
        return enforce_youth_target(policy, decision)
    return decision


def map_representative_duplicate_evidence(
    policy: ExtractedPolicy,
) -> DuplicateEvidence:
    if policy.source_id not in {BUSAN_SOURCE_ID, SEOUL_SOURCE_ID}:
        raise ExtractionError("invalid representative duplicate source")
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


def _extract_structured_regional(
    documents: Iterable[RawPolicyDocument],
    *,
    source_id: str,
    source_name: str,
    list_url: str,
    detail_url: str,
    version: str,
    parse_detail: Callable[[RawPolicyDocument], dict[str, Any]],
    field_mapper: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    list_scope_mapper: (
        Callable[[RawPolicyDocument], dict[str, str]] | None
    ) = None,
) -> tuple[ExtractedPolicy, ...]:
    selected = tuple(documents)
    if not selected or any(value.source_id != source_id for value in selected):
        raise ExtractionError("invalid representative Raw source")
    parents = {
        value.document_id: value
        for value in selected
        if value.document_role is RawDocumentRole.LIST_RESPONSE
        and value.source_url == list_url
    }
    items = [
        value
        for value in selected
        if value.document_role is RawDocumentRole.LIST_ITEM
    ]
    details = {
        value.external_id: value
        for value in selected
        if value.document_role is RawDocumentRole.DETAIL_RESPONSE
        and value.source_url == detail_url
    }
    if not parents or not items or len(details) != len(items):
        raise ExtractionError("representative Raw batch is incomplete")
    policies: list[ExtractedPolicy] = []
    seen: set[str] = set()
    for document in items:
        item = _json_document(document)
        external_id = _text(item.get("external_id"))
        if (
            external_id is None
            or external_id != document.external_id
            or external_id in seen
            or document.parent_document_id not in parents
        ):
            raise ExtractionError("representative list identity drift")
        seen.add(external_id)
        detail_document = details.get(external_id)
        if detail_document is None:
            raise ExtractionError("representative detail identity missing")
        detail = parse_detail(detail_document)
        fields = field_mapper(item, detail)
        if fields["title"] != _text(item.get("title")):
            raise ExtractionError("representative detail title drift")
        provenance_documents = (
            parents[document.parent_document_id],
            document,
            detail_document,
        )
        provenance = tuple(
            SourceProvenance.from_raw(value) for value in provenance_documents
        )
        source_scope = (
            list_scope_mapper(parents[document.parent_document_id])
            if list_scope_mapper is not None
            else None
        )
        policies.append(
            ExtractedPolicy(
                source_id=source_id,
                source_name=source_name,
                external_id=external_id,
                title=fields["title"],
                organization=fields.get("organization"),
                summary=fields.get("summary"),
                category_text=fields.get("category"),
                application_period_text=fields.get("application_period"),
                region_text=fields.get("source_region"),
                age_text=fields.get("age"),
                eligibility_text=fields.get("eligibility"),
                support_content=fields.get("support_content"),
                application_method=fields.get("application_method"),
                source_url=fields["source_url"],
                collected_at=max(value.collected_at for value in provenance),
                provenance=provenance,
                extra={
                    "selector_contract": version,
                    "source_fields": {
                        "list_item": deepcopy(item),
                        "detail_response": deepcopy(detail),
                    },
                    "source_scope": deepcopy(source_scope),
                    "institutional_contact": fields.get("contact"),
                    "required_documents": fields.get("required_documents"),
                    "exclusion_conditions": fields.get("exclusions"),
                },
            )
        )
    if set(details) != seen:
        raise ExtractionError("orphan representative detail identity")
    return tuple(policies)


def _busan_fields(
    item: dict[str, Any], detail: dict[str, Any]
) -> dict[str, Any]:
    external_id = item["external_id"]
    organization = _text(detail.get("담당기관")) or _text(
        item.get("organization")
    )
    # The portal and 담당기관 are jurisdiction evidence, while the generic
    # word "청년" alone is intentionally insufficient for automatic acceptance.
    source_region = "부산광역시" if organization else None
    return {
        "title": _text(detail.get("title")),
        "organization": organization,
        "summary": None,
        "category": _text(item.get("category")),
        "application_period": _text(detail.get("신청기간")),
        "source_region": source_region,
        "age": None,
        "eligibility": _text(detail.get("지원대상")),
        "support_content": None,
        "application_method": None,
        "contact": _text(detail.get("문의")),
        "required_documents": None,
        "exclusions": None,
        "source_url": (
            f"{BUSAN_DETAIL_URL}?menuCd=13&bizSid={external_id}"
        ),
    }


def _busan_source_scope(document: RawPolicyDocument) -> dict[str, str]:
    parser = _BusanListParser()
    try:
        parser.feed(document.raw_bytes.decode("utf-8"))
        parser.close()
        payload = parser.payload()
    except UnicodeDecodeError:
        raise ExtractionError("Busan list scope encoding drift") from None
    return {
        "jurisdiction_text": payload.jurisdiction_text,
        "operator_text": payload.operator_text,
        "youth_policy_scope_text": payload.youth_policy_scope_text,
        "application_scope_text": payload.application_scope_text,
    }


def _seoul_fields(
    item: dict[str, Any], detail: dict[str, Any]
) -> dict[str, Any]:
    external_id = item["external_id"]
    return {
        "title": _text(detail.get("title")),
        "organization": _text(detail.get("organization")),
        "summary": _text(item.get("summary")),
        "category": _text(detail.get("category")) or _text(item.get("category")),
        "application_period": _text(detail.get("application_period")),
        "source_region": _text(detail.get("source_region")),
        "age": _text(detail.get("age")),
        "eligibility": _text(detail.get("eligibility")),
        "support_content": _text(detail.get("support_content")),
        "application_method": _text(detail.get("application_method")),
        "contact": _text(detail.get("contact")),
        "required_documents": _text(detail.get("required_documents")),
        "exclusions": _text(detail.get("exclusions")),
        "source_url": (
            f"{SEOUL_DETAIL_URL}?key=2309150002&plcyBizId={external_id}"
        ),
    }


def _validate_seoul_capture(
    capture: Mapping[str, Any]
) -> tuple[dict[str, Any], ...]:
    if capture.get("source_id") != SEOUL_SOURCE_ID:
        raise ExtractionError("invalid Seoul Browser capture source")
    list_url = capture.get("list_url")
    if not _matches_approved_url(
        list_url,
        SEOUL_LIST_URL,
        {"key": "2309150002"},
    ):
        raise ExtractionError("invalid Seoul Browser list URL")
    trace = capture.get("action_trace")
    items = capture.get("items")
    if (
        not isinstance(trace, list)
        or not 1 <= len(trace) <= 30
        or not all(isinstance(value, str) and value.strip() for value in trace)
        or not isinstance(items, list)
    ):
        raise ExtractionError("incomplete Seoul Browser capture")
    if not 1 <= len(items) <= 3:
        raise ExtractionError("Seoul Browser capture requires 1 to 3 items")
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    required_detail = {
        "title",
        "organization",
        "category",
        "application_period",
        "source_region",
        "eligibility",
        "support_content",
    }
    for value in items:
        if not isinstance(value, dict):
            raise ExtractionError("invalid Seoul Browser item")
        external_id = value.get("external_id")
        title = value.get("title")
        detail_url = value.get("detail_url")
        detail = value.get("detail")
        if (
            not isinstance(external_id, str)
            or not _SEOUL_ID.fullmatch(external_id)
            or external_id in seen
            or not isinstance(title, str)
            or not title.strip()
            or not _matches_approved_url(
                detail_url,
                SEOUL_DETAIL_URL,
                {"key": "2309150002", "plcyBizId": external_id},
            )
            or not isinstance(detail, dict)
            or not required_detail.issubset(detail)
            or _text(detail.get("title")) != _text(title)
            or any(_text(detail.get(field)) is None for field in required_detail)
        ):
            raise ExtractionError("Seoul Browser item contract drift")
        seen.add(external_id)
        validated.append(deepcopy(value))
    return tuple(validated)


def _matches_approved_url(
    value: Any,
    approved_base: str,
    required_query: Mapping[str, str],
) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        approved = urllib.parse.urlsplit(approved_base)
        query = urllib.parse.parse_qs(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=False,
        )
    except ValueError:
        return False
    if (
        parsed.scheme != approved.scheme
        or parsed.netloc != approved.netloc
        or parsed.path != approved.path
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        return False
    return all(
        query.get(name) == [expected]
        for name, expected in required_query.items()
    )


def _parse_busan_list(response: TransportResponse) -> _BusanList:
    try:
        parser = _BusanListParser()
        parser.feed(response.body.decode("utf-8"))
        parser.close()
        return parser.payload()
    except (UnicodeDecodeError, ExtractionError):
        raise safe_parse_error(
            source_id=BUSAN_SOURCE_ID,
            source_url=BUSAN_LIST_URL,
            response=response,
            reason="list selector drifted",
        ) from None


def _parse_busan_detail(response: TransportResponse) -> dict[str, Any]:
    try:
        return _parse_busan_detail_bytes(response.body)
    except ExtractionError:
        raise safe_parse_error(
            source_id=BUSAN_SOURCE_ID,
            source_url=BUSAN_DETAIL_URL,
            response=response,
            reason="detail selector drifted",
        ) from None


def _parse_busan_detail_bytes(payload: bytes) -> dict[str, Any]:
    try:
        parser = _BusanDetailParser()
        parser.feed(payload.decode("utf-8"))
        parser.close()
        return parser.payload()
    except UnicodeDecodeError:
        raise ExtractionError("Busan detail is not valid UTF-8") from None


def _json_document(document: RawPolicyDocument) -> dict[str, Any]:
    try:
        value = json.loads(document.raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExtractionError("representative JSON Raw is invalid") from None
    if not isinstance(value, dict):
        raise ExtractionError("representative JSON Raw must be an object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _raw(
    *,
    source_id: str,
    version: str,
    response: TransportResponse,
    role: RawDocumentRole,
    external_id: str | None,
    parent_document_id: str | None,
    source_url: str,
    payload: bytes,
    raw_format: RawFormat,
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
            response,
            default=(
                "application/json"
                if raw_format is RawFormat.JSON
                else "text/html"
            ),
        ),
        raw_format=raw_format,
        raw_payload=payload,
        http_status=response.status,
        collector_version=version,
    )


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = _clean(value)
    return cleaned or None


def _validate_busan_profile(profile: RegionalSourceProfile) -> None:
    if (
        profile.source_id != BUSAN_SOURCE_ID
        or profile.home_url != BUSAN_HOME_URL
        or profile.collection_mode != "http_html"
        or len(profile.approved_list_urls) != 1
        or len(profile.approved_detail_url_patterns) != 1
    ):
        raise CollectorConfigurationError("Busan profile contract drifted")
