"""Profile-driven collector for the approved Gyeongbuk youth portal."""

from __future__ import annotations

import html
import json
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
from collectors.extracted import (
    ExtractedPolicy,
    ExtractionError,
    SourceProvenance,
)
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
    evaluate_regional_policy,
)
from collectors.source_common import response_content_type, safe_parse_error
from collectors.storage import RawDocumentStore


SOURCE_ID = "regional-gyeongbuk-youth-platform"
SOURCE_NAME = "경북청년포털 청년e끌림"
HOME_URL = "https://gbyouth.go.kr/main.tc"
LIST_PAGE_URL = "https://gbyouth.go.kr/policy/list.tc"
LIST_JSON_URL = "https://gbyouth.go.kr/policy/list.json"
DETAIL_MODAL_URL = "https://gbyouth.go.kr/policy/detail.modal"
COLLECTOR_VERSION = "regional-gyeongbuk-youth-platform/1.0"
LIST_PAGE_QUERY = {"mn": "2379", "pageNo": "5069"}
LIST_FORM = {
    "pageNo": "5069",
    "mn": "2379",
    "pageIndex": "1",
    "searchCondition": "0",
    "type": "0",
    "searchPolicyNm": "",
    "searchPolicyTypeTmp": "",
    "searchRgnSe": "",
    "searchAplyPeriod": "",
    "uploadType": "",
}
_DETAIL_LABELS = {
    "정책유형": "category_text",
    "지역구분": "region_text",
    "정책내용 상세": "support_content",
    "지원내용": "support_content",
    "지원규모": "eligibility_text",
    "운영기간": "operation_period_text",
    "신청기간": "application_period_text",
    "주관기관": "supervising_organization",
    "운영기관": "operating_organization",
    "문의처": "institutional_contact",
    "신청방법": "application_method",
    "첨부파일": "required_documents",
}
_PAIR_TAGS = {"dt", "dd", "th", "td"}
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass(frozen=True, slots=True)
class _CsrfContract:
    header_name: str
    token: str


@dataclass(frozen=True, slots=True)
class _ListPayload:
    items: tuple[dict[str, Any], ...]
    total_count: int


@dataclass(frozen=True, slots=True)
class _DetailPayload:
    title: str
    fields: dict[str, str]


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "meta":
            return
        values = dict(attrs)
        name = values.get("name")
        content = values.get("content")
        if name in {"_csrf", "_csrf_header"} and content:
            self.values[name] = content


class _DetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture_tag: str | None = None
        self._capture_depth = 0
        self._chunks: list[str] = []
        self._elements: list[tuple[str, str]] = []
        self._title_chunks: list[str] = []
        self._titles: list[str] = []
        self._title_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag in _VOID_TAGS:
            return
        if self._title_depth:
            self._title_depth += 1
        elif tag in {"h1", "h2"}:
            self._title_depth = 1
            self._title_chunks = []
        if self._capture_tag is not None:
            self._capture_depth += 1
        elif tag in _PAIR_TAGS:
            self._capture_tag = tag
            self._capture_depth = 1
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._title_depth:
            self._title_chunks.append(data)
        if self._capture_tag is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if self._title_depth:
            self._title_depth -= 1
            if self._title_depth == 0:
                title = _clean_text("".join(self._title_chunks))
                if title:
                    self._titles.append(title)
        if self._capture_tag is None:
            return
        self._capture_depth -= 1
        if self._capture_depth == 0:
            value = _clean_text("".join(self._chunks))
            if value:
                self._elements.append((self._capture_tag, value))
            self._capture_tag = None
            self._chunks = []

    def payload(self) -> _DetailPayload:
        title = self._titles[0] if self._titles else ""
        fields: dict[str, str] = {}
        for index, (tag, label) in enumerate(self._elements[:-1]):
            key = _DETAIL_LABELS.get(label.rstrip(":"))
            if key is None or tag not in {"dt", "th"}:
                continue
            value_tag, value = self._elements[index + 1]
            if value_tag in {"dd", "td"} and value:
                fields.setdefault(key, value)
        if not title or not fields:
            raise ExtractionError("Gyeongbuk detail selector drift")
        return _DetailPayload(title=title, fields=fields)


