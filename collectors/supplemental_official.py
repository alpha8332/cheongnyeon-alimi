"""Offline-replayable adapters for approved supplemental official Sources."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from html.parser import HTMLParser
from typing import Any, Iterable, Mapping

from collectors.base import CollectionOptions, CollectionResult
from collectors.config import http_config_from_environment
from collectors.cross_source_duplicate import DuplicateEvidence
from collectors.errors import CollectorConfigurationError
from collectors.extracted import ExtractedPolicy, ExtractionError, SourceProvenance
from collectors.http import HttpClient, HttpClientConfig, TransportResponse
from collectors.raw import RawDocumentRole, RawFormat, RawPolicyDocument, SourceType
from collectors.raw import utc_now
from collectors.source_common import response_content_type, safe_parse_error
from collectors.storage import RawDocumentStore


WORK24_SOURCE_ID = "work24-policy-web"
LH_SOURCE_ID = "lh-housing-announcement-web"
KOSAF_SOURCE_ID = "kosaf-scholarship-web"
KINFA_SOURCE_ID = "kinfa-financial-product-web"
SUPPLEMENTAL_SOURCE_IDS = frozenset(
    {WORK24_SOURCE_ID, LH_SOURCE_ID, KOSAF_SOURCE_ID, KINFA_SOURCE_ID}
)

WORK24_LIST_URL = "https://www.work24.go.kr/cm/c/f/1100/selecPolicyInfo.do"
WORK24_DETAIL_URL = "https://www.work24.go.kr/cm/c/f/1100/selecSystInfo.do"
LH_LIST_URL = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/"
    "selectWrtancList.do?mi=1026"
)
LH_DETAIL_URL = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/"
    "selectWrtancInfo.do"
)
KOSAF_LIST_URL = (
    "https://www.kosaf.go.kr/ko/scholar.do?pg=scholarship_submain01"
)
KOSAF_DETAIL_URL = "https://www.kosaf.go.kr/ko/scholar.do"
KINFA_LIST_URL = (
    "https://www.kinfa.or.kr/financialProduct/peopleFinancial.do"
)
KINFA_ORIGIN = "https://www.kinfa.or.kr"

ADAPTER_VERSION = "supplemental-official-adapter/1.0"
_WORK24_ID = re.compile(r"^SI\d+$")
_LH_ID = re.compile(r"^\d{10,20}$")
_WORK24_CALL = re.compile(
    r"fn_goPolicyIntro\(\s*['\"]([^'\"]*)['\"]\s*,\s*"
    r"['\"]([^'\"]*)['\"]\s*,\s*['\"](SI\d+)['\"]\s*\)"
)
_KOSAF_APPROVED_KEYS = frozenset(
    {
        "scholarship_submain01",
        "scholarship05_04_01",
        "scholarship05_19_01",
        "scholarship05_18_01",
        "scholarship05_07_01",
        "scholarship05_05_01",
    }
)
_KINFA_APPROVED_KEYS = frozenset(
    {"hessalLoanYoos", "youngFutureLinkLoan"}
)
_KINFA_TITLE_TOKENS = {
    "hessalLoanYoos": "햇살론유스",
    "youngFutureLinkLoan": "청년 미래이음 대출",
}
_VOID_TAGS = frozenset(
    {
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
)


@dataclass(slots=True)
class _Node:
    tag: str
    attrs: dict[str, str]
    parent: _Node | None = None
    children: list[_Node] = field(default_factory=list)
    chunks: list[str] = field(default_factory=list)

    def text(self) -> str:
        values = list(self.chunks)
        values.extend(child.text() for child in self.children)
        return _clean_text(" ".join(values))

    def descendants(self) -> Iterable[_Node]:
        for child in self.children:
            yield child
            yield from child.descendants()


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self._stack = [self.root]
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in {"script", "style", "template", "noscript"}:
            self._ignored_depth += 1
        if self._ignored_depth:
            return
        node = _Node(
            tag=tag,
            attrs={key: value or "" for key, value in attrs},
            parent=self._stack[-1],
        )
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if self._ignored_depth:
            return
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._stack[-1].chunks.append(data)


@dataclass(frozen=True, slots=True)
class SupplementalListItem:
    source_id: str
    external_id: str
    title: str
    canonical_url: str
    source_fields: tuple[tuple[str, str], ...] = ()

    def to_payload(self) -> bytes:
        return json.dumps(
            {
                "adapter_version": ADAPTER_VERSION,
                "source_id": self.source_id,
                "external_id": self.external_id,
                "title": self.title,
                "canonical_url": self.canonical_url,
                "source_fields": dict(self.source_fields),
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")


class SupplementalOutcome(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    REVIEW = "review"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SupplementalDecision:
    source_id: str
    external_id: str
    outcome: SupplementalOutcome
    reason_codes: tuple[str, ...]
    accepted_policy: ExtractedPolicy | None

    @property
    def accepted(self) -> bool:
        return self.accepted_policy is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "external_id": self.external_id,
            "outcome": self.outcome.value,
            "accepted": self.accepted,
            "reason_codes": list(self.reason_codes),
        }


def discover_supplemental_list_items(
    source_id: str, payload: bytes
) -> tuple[SupplementalListItem, ...]:
    """Discover only identities allowed by one approved list contract."""
    root = _parse_html(payload)
    parsers = {
        WORK24_SOURCE_ID: _work24_items,
        LH_SOURCE_ID: _lh_items,
        KOSAF_SOURCE_ID: _kosaf_items,
        KINFA_SOURCE_ID: _kinfa_items,
    }
    try:
        items = parsers[source_id](root)
    except KeyError:
        raise ExtractionError("unsupported supplemental Source") from None
    if not items:
        raise ExtractionError("supplemental list selector drift")
    by_id: dict[str, SupplementalListItem] = {}
    for item in items:
        previous = by_id.get(item.external_id)
        if previous is not None and previous != item:
            raise ExtractionError(
                "supplemental list identity has conflicting evidence"
            )
        by_id[item.external_id] = item
    return tuple(by_id[key] for key in sorted(by_id))


class SupplementalOfficialExtractor:
    """Validate Raw relationships and map source HTML to common evidence."""

    def __init__(self, source_id: str) -> None:
        if source_id not in SUPPLEMENTAL_SOURCE_IDS:
            raise ExtractionError("unsupported supplemental Source")
        self.source_id = source_id

    def extract(
        self, documents: Iterable[RawPolicyDocument]
    ) -> tuple[ExtractedPolicy, ...]:
        selected = tuple(documents)
        if not selected or any(
            document.source_id != self.source_id for document in selected
        ):
            raise ExtractionError("supplemental Raw source mismatch")
        lists = tuple(
            document
            for document in selected
            if document.document_role is RawDocumentRole.LIST_RESPONSE
        )
        if len(lists) != 1:
            raise ExtractionError("supplemental replay requires one list response")
        list_document = lists[0]
        if (
            list_document.source_type is not SourceType.WEB
            or list_document.raw_format is not RawFormat.HTML
            or list_document.source_url != _queryless(_list_url(self.source_id))
        ):
            raise ExtractionError("supplemental list Raw contract drift")
        discovered = {
            item.external_id: item
            for item in discover_supplemental_list_items(
                self.source_id, list_document.raw_bytes
            )
        }
        items = _role_by_identity(
            selected, RawDocumentRole.LIST_ITEM, self.source_id
        )
        details = _roles_by_identity(
            selected, RawDocumentRole.DETAIL_RESPONSE
        )
        if not items or not details or not set(details).issubset(items):
            raise ExtractionError("supplemental list/detail Raw set is incomplete")

        policies: list[ExtractedPolicy] = []
        for external_id in sorted(details):
            item_document = items[external_id]
            detail_documents = details[external_id]
            if (
                item_document.parent_document_id != list_document.document_id
                or item_document.raw_format is not RawFormat.JSON
                or item_document.source_type is not SourceType.WEB
                or any(
                    document.raw_format is not RawFormat.HTML
                    or document.source_type is not SourceType.WEB
                    for document in detail_documents
                )
            ):
                raise ExtractionError("supplemental Raw relationship drift")
            item = _load_item(item_document.raw_bytes)
            expected = discovered.get(external_id)
            if item != expected:
                raise ExtractionError("supplemental list item evidence drift")
            if any(
                document.source_url != _queryless(item.canonical_url)
                for document in detail_documents
            ):
                raise ExtractionError("supplemental detail canonical URL drift")
            policies.append(
                _extract_detail_bundle(
                    item,
                    tuple(
                        document.raw_bytes
                        for document in detail_documents
                    ),
                    tuple(
                        SourceProvenance.from_raw(document)
                        for document in (
                            list_document,
                            item_document,
                            *detail_documents,
                        )
                    ),
                )
            )
        return tuple(policies)


class SupplementalOfficialCollector:
    """Collect one approved landing page and at most three detail responses."""

    source_id: str

    def __init__(
        self,
        source_id: str,
        *,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        if source_id not in SUPPLEMENTAL_SOURCE_IDS:
            raise CollectorConfigurationError(
                "unsupported supplemental Source"
            )
        self.source_id = source_id
        self._http_client = http_client or HttpClient(
            config=supplemental_http_config_from_environment()
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
                "supplemental Source permits one approved list page"
            )
        if selected.detail_limit > 3:
            raise CollectorConfigurationError(
                "supplemental Source permits at most three detail requests"
            )

        list_url = _list_url(self.source_id)
        response = _get_url(
            self._http_client,
            source_id=self.source_id,
            request_url=list_url,
        )
        try:
            discovered = discover_supplemental_list_items(
                self.source_id,
                response.body,
            )
        except ExtractionError:
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=_queryless(list_url),
                response=response,
                reason="supplemental list selector drifted",
            ) from None

        items = discovered[: selected.limit]
        list_collected_at = self._now()
        list_document = _supplemental_raw(
            source_id=self.source_id,
            response=response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=list_url,
            payload=response.body,
            raw_format=RawFormat.HTML,
            collected_at=list_collected_at,
        )
        item_documents = tuple(
            _supplemental_raw(
                source_id=self.source_id,
                response=response,
                role=RawDocumentRole.LIST_ITEM,
                external_id=item.external_id,
                parent_document_id=list_document.document_id,
                source_url=list_url,
                payload=item.to_payload(),
                raw_format=RawFormat.JSON,
                collected_at=list_collected_at,
            )
            for item in items
        )

        detail_documents: list[RawPolicyDocument] = []
        last_detail_response: TransportResponse | None = None
        for item, request_url in _detail_plan(
            self.source_id,
            items,
            detail_limit=selected.detail_limit,
            detail_offset=selected.detail_offset,
        ):
            last_detail_response = _get_url(
                self._http_client,
                source_id=self.source_id,
                request_url=request_url,
            )
            detail_documents.append(
                _supplemental_raw(
                    source_id=self.source_id,
                    response=last_detail_response,
                    role=RawDocumentRole.DETAIL_RESPONSE,
                    external_id=item.external_id,
                    parent_document_id=None,
                    source_url=item.canonical_url,
                    payload=last_detail_response.body,
                    raw_format=RawFormat.HTML,
                    collected_at=self._now(),
                )
            )

        documents = (
            list_document,
            *item_documents,
            *tuple(detail_documents),
        )
        if detail_documents:
            try:
                SupplementalOfficialExtractor(self.source_id).extract(
                    documents
                )
            except ExtractionError:
                assert last_detail_response is not None
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=_queryless(list_url),
                    response=last_detail_response,
                    reason="supplemental detail selector drifted",
                ) from None
        stored_paths = tuple(
            self._store.save(document) for document in documents
        )
        return CollectionResult(
            source_id=self.source_id,
            request_count=1 + len(detail_documents),
            item_count=len(items),
            detail_count=len(detail_documents),
            stored_paths=stored_paths,
            page=1,
            page_size=selected.limit,
            total_count=len(discovered),
            external_ids=tuple(item.external_id for item in items),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(
                document.document_id for document in detail_documents
            ),
        )


def supplemental_http_config_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
) -> HttpClientConfig:
    base = http_config_from_environment(environ=environ)
    return HttpClientConfig(
        timeout_seconds=base.timeout_seconds,
        max_retries=base.max_retries,
        backoff_seconds=base.backoff_seconds,
        request_interval_seconds=max(
            2.0,
            base.request_interval_seconds,
        ),
        user_agent=base.user_agent,
    )


def create_supplemental_official_collector(
    source_id: str,
) -> SupplementalOfficialCollector:
    return SupplementalOfficialCollector(source_id)


def decide_supplemental_policy(
    policy: ExtractedPolicy, *, as_of: date | None = None
) -> SupplementalDecision:
    """Reject closed or insufficient evidence before Policy persistence."""
    if policy.source_id not in SUPPLEMENTAL_SOURCE_IDS:
        raise ExtractionError("supplemental decision source is unsupported")
    evidence = policy.extra.get("supplemental_evidence")
    if not isinstance(evidence, Mapping):
        return _decision(
            policy,
            SupplementalOutcome.FAILED,
            "evidence_contract_missing",
        )
    required = {
        "youth_target",
        "application_availability",
        "organization",
        "eligibility",
        "required_documents",
        "application_method",
    }
    if set(evidence) != required:
        return _decision(policy, SupplementalOutcome.FAILED, "evidence_contract_drift")
    availability = _resolved_availability(
        str(evidence["application_availability"]),
        policy.application_period_text,
        as_of or policy.collected_at.date(),
    )
    if availability == "closed":
        return _decision(policy, SupplementalOutcome.CLOSED, "application_closed")
    if availability != "open":
        return _decision(
            policy, SupplementalOutcome.REVIEW, "application_availability_unconfirmed"
        )
    missing = tuple(
        name
        for name in (
            "youth_target",
            "organization",
            "eligibility",
            "required_documents",
            "application_method",
        )
        if evidence[name] != "confirmed"
    )
    if missing:
        return SupplementalDecision(
            source_id=policy.source_id,
            external_id=policy.external_id,
            outcome=SupplementalOutcome.REVIEW,
            reason_codes=tuple(f"{name}_unconfirmed" for name in missing),
            accepted_policy=None,
        )
    return SupplementalDecision(
        source_id=policy.source_id,
        external_id=policy.external_id,
        outcome=SupplementalOutcome.ACCEPTED,
        reason_codes=("minimum_official_evidence_confirmed",),
        accepted_policy=policy,
    )


def map_supplemental_duplicate_evidence(
    policy: ExtractedPolicy,
) -> DuplicateEvidence:
    if policy.source_id not in SUPPLEMENTAL_SOURCE_IDS:
        raise ExtractionError("supplemental duplicate source is unsupported")
    return DuplicateEvidence(
        canonical_urls=(policy.source_url,),
        field_locators=(("canonical_urls", "detail_response:canonical_url"),),
        provenance=policy.provenance,
    )


def _work24_items(root: _Node) -> tuple[SupplementalListItem, ...]:
    items: list[SupplementalListItem] = []
    for node in root.descendants():
        if node.tag != "a":
            continue
        match = _WORK24_CALL.search(html.unescape(node.attrs.get("onclick", "")))
        title = _clean_list_title(node.text())
        if match is None or not title:
            continue
        _, syst_class_id, external_id = match.groups()
        if not _WORK24_ID.fullmatch(external_id):
            continue
        query = {"systId": external_id}
        if syst_class_id:
            query["systClId"] = syst_class_id
        items.append(
            SupplementalListItem(
                WORK24_SOURCE_ID,
                external_id,
                title,
                f"{WORK24_DETAIL_URL}?{urllib.parse.urlencode(query)}",
                (("systClId", syst_class_id),),
            )
        )
    return tuple(items)


def _lh_items(root: _Node) -> tuple[SupplementalListItem, ...]:
    items: list[SupplementalListItem] = []
    for node in root.descendants():
        classes = set(node.attrs.get("class", "").split())
        if node.tag != "a" or "wrtancInfoBtn" not in classes:
            continue
        external_id = node.attrs.get("data-id1", "")
        title = _clean_list_title(node.text())
        codes = {
            "ccrCnntSysDsCd": node.attrs.get("data-id2", ""),
            "uppAisTpCd": node.attrs.get("data-id3", ""),
            "aisTpCd": node.attrs.get("data-id4", ""),
        }
        if not _LH_ID.fullmatch(external_id) or not title or any(
            not value for value in codes.values()
        ):
            continue
        query = {"mi": "1026", "panId": external_id, **codes}
        items.append(
            SupplementalListItem(
                LH_SOURCE_ID,
                external_id,
                title,
                f"{LH_DETAIL_URL}?{urllib.parse.urlencode(query)}",
                tuple(sorted(codes.items())),
            )
        )
    return tuple(items)


def _kosaf_items(root: _Node) -> tuple[SupplementalListItem, ...]:
    items: list[SupplementalListItem] = []
    for node in root.descendants():
        if node.tag != "a":
            continue
        parsed = urllib.parse.urlsplit(
            urllib.parse.urljoin("https://www.kosaf.go.kr", node.attrs.get("href", ""))
        )
        query = dict(urllib.parse.parse_qsl(parsed.query))
        key = query.get("pg", "")
        title = node.text()
        if (
            key not in _KOSAF_APPROVED_KEYS
            or not title
            or title == "소개"
            or set(query) - {"pg", "naviParam", "yr", "smtr"}
        ):
            continue
        items.append(
            SupplementalListItem(
                KOSAF_SOURCE_ID,
                key,
                title,
                f"{KOSAF_DETAIL_URL}?{urllib.parse.urlencode({'pg': key})}",
            )
        )
    return tuple(items)


def _kinfa_items(root: _Node) -> tuple[SupplementalListItem, ...]:
    items: list[SupplementalListItem] = []
    for node in root.descendants():
        if node.tag != "a":
            continue
        parsed = urllib.parse.urlsplit(
            urllib.parse.urljoin(KINFA_ORIGIN, node.attrs.get("href", ""))
        )
        match = re.fullmatch(r"/financialProduct/([A-Za-z0-9_-]+)\.do", parsed.path)
        title = node.text()
        if match is None or match.group(1) not in _KINFA_APPROVED_KEYS or not title:
            continue
        key = match.group(1)
        title = title.removeprefix("자세히 보기 ").strip()
        if _KINFA_TITLE_TOKENS[key] not in title:
            continue
        items.append(
            SupplementalListItem(
                KINFA_SOURCE_ID,
                key,
                title,
                f"{KINFA_ORIGIN}{parsed.path}",
            )
        )
    return tuple(items)


def _extract_detail_bundle(
    item: SupplementalListItem,
    payloads: tuple[bytes, ...],
    provenance: tuple[SourceProvenance, ...],
) -> ExtractedPolicy:
    parser = {
        WORK24_SOURCE_ID: _work24_detail,
        LH_SOURCE_ID: _lh_detail,
        KOSAF_SOURCE_ID: _kosaf_detail,
        KINFA_SOURCE_ID: _kinfa_detail,
    }[item.source_id]
    parsed = tuple(parser(_parse_html(payload), item) for payload in payloads)
    values = _merge_detail_values(tuple(value for value, _ in parsed))
    locators: dict[str, str] = {}
    for index, (detail_values, fields) in enumerate(parsed):
        for field_name, locator in fields.items():
            if detail_values.get(field_name) not in (None, "", ()):
                locators.setdefault(
                    field_name,
                    f"detail_response[{index}]:{locator}",
                )
    title = values.get("title")
    if not title or _comparison_text(title) != _comparison_text(item.title):
        raise ExtractionError("supplemental detail title drift")
    evidence = {
        "youth_target": _confirmed(values.get("youth_target")),
        "application_availability": values.get("application_availability", "unknown"),
        "organization": _confirmed(values.get("organization")),
        "eligibility": _confirmed(values.get("eligibility")),
        "required_documents": _confirmed(values.get("required_documents")),
        "application_method": _confirmed(values.get("application_method")),
    }
    return ExtractedPolicy(
        source_id=item.source_id,
        source_name=_source_name(item.source_id),
        external_id=item.external_id,
        title=title,
        organization=values.get("organization"),
        summary=values.get("summary"),
        category_text=values.get("category"),
        application_period_text=values.get("application_period"),
        region_text=values.get("region"),
        age_text=values.get("age"),
        eligibility_text=values.get("eligibility"),
        support_content=values.get("support_content"),
        application_method=values.get("application_method"),
        source_url=item.canonical_url,
        collected_at=max(value.collected_at for value in provenance),
        provenance=provenance,
        target_groups=tuple(values.get("target_groups", ())),
        extra={
            "adapter_version": ADAPTER_VERSION,
            "field_locators": locators,
            "required_documents": values.get("required_documents"),
            "supplemental_evidence": evidence,
            "source_fields": dict(item.source_fields),
        },
    )


def _work24_detail(
    root: _Node, item: SupplementalListItem
) -> tuple[dict[str, Any], dict[str, str]]:
    identity = _one(root, "input", attr=("id", "systId"))
    if identity is None or identity.attrs.get("value") != item.external_id:
        raise ExtractionError("Work24 detail identity drift")
    title_node = _matching_text_node(root, "h2", item.title, class_name="h2_sb")
    overview = _one(root, "div", attr=("id", "iemVal0"))
    support = _one(root, "div", attr=("id", "iemVal1"))
    eligibility = _one(root, "div", attr=("id", "iemVal2"))
    documents = _labeled_section(root, ("제출서류", "필요서류"))
    method = _labeled_section(root, ("신청방법",))
    period = _labeled_section(root, ("신청기간", "접수기간"))
    values = {
        "title": _node_text(title_node),
        "organization": "고용노동부·한국고용정보원",
        "summary": _node_text(overview),
        "support_content": _node_text(support),
        "eligibility": _node_text(eligibility),
        "required_documents": documents,
        "application_method": method,
        "application_period": period,
        "youth_target": _youth_evidence(title_node, eligibility),
        "application_availability": _availability(period),
        "target_groups": ("청년",) if _youth_evidence(title_node, eligibility) else (),
    }
    return values, {
        "title": "form#HPCMCF1100VO h2.h2_sb",
        "summary": "#iemVal0",
        "support_content": "#iemVal1",
        "eligibility": "#iemVal2",
    }


def _lh_detail(
    root: _Node, item: SupplementalListItem
) -> tuple[dict[str, Any], dict[str, str]]:
    view = _one(root, "div", class_name="bbs_ViewA")
    if view is None:
        raise ExtractionError("LH detail selector drift")
    title_node = _first_nonempty(view, "h3")
    status = _strong_value(view, "공고상태")
    period_node = _one(view, "label", attr=("id", "sta_acpDt"))
    period = _node_text(period_node)
    values = {
        "title": _node_text(title_node),
        "organization": "한국토지주택공사",
        "category": _strong_value(view, "유형"),
        "application_period": period,
        "region": _labeled_section(view, ("지역", "소재지")),
        "eligibility": _labeled_section(view, ("신청자격", "입주자격")),
        "support_content": _labeled_section(view, ("공급정보", "지원내용")),
        "required_documents": _labeled_section(view, ("제출서류", "필요서류")),
        "application_method": _labeled_section(view, ("접수처정보", "신청방법")),
        "youth_target": _youth_evidence(title_node),
        "application_availability": (
            "closed" if status and "마감" in status else _availability(period)
        ),
        "target_groups": ("청년",) if _youth_evidence(title_node) else (),
    }
    return values, {
        "title": ".bbs_ViewA > h3",
        "application_status": ".bbsV_data strong:공고상태",
        "application_period": "#sta_acpDt",
    }


def _kosaf_detail(
    root: _Node, item: SupplementalListItem
) -> tuple[dict[str, Any], dict[str, str]]:
    title_node = _current_anchor(root, item.external_id) or _title_prefix(root)
    period_parts = _labeled_sections(
        root,
        ("신청기간", "사업기간"),
        ancestor_class="page-group",
    )
    period = " | ".join(period_parts) or None
    eligibility = _kosaf_tab_text(
        root,
        ("신청대상", "지원자격"),
    )
    method = _kosaf_application_method(root)
    values = {
        "title": _node_text(title_node),
        "organization": "한국장학재단",
        "category": "장학금",
        "application_period": period,
        "eligibility": eligibility,
        "support_content": _kosaf_tab_text(
            root,
            ("장학금 지원금액", "지원금액"),
        ),
        "required_documents": _kosaf_tab_text(
            root,
            ("제출서류",),
        ),
        "application_method": method,
        "youth_target": _kosaf_youth_evidence(title_node, eligibility),
        "application_availability": _availability(period),
        "target_groups": ("대학생",) if eligibility and "학생" in eligibility else (),
    }
    return values, {
        "title": f"a[href*='pg={item.external_id}'][aria-current=page]",
        "application_period": "heading:신청기간|사업기간 + block",
        "eligibility": "heading:신청대상|지원자격 + block",
        "required_documents": "heading:제출서류 + block",
    }


def _kinfa_detail(
    root: _Node, item: SupplementalListItem
) -> tuple[dict[str, Any], dict[str, str]]:
    title_node = _title_prefix(root)
    eligibility = _kinfa_eligibility(root)
    documents = _labeled_card(root, ("제출 필요서류", "제출서류"))
    method = _labeled_card(root, ("이용절차", "신청방법"))
    period = _labeled_section(root, ("신청기간", "접수기간"))
    if period is None and method and "신청 가능" in method:
        period = method
    values = {
        "title": _node_text(title_node),
        "organization": "서민금융진흥원",
        "category": "금융·자산 형성 지원",
        "application_period": period,
        "eligibility": eligibility,
        "support_content": _labeled_card(
            root,
            ("보증한도 및 보증기간", "대출한도", "지원내용"),
        ),
        "required_documents": documents,
        "application_method": method,
        "youth_target": _youth_evidence(title_node, eligibility),
        "application_availability": _availability(period),
        "target_groups": ("청년",) if _youth_evidence(title_node, eligibility) else (),
    }
    return values, {
        "title": "head > title:first-segment",
        "eligibility": "heading:보증대상|지원대상 + block",
        "required_documents": "heading:제출서류|필요서류 + block",
    }


def _parse_html(payload: bytes) -> _Node:
    try:
        value = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise ExtractionError("supplemental HTML is not valid UTF-8") from None
    parser = _TreeParser()
    parser.feed(value)
    parser.close()
    return parser.root


def _role_by_identity(
    documents: tuple[RawPolicyDocument, ...],
    role: RawDocumentRole,
    source_id: str,
) -> dict[str, RawPolicyDocument]:
    values: dict[str, RawPolicyDocument] = {}
    for document in documents:
        if document.document_role is not role:
            continue
        external_id = document.external_id
        if not external_id or external_id in values:
            raise ExtractionError("supplemental Raw identity is missing or duplicated")
        values[external_id] = document
    return values


def _roles_by_identity(
    documents: tuple[RawPolicyDocument, ...],
    role: RawDocumentRole,
) -> dict[str, tuple[RawPolicyDocument, ...]]:
    grouped: dict[str, list[RawPolicyDocument]] = {}
    for document in documents:
        if document.document_role is not role:
            continue
        external_id = document.external_id
        if not external_id:
            raise ExtractionError("supplemental Raw identity is missing")
        grouped.setdefault(external_id, []).append(document)
    return {
        external_id: tuple(
            sorted(
                values,
                key=lambda document: (
                    document.collected_at,
                    document.document_id,
                ),
            )
        )
        for external_id, values in grouped.items()
    }


def _merge_detail_values(
    values: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for fields in values:
        for field_name, value in fields.items():
            if value in (None, "", ()):
                continue
            if field_name == "target_groups":
                existing = tuple(merged.get(field_name, ()))
                merged[field_name] = tuple(
                    dict.fromkeys((*existing, *tuple(value)))
                )
                continue
            if field_name == "application_availability":
                existing = merged.get(field_name)
                if existing in {None, "unknown"} or value == "open":
                    merged[field_name] = value
                continue
            merged.setdefault(field_name, value)
    return merged


def _load_item(payload: bytes) -> SupplementalListItem:
    try:
        value = json.loads(payload)
        if set(value) != {
            "adapter_version",
            "source_id",
            "external_id",
            "title",
            "canonical_url",
            "source_fields",
        } or value["adapter_version"] != ADAPTER_VERSION:
            raise ValueError
        fields = value["source_fields"]
        if not isinstance(fields, dict):
            raise ValueError
        return SupplementalListItem(
            source_id=value["source_id"],
            external_id=value["external_id"],
            title=value["title"],
            canonical_url=value["canonical_url"],
            source_fields=tuple(sorted(fields.items())),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ExtractionError("supplemental list item payload drift") from None


def _list_url(source_id: str) -> str:
    return {
        WORK24_SOURCE_ID: WORK24_LIST_URL,
        LH_SOURCE_ID: LH_LIST_URL,
        KOSAF_SOURCE_ID: KOSAF_LIST_URL,
        KINFA_SOURCE_ID: KINFA_LIST_URL,
    }[source_id]


def _source_name(source_id: str) -> str:
    return {
        WORK24_SOURCE_ID: "고용24 정책",
        LH_SOURCE_ID: "LH청약플러스 임대주택 공고",
        KOSAF_SOURCE_ID: "한국장학재단 장학금",
        KINFA_SOURCE_ID: "서민금융진흥원 금융상품",
    }[source_id]


def _get_url(
    http_client: HttpClient,
    *,
    source_id: str,
    request_url: str,
) -> TransportResponse:
    parsed = urllib.parse.urlsplit(request_url)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    return http_client.get(
        source_id=source_id,
        url=urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, "", "")
        ),
        query=query,
    )


def _detail_plan(
    source_id: str,
    items: tuple[SupplementalListItem, ...],
    *,
    detail_limit: int,
    detail_offset: int,
) -> tuple[tuple[SupplementalListItem, str], ...]:
    if detail_limit == 0:
        return ()
    if source_id == KOSAF_SOURCE_ID:
        preferred = next(
            (
                item
                for item in items
                if item.external_id == "scholarship05_04_01"
            ),
            None,
        )
        if preferred is None or detail_offset:
            return ()
        return tuple(
            (preferred, request_url)
            for request_url in (
                preferred.canonical_url,
                f"{preferred.canonical_url}&ttab1=3",
                f"{preferred.canonical_url}&ttab1=4",
            )[:detail_limit]
        )

    youth_tokens = ("청년", "대학생", "유스", "신혼", "행복주택")
    ordered = tuple(
        sorted(
            items,
            key=lambda item: (
                not any(token in item.title for token in youth_tokens),
                item.external_id,
            ),
        )
    )
    selected = ordered[detail_offset : detail_offset + detail_limit]
    return tuple((item, item.canonical_url) for item in selected)


def _supplemental_raw(
    *,
    source_id: str,
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
        source_url=_queryless(source_url),
        collected_at=collected_at,
        content_type=(
            "application/json; charset=utf-8"
            if raw_format is RawFormat.JSON
            else response_content_type(
                response,
                default="text/html; charset=utf-8",
            )
        ),
        raw_format=raw_format,
        raw_payload=payload,
        http_status=response.status,
        collector_version=ADAPTER_VERSION,
    )


def _queryless(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "", "")
    )


def _one(
    root: _Node,
    tag: str,
    *,
    class_name: str | None = None,
    attr: tuple[str, str] | None = None,
) -> _Node | None:
    matches = [
        node
        for node in root.descendants()
        if node.tag == tag
        and (class_name is None or class_name in node.attrs.get("class", "").split())
        and (attr is None or node.attrs.get(attr[0]) == attr[1])
    ]
    if len(matches) > 1:
        raise ExtractionError("supplemental detail selector is ambiguous")
    return matches[0] if matches else None


def _first_nonempty(
    root: _Node, tag: str, *, class_name: str | None = None
) -> _Node | None:
    for node in root.descendants():
        if (
            node.tag == tag
            and (
                class_name is None
                or class_name in node.attrs.get("class", "").split()
            )
            and node.text()
        ):
            return node
    return None


def _matching_text_node(
    root: _Node,
    tag: str,
    expected: str,
    *,
    class_name: str | None = None,
) -> _Node | None:
    for node in root.descendants():
        if (
            node.tag == tag
            and (
                class_name is None
                or class_name in node.attrs.get("class", "").split()
            )
            and _comparison_text(node.text()) == _comparison_text(expected)
        ):
            return node
    return None


def _current_anchor(root: _Node, key: str) -> _Node | None:
    for node in root.descendants():
        if node.tag != "a" or node.attrs.get("aria-current") != "page":
            continue
        query = dict(
            urllib.parse.parse_qsl(
                urllib.parse.urlsplit(html.unescape(node.attrs.get("href", ""))).query
            )
        )
        if query.get("pg") == key:
            return node
    return None


def _title_prefix(root: _Node) -> _Node | None:
    node = _one(root, "title")
    if node is None:
        return None
    node.chunks = [node.text().split(">", 1)[0].strip()]
    node.children = []
    return node


def _labeled_section(
    root: _Node,
    labels: tuple[str, ...],
    *,
    ancestor_class: str | None = None,
) -> str | None:
    values = _labeled_sections(
        root,
        labels,
        ancestor_class=ancestor_class,
    )
    return values[0] if values else None


def _labeled_sections(
    root: _Node,
    labels: tuple[str, ...],
    *,
    ancestor_class: str | None = None,
) -> tuple[str, ...]:
    heading_tags = {
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "dt",
        "strong",
        "p",
        "span",
        "li",
        "caption",
    }
    selected: list[str] = []
    for node in root.descendants():
        own_text = _clean_text(" ".join(node.chunks)).rstrip(":")
        matched_label = next(
            (label for label in labels if label in own_text),
            None,
        )
        if (
            node.tag not in heading_tags
            or matched_label is None
            or ancestor_class is not None
            and not _has_ancestor_class(node, ancestor_class)
        ):
            continue
        remainder = _clean_text(
            own_text.split(matched_label, 1)[1].lstrip(":() ")
        )
        semantic_remainder = remainder
        for label in labels:
            semantic_remainder = semantic_remainder.replace(label, "")
        semantic_remainder = re.sub(r"[\s:()/·]+", "", semantic_remainder)
        if semantic_remainder:
            value = _clean_text(
                node.text().split(matched_label, 1)[1].lstrip(":() ")
            )
            if value and value not in selected:
                selected.append(value)
            continue
        parent = node.parent
        if parent is None:
            continue
        parent_text = parent.text()
        value = _clean_text(parent_text.removeprefix(node.text()))
        if value and value != parent_text:
            if value not in selected:
                selected.append(value)
            continue
        siblings = parent.children
        try:
            index = siblings.index(node)
        except ValueError:
            continue
        for sibling in siblings[index + 1 :]:
            value = sibling.text()
            if value:
                if value not in selected:
                    selected.append(value)
                break
    return tuple(selected)


def _has_ancestor_class(node: _Node, class_name: str) -> bool:
    current = node.parent
    while current is not None:
        if any(
            token.casefold().rstrip("s")
            == class_name.casefold().rstrip("s")
            for token in current.attrs.get("class", "").split()
        ):
            return True
        current = current.parent
    return False


def _nearest_ancestor_class(node: _Node, class_name: str) -> _Node | None:
    current = node.parent
    while current is not None:
        if class_name in current.attrs.get("class", "").split():
            return current
        current = current.parent
    return None


def _labeled_card(root: _Node, labels: tuple[str, ...]) -> str | None:
    for node in root.descendants():
        if node.tag != "p" or "tit" not in node.attrs.get("class", "").split():
            continue
        title = node.text()
        if not any(label in title for label in labels):
            continue
        card = _nearest_ancestor_class(node, "card-01")
        if card is not None:
            value = _clean_text(
                card.text().removeprefix(title).replace("닫힘", "", 1)
            )
            if value:
                return value
    return _labeled_section(root, labels)


def _kinfa_eligibility(root: _Node) -> str | None:
    direct = _labeled_section(
        root,
        ("보증대상", "지원대상", "신청대상"),
    )
    if direct:
        return direct
    for node in root.descendants():
        classes = set(node.attrs.get("class", "").split())
        text = node.text()
        if (
            node.tag == "div"
            and {"card", "card-01"}.issubset(classes)
            and "청년" in text
            and "대학생" in text
        ):
            return text
    return None


def _kosaf_application_method(root: _Node) -> str | None:
    for node in root.descendants():
        if node.tag != "a" or node.text() != "신청하기":
            continue
        action = node.attrs.get("href", "")
        if "PTJH_SCRSAPLY" in action:
            return "한국장학재단 장학금 신청 메뉴에서 신청"
    return _labeled_section(root, ("신청방법",))


def _kosaf_tab_text(root: _Node, labels: tuple[str, ...]) -> str | None:
    for node in root.descendants():
        if node.tag not in {"h5", "h6", "caption"}:
            continue
        title = node.text()
        if not any(label in title for label in labels):
            continue
        tab = _nearest_ancestor_class(node, "con_tabitem")
        if tab is not None:
            value = _clean_text(tab.text().replace(title, "", 1))
            if value:
                return value
    return _labeled_section(
        root,
        labels,
        ancestor_class="page-group",
    )


def _kosaf_youth_evidence(
    title_node: _Node | None,
    eligibility: str | None,
) -> str | None:
    direct = _youth_evidence(title_node, eligibility)
    if direct:
        return direct
    if eligibility and "학생" in eligibility and "대학" in eligibility:
        return eligibility
    return None


def _strong_value(root: _Node, label: str) -> str | None:
    for node in root.descendants():
        if node.tag == "strong" and node.text().rstrip(":") == label:
            parent = node.parent
            if parent is not None:
                value = _clean_text(parent.text().removeprefix(node.text()))
                return value or None
    return None


def _availability(period: str | None) -> str:
    if not period:
        return "unknown"
    if _date_ranges(period):
        return "dated"
    if any(token in period for token in ("마감", "종료", "신청불가")):
        return "closed"
    if any(token in period for token in ("상시", "수시", "신청 가능", "접수중")):
        return "open"
    return "unknown"


def _resolved_availability(
    status: str, period: str | None, as_of: date
) -> str:
    if status != "dated" or not period:
        return status
    ranges = _date_ranges(period)
    if not ranges:
        return "unknown"
    if any(start <= as_of <= end for start, end in ranges):
        return "open"
    if all(as_of > end for _, end in ranges):
        return "closed"
    return "unknown"


def _date_ranges(value: str) -> tuple[tuple[date, date], ...]:
    pattern = re.compile(
        r"(?P<sy>20\d{2})[.\-/]\s*(?P<sm>\d{1,2})[.\-/]\s*"
        r"(?P<sd>\d{1,2})[^~|]{0,30}~\s*"
        r"(?:(?P<ey>20\d{2})[.\-/]\s*)?"
        r"(?P<em>\d{1,2})[.\-/]\s*(?P<ed>\d{1,2})"
    )
    selected: list[tuple[date, date]] = []
    for match in pattern.finditer(value):
        try:
            start = date(
                int(match.group("sy")),
                int(match.group("sm")),
                int(match.group("sd")),
            )
            end = date(
                int(match.group("ey") or match.group("sy")),
                int(match.group("em")),
                int(match.group("ed")),
            )
        except ValueError:
            continue
        if start <= end:
            selected.append((start, end))
    return tuple(selected)


def _youth_evidence(*values: _Node | str | None) -> str | None:
    text = " ".join(
        value.text() if isinstance(value, _Node) else value or "" for value in values
    )
    return (
        text
        if any(
            token in text
            for token in ("청년", "대학생", "고등학생", "유스")
        )
        else None
    )


def _confirmed(value: Any) -> str:
    return (
        "confirmed"
        if isinstance(value, str) and bool(value.strip())
        else "unconfirmed"
    )


def _decision(
    policy: ExtractedPolicy, outcome: SupplementalOutcome, reason: str
) -> SupplementalDecision:
    return SupplementalDecision(
        source_id=policy.source_id,
        external_id=policy.external_id,
        outcome=outcome,
        reason_codes=(reason,),
        accepted_policy=None,
    )


def _node_text(node: _Node | None) -> str | None:
    if node is None:
        return None
    value = node.text()
    return value or None


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def _clean_list_title(value: str) -> str:
    selected = _clean_text(value)
    return re.sub(r"\s+(?:new|\d+일전)$", "", selected, flags=re.IGNORECASE)


def _comparison_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", value).casefold()