class GyeongbukYouthCollector:
    """Collect one bounded Gyeongbuk JSON page and up to three details."""

    source_id = SOURCE_ID

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        profile: RegionalSourceProfile | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._profile = profile or load_approved_regional_profile(SOURCE_ID)
        _validate_profile(self._profile)
        self._http_client = http_client or HttpClient(
            config=web_http_config_from_environment()
        )
        self._store = store or RawDocumentStore()
        self._now = now

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        if selected.page != 1:
            raise CollectorConfigurationError(
                "Gyeongbuk pilot profile only permits page 1"
            )
        if (
            selected.detail_limit
            > self._profile.request_budget.max_detail_requests
        ):
            raise CollectorConfigurationError(
                "Gyeongbuk detail limit exceeds the approved request budget"
            )

        home_response = self._http_client.get(
            source_id=self.source_id,
            url=HOME_URL,
        )
        csrf = _csrf_contract(home_response)
        headers = {
            csrf.header_name: csrf.token,
            "Referer": _list_page_url(),
            "X-Requested-With": "XMLHttpRequest",
        }
        list_response = self._http_client.post_form(
            source_id=self.source_id,
            url=LIST_JSON_URL,
            form=LIST_FORM,
            headers=headers,
        )
        list_payload = _parse_list(list_response)
        items = list_payload.items[: selected.limit]
        if not items:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=LIST_JSON_URL,
                reason="source returned an empty policy list",
                status=list_response.status,
            )

        collected_at = self._now()
        list_document = _raw_document(
            response=list_response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            collected_at=collected_at,
            payload=list_response.body,
            source_url=LIST_JSON_URL,
            raw_format=RawFormat.JSON,
        )
        documents: list[RawPolicyDocument] = [list_document]
        external_ids: list[str] = []
        for item in items:
            external_id = str(item["no"])
            external_ids.append(external_id)
            item_document = _raw_document(
                response=list_response,
                role=RawDocumentRole.LIST_ITEM,
                external_id=external_id,
                parent_document_id=list_document.document_id,
                collected_at=collected_at,
                payload=_json_bytes(item),
                source_url=LIST_JSON_URL,
                raw_format=RawFormat.JSON,
            )
            documents.append(item_document)

        detail_document_ids: list[str] = []
        detail_count = min(selected.detail_limit, len(external_ids))
        for external_id in external_ids[:detail_count]:
            detail_response = self._http_client.post_form(
                source_id=self.source_id,
                url=DETAIL_MODAL_URL,
                form={
                    "templateRoot": "/resources/templates/front",
                    "no": external_id,
                },
                headers=headers,
            )
            detail = _parse_detail(detail_response)
            if detail.title != _item_title(items, external_id):
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=DETAIL_MODAL_URL,
                    response=detail_response,
                    reason="detail title does not match the list item",
                )
            document = _raw_document(
                response=detail_response,
                role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=external_id,
                parent_document_id=None,
                collected_at=self._now(),
                payload=detail_response.body,
                source_url=DETAIL_MODAL_URL,
                raw_format=RawFormat.HTML,
            )
            documents.append(document)
            detail_document_ids.append(document.document_id)

        stored_paths = tuple(self._store.save(document) for document in documents)
        return CollectionResult(
            source_id=self.source_id,
            request_count=2 + detail_count,
            item_count=len(items),
            detail_count=detail_count,
            stored_paths=stored_paths,
            page=1,
            page_size=len(items),
            total_count=list_payload.total_count,
            external_ids=tuple(external_ids),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_document_ids),
        )


class GyeongbukYouthExtractor:
    """Map Gyeongbuk list JSON and optional modal HTML to common fields."""

    source_id = SOURCE_ID

    def extract(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[ExtractedPolicy, ...]:
        selected = tuple(documents)
        if not selected or any(
            document.source_id != SOURCE_ID for document in selected
        ):
            raise ExtractionError("invalid Gyeongbuk Raw source")
        list_responses = {
            document.document_id: document
            for document in selected
            if document.document_role is RawDocumentRole.LIST_RESPONSE
            and document.raw_format is RawFormat.JSON
            and document.source_url == LIST_JSON_URL
        }
        items = [
            document
            for document in selected
            if document.document_role is RawDocumentRole.LIST_ITEM
        ]
        details = {
            document.external_id: document
            for document in selected
            if document.document_role is RawDocumentRole.DETAIL_RESPONSE
        }
        if not list_responses or not items:
            raise ExtractionError("Gyeongbuk Raw batch is incomplete")
        if len(details) != len(
            [
                document
                for document in selected
                if document.document_role is RawDocumentRole.DETAIL_RESPONSE
            ]
        ):
            raise ExtractionError("duplicate Gyeongbuk detail identity")

        policies: list[ExtractedPolicy] = []
        item_ids: set[str] = set()
        for item in items:
            if (
                item.raw_format is not RawFormat.JSON
                or item.source_url != LIST_JSON_URL
                or item.parent_document_id not in list_responses
            ):
                raise ExtractionError("invalid Gyeongbuk list item contract")
            fields = _json_object(item)
            external_id = str(fields.get("no", ""))
            if not external_id or external_id != item.external_id:
                raise ExtractionError("Gyeongbuk list identity mismatch")
            if external_id in item_ids:
                raise ExtractionError("duplicate Gyeongbuk list identity")
            item_ids.add(external_id)
            detail_document = details.get(external_id)
            detail = None
            if detail_document is not None:
                if (
                    detail_document.raw_format is not RawFormat.HTML
                    or detail_document.source_url != DETAIL_MODAL_URL
                ):
                    raise ExtractionError("invalid Gyeongbuk detail contract")
                detail = _parse_detail_payload(detail_document.raw_bytes)
                if detail.title != _present_text(fields.get("policyNm")):
                    raise ExtractionError("Gyeongbuk detail identity drift")
            provenance_documents = (
                list_responses[item.parent_document_id],
                item,
                *(() if detail_document is None else (detail_document,)),
            )
            provenance = tuple(
                SourceProvenance.from_raw(document)
                for document in provenance_documents
            )
            detail_fields = detail.fields if detail is not None else {}
            policies.append(
                ExtractedPolicy(
                    source_id=SOURCE_ID,
                    source_name=SOURCE_NAME,
                    external_id=external_id,
                    title=(
                        detail.title
                        if detail is not None
                        else _present_text(fields.get("policyNm"))
                    ),
                    organization=(
                        detail_fields.get("operating_organization")
                        or detail_fields.get("supervising_organization")
                        or _present_text(fields.get("operInstNm"))
                        or _present_text(fields.get("sprvsnInstNm"))
                    ),
                    summary=_present_text(fields.get("policyCn")),
                    category_text=(
                        detail_fields.get("category_text")
                        or _present_text(fields.get("policyTypeNm"))
                    ),
                    application_period_text=(
                        detail_fields.get("application_period_text")
                        or _period(fields.get("aplyBgngDt"), fields.get("aplyEndDt"))
                    ),
                    region_text=(
                        detail_fields.get("region_text")
                        or _present_text(fields.get("rgnSeNm"))
                    ),
                    age_text=None,
                    eligibility_text=(
                        detail_fields.get("eligibility_text")
                        or _present_text(fields.get("policyScl"))
                    ),
                    support_content=(
                        detail_fields.get("support_content")
                        or _present_text(fields.get("policyCnDtl"))
                        or _present_text(fields.get("policyCn"))
                    ),
                    application_method=detail_fields.get("application_method"),
                    source_url=_canonical_detail_url(external_id),
                    collected_at=max(value.collected_at for value in provenance),
                    provenance=provenance,
                    extra={
                        "selector_contract": COLLECTOR_VERSION,
                        "source_fields": {
                            "list_item": deepcopy(fields),
                            "detail_response": deepcopy(detail_fields) or None,
                        },
                        "institutional_contact": (
                            detail_fields.get("institutional_contact")
                            or _present_text(fields.get("policyEnq"))
                        ),
                        "required_documents": detail_fields.get(
                            "required_documents"
                        ),
                    },
                )
            )
        if set(details) - item_ids:
            raise ExtractionError("orphan Gyeongbuk detail identity")
        return tuple(policies)


def create_gyeongbuk_youth_collector() -> GyeongbukYouthCollector:
    return GyeongbukYouthCollector()


def decide_gyeongbuk_regional_policy(
    policy: ExtractedPolicy,
    *,
    as_of: date | None = None,
) -> RegionalPolicyDecision:
    """Map approved Gyeongbuk fields into the common RYP3 gate."""
    if policy.source_id != SOURCE_ID:
        raise ExtractionError("invalid Gyeongbuk regional policy source")
    source_fields = policy.extra.get("source_fields")
    if not isinstance(source_fields, dict):
        raise ExtractionError("Gyeongbuk regional evidence is missing")
    list_fields = source_fields.get("list_item")
    detail_fields = source_fields.get("detail_response")
    if not isinstance(list_fields, dict):
        raise ExtractionError("Gyeongbuk list evidence is missing")
    detail = detail_fields if isinstance(detail_fields, dict) else {}
    values = {
        "implementing_organization_text": (
            _present_text(detail.get("supervising_organization"))
            or _present_text(list_fields.get("sprvsnInstNm"))
        ),
        "region_eligibility_text": (
            _present_text(detail.get("eligibility_text"))
            or _present_text(list_fields.get("policyScl"))
        ),
        "application_channel_text": (
            _present_text(detail.get("application_method"))
        ),
        "additional_benefit_text": (
            _present_text(detail.get("support_content"))
            or _present_text(list_fields.get("policyCnDtl"))
        ),
        "source_region_text": (
            _present_text(detail.get("region_text"))
            or _present_text(list_fields.get("rgnSeNm"))
        ),
        "application_period_text": _present_text(
            policy.application_period_text
        ),
    }
    locators = {
        "implementing_organization_text": (
            "detail:supervising_organization|list:sprvsnInstNm"
        ),
        "region_eligibility_text": (
            "detail:eligibility_text|list:policyScl"
        ),
        "application_channel_text": "detail:application_method",
        "additional_benefit_text": (
            "detail:support_content|list:policyCnDtl"
        ),
        "source_region_text": "detail:region_text|list:rgnSeNm",
        "application_period_text": (
            "detail:application_period_text|list:aplyBgngDt+aplyEndDt"
        ),
    }
    evidence = RegionalPolicyEvidence(
        **values,
        field_locators=tuple(
            (field_name, locators[field_name])
            for field_name, value in values.items()
            if value is not None
        ),
        provenance=policy.provenance,
    )
    return evaluate_regional_policy(
        policy,
        evidence,
        expected_region_text="경상북도",
        as_of=as_of,
    )


def map_gyeongbuk_duplicate_evidence(
    policy: ExtractedPolicy,
) -> DuplicateEvidence:
    """Map only explicit URLs exposed by the approved Gyeongbuk profile."""
    if policy.source_id != SOURCE_ID:
        raise ExtractionError("invalid Gyeongbuk duplicate evidence source")
    canonical_urls = [policy.source_url]
    locator = "detail:canonical_url"
    if (
        isinstance(policy.application_method, str)
        and policy.application_method.strip().lower().startswith(
            ("http://", "https://")
        )
    ):
        canonical_urls.append(policy.application_method.strip())
        locator += "|detail:application_method"
    return DuplicateEvidence(
        canonical_urls=tuple(canonical_urls),
        field_locators=(("canonical_urls", locator),),
        provenance=policy.provenance,
    )


def _validate_profile(profile: RegionalSourceProfile) -> None:
    if (
        profile.source_id != SOURCE_ID
        or profile.home_url != HOME_URL
        or profile.collection_mode != "http_json"
        or profile.approved_list_urls != (LIST_JSON_URL,)
        or len(profile.approved_detail_url_patterns) != 1
        or not profile.approved_detail_url_patterns[0].startswith(
            f"POST {DETAIL_MODAL_URL} "
        )
    ):
        raise CollectorConfigurationError("Gyeongbuk profile contract drifted")


def _csrf_contract(response: TransportResponse) -> _CsrfContract:
    try:
        parser = _MetaParser()
        parser.feed(response.body.decode("utf-8"))
        parser.close()
        return _CsrfContract(
            header_name=parser.values["_csrf_header"],
            token=parser.values["_csrf"],
        )
    except (UnicodeDecodeError, KeyError):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=HOME_URL,
            response=response,
            reason="home response is missing the CSRF contract",
        ) from None


def _parse_list(response: TransportResponse) -> _ListPayload:
    try:
        payload = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=LIST_JSON_URL,
            response=response,
            reason="list response is not valid JSON",
        ) from None
    if not isinstance(payload, dict):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=LIST_JSON_URL,
            response=response,
            reason="list response root must be an object",
        )
    groups = (payload.get("resultList1"), payload.get("resultList2"))
    if not all(isinstance(group, list) for group in groups):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=LIST_JSON_URL,
            response=response,
            reason="list response is missing regional policy arrays",
        )
    try:
        total_count = int(payload["totCnt1"]) + int(payload["totCnt2"])
    except (KeyError, TypeError, ValueError):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=LIST_JSON_URL,
            response=response,
            reason="list response has invalid total counts",
        ) from None
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in (*groups[0], *groups[1]):
        if not isinstance(value, dict):
            raise safe_parse_error(
                source_id=SOURCE_ID,
                source_url=LIST_JSON_URL,
                response=response,
                reason="policy list contains a non-object item",
            )
        external_id = str(value.get("no", ""))
        if (
            not external_id.isdigit()
            or int(external_id) <= 0
            or not _present_text(value.get("policyNm"))
            or external_id in seen
        ):
            raise safe_parse_error(
                source_id=SOURCE_ID,
                source_url=LIST_JSON_URL,
                response=response,
                reason="policy list identity is invalid or duplicated",
            )
        seen.add(external_id)
        items.append(value)
    if total_count < len(items):
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=LIST_JSON_URL,
            response=response,
            reason="list total count is smaller than the returned items",
        )
    return _ListPayload(items=tuple(items), total_count=total_count)


def _parse_detail(response: TransportResponse) -> _DetailPayload:
    try:
        return _parse_detail_payload(response.body)
    except ExtractionError:
        raise safe_parse_error(
            source_id=SOURCE_ID,
            source_url=DETAIL_MODAL_URL,
            response=response,
            reason="detail selector drifted",
        ) from None


def _parse_detail_payload(payload: bytes) -> _DetailPayload:
    try:
        parser = _DetailParser()
        parser.feed(payload.decode("utf-8"))
        parser.close()
        return parser.payload()
    except UnicodeDecodeError:
        raise ExtractionError("Gyeongbuk detail is not valid UTF-8") from None


def _raw_document(
    *,
    response: TransportResponse,
    role: RawDocumentRole,
    external_id: str | None,
    parent_document_id: str | None,
    collected_at: datetime,
    payload: bytes,
    source_url: str,
    raw_format: RawFormat,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=source_url,
        collected_at=collected_at,
        content_type=response_content_type(
            response,
            default=(
                "application/json; charset=utf-8"
                if raw_format is RawFormat.JSON
                else "text/html; charset=utf-8"
            ),
        ),
        raw_format=raw_format,
        raw_payload=payload,
        http_status=response.status,
        collector_version=COLLECTOR_VERSION,
    )


def _json_object(document: RawPolicyDocument) -> dict[str, Any]:
    try:
        value = json.loads(document.raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExtractionError("Gyeongbuk list item is not valid JSON") from None
    if not isinstance(value, dict):
        raise ExtractionError("Gyeongbuk list item must be an object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _item_title(items: tuple[dict[str, Any], ...], external_id: str) -> str:
    for item in items:
        if str(item.get("no")) == external_id:
            return _present_text(item.get("policyNm")) or ""
    raise AssertionError("unreachable")


def _canonical_detail_url(external_id: str) -> str:
    query = {**LIST_PAGE_QUERY, "no": external_id}
    return f"{LIST_PAGE_URL}?{urllib.parse.urlencode(query)}"


def _list_page_url() -> str:
    return f"{LIST_PAGE_URL}?{urllib.parse.urlencode(LIST_PAGE_QUERY)}"


def _period(start: Any, end: Any) -> str | None:
    start_text = _present_text(start)
    end_text = _present_text(end)
    if start_text and end_text:
        return f"{start_text} ~ {end_text}"
    return start_text or end_text


def _present_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    selected = _clean_text(value)
    return selected or None


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).replace("\xa0", " ").split())
