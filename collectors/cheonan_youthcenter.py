"""Bounded public web collector for the approved Cheonan youth notice."""

from __future__ import annotations

import html
import re
import urllib.parse
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser

from collectors.base import CollectionOptions, CollectionResult
from collectors.config import http_config_from_environment
from collectors.errors import CollectorConfigurationError
from collectors.extracted import (
    ExtractedPolicy,
    ExtractionError,
    SourceProvenance,
)
from collectors.http import HttpClient, HttpClientConfig, TransportResponse
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
    utc_now,
)
from collectors.source_common import response_content_type, safe_parse_error
from collectors.storage import RawDocumentStore


SOURCE_ID = "cheonan-youthcenter-web"
SOURCE_NAME = "천안청년센터이음 공지사항"
SOURCE_ORIGIN = "https://www.ch2030youth.kr"
BOARD_PATH = "/bbs/board.php"
BOARD_URL = f"{SOURCE_ORIGIN}{BOARD_PATH}"
APPROVED_BOARD = "notice"
APPROVED_NOTICE_ID = 674
APPROVED_EXTERNAL_ID = f"notice:{APPROVED_NOTICE_ID}"
COLLECTOR_VERSION = "cheonan-youthcenter-web/1.0"
MIN_REQUEST_INTERVAL_SECONDS = 2.0

LIST_QUERY = {"bo_table": APPROVED_BOARD}
DETAIL_QUERY = {
    "bo_table": APPROVED_BOARD,
    "wr_id": str(APPROVED_NOTICE_ID),
}
CANONICAL_DETAIL_URL = (
    f"{BOARD_URL}?{urllib.parse.urlencode(DETAIL_QUERY)}"
)

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
_BLOCK_TAGS = {
    "article",
    "blockquote",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "tr",
    "ul",
}
_SECTION_KEYS = {
    "모집대상": "eligibility",
    "제출서류": "required_documents",
    "신청방법": "application_method",
    "운영일정": "application_period",
    "지원 기간 및 서비스": "support_content",
    "지원기간 및 서비스": "support_content",
    "지원 예외사항": "excluded_conditions",
    "지원예외사항": "excluded_conditions",
    "기타사항": "other_conditions",
    "문의": "contact",
}


@dataclass(frozen=True, slots=True)
class _ListItem:
    external_id: str
    title: str
    canonical_url: str


@dataclass(frozen=True, slots=True)
class _DetailFields:
    title: str
    published_text: str | None
    introduction: str | None
    sections: dict[str, tuple[str, ...]]


class _ApprovedListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._list_depth: int | None = None
        self._anchor_depth: int | None = None
        self._anchor_text: list[str] = []
        self._items: list[_ListItem] = []
        self._seen_list = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        is_void = tag in _VOID_TAGS
        if self._list_depth is not None and not is_void:
            self._list_depth += 1
        elif values.get("id") == "bo_list":
            if self._seen_list:
                raise ExtractionError("duplicate Cheonan list selector")
            self._seen_list = True
            self._list_depth = 1

        if self._anchor_depth is not None and not is_void:
            self._anchor_depth += 1
        elif self._list_depth is not None and tag == "a":
            href = values.get("href") or ""
            external_id = _approved_external_id(href)
            if external_id is not None:
                self._anchor_depth = 1
                self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._anchor_depth is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if self._anchor_depth is not None:
            self._anchor_depth -= 1
            if self._anchor_depth == 0:
                title = _clean_inline_text("".join(self._anchor_text))
                if not title:
                    raise ExtractionError(
                        "approved Cheonan list item has an empty title"
                    )
                self._items.append(
                    _ListItem(
                        external_id=APPROVED_EXTERNAL_ID,
                        title=title,
                        canonical_url=CANONICAL_DETAIL_URL,
                    )
                )
                self._anchor_depth = None
                self._anchor_text = []

        if self._list_depth is not None:
            self._list_depth -= 1
            if self._list_depth == 0:
                self._list_depth = None

    def approved_item(self) -> _ListItem:
        if not self._seen_list:
            raise ExtractionError("Cheonan list selector drift")
        if len(self._items) != 1:
            raise ExtractionError(
                "Cheonan list must contain exactly one approved notice"
            )
        return self._items[0]


class _DetailParser(HTMLParser):
    _TARGET_IDS = {"bo_v_title", "bo_v_info", "bo_v_con"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depths: dict[str, int] = {}
        self._chunks: dict[str, list[str]] = {
            target: [] for target in self._TARGET_IDS
        }
        self._seen: set[str] = set()
        self._seen_root = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        is_void = tag in _VOID_TAGS
        if not is_void:
            for target in tuple(self._depths):
                self._depths[target] += 1
        if values.get("id") == "bo_v":
            self._seen_root = True
        target = values.get("id")
        if target in self._TARGET_IDS:
            if target in self._seen:
                raise ExtractionError("duplicate Cheonan detail selector")
            self._seen.add(target)
            self._depths[target] = 1
        if tag == "br" or tag in _BLOCK_TAGS:
            for active in self._depths:
                self._chunks[active].append("\n")

    def handle_data(self, data: str) -> None:
        for active in self._depths:
            self._chunks[active].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if tag in _BLOCK_TAGS:
            for active in self._depths:
                self._chunks[active].append("\n")
        for target in tuple(self._depths):
            self._depths[target] -= 1
            if self._depths[target] == 0:
                del self._depths[target]

    def fields(self) -> _DetailFields:
        required = {"bo_v_title", "bo_v_con"}
        if not self._seen_root or not required.issubset(self._seen):
            raise ExtractionError("Cheonan detail selector drift")
        title = _clean_inline_text("".join(self._chunks["bo_v_title"]))
        if not title:
            raise ExtractionError("Cheonan detail title is empty")
        content_lines = _clean_lines(self._chunks["bo_v_con"])
        if not content_lines:
            raise ExtractionError("Cheonan detail content is empty")
        published_text = _published_text(
            _clean_inline_text("".join(self._chunks["bo_v_info"]))
        )
        introduction, sections = _split_sections(content_lines)
        return _DetailFields(
            title=title,
            published_text=published_text,
            introduction=introduction,
            sections=sections,
        )


class CheonanYouthCenterCollector:
    """Collect only the single W4-G0 approved public notice."""

    source_id = SOURCE_ID

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
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
                "cheonan-youthcenter-web only permits page 1"
            )

        list_response = self._http_client.get(
            source_id=self.source_id,
            url=BOARD_URL,
            query=LIST_QUERY,
        )
        try:
            list_item = _parse_approved_list(list_response.body)
        except ExtractionError:
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=BOARD_URL,
                response=list_response,
                reason="approved notice is missing or list selector drifted",
            ) from None

        list_collected_at = self._now()
        list_document = _raw_document(
            response=list_response,
            role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            collected_at=list_collected_at,
            payload=list_response.body,
        )
        item_document = _raw_document(
            response=list_response,
            role=RawDocumentRole.LIST_ITEM,
            external_id=list_item.external_id,
            parent_document_id=list_document.document_id,
            collected_at=list_collected_at,
            payload=_list_item_payload(list_item),
        )
        documents = [list_document, item_document]
        detail_document_ids: list[str] = []
        detail_count = 0

        if selected.detail_limit > 0:
            detail_response = self._http_client.get(
                source_id=self.source_id,
                url=BOARD_URL,
                query=DETAIL_QUERY,
            )
            try:
                _parse_detail(detail_response.body)
            except ExtractionError:
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=BOARD_URL,
                    response=detail_response,
                    reason="approved notice detail selector drifted",
                ) from None
            detail_document = _raw_document(
                response=detail_response,
                role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=list_item.external_id,
                parent_document_id=None,
                collected_at=self._now(),
                payload=detail_response.body,
            )
            documents.append(detail_document)
            detail_document_ids.append(detail_document.document_id)
            detail_count = 1

        stored_paths = tuple(
            self._store.save(document) for document in documents
        )
        return CollectionResult(
            source_id=self.source_id,
            request_count=1 + detail_count,
            item_count=1,
            detail_count=detail_count,
            stored_paths=stored_paths,
            page=1,
            page_size=1,
            total_count=1,
            external_ids=(APPROVED_EXTERNAL_ID,),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_document_ids),
        )


class CheonanYouthCenterExtractor:
    """Interpret approved list and detail HTML without source inference."""

    source_id = SOURCE_ID

    def extract(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[ExtractedPolicy, ...]:
        selected = tuple(documents)
        if any(document.source_id != SOURCE_ID for document in selected):
            raise ExtractionError("Raw document belongs to another source")
        list_document = _single_document(
            selected,
            RawDocumentRole.LIST_RESPONSE,
        )
        item_document = _single_document(
            selected,
            RawDocumentRole.LIST_ITEM,
        )
        detail_document = _single_document(
            selected,
            RawDocumentRole.DETAIL_RESPONSE,
        )
        for document in selected:
            if (
                document.source_type is not SourceType.WEB
                or document.raw_format is not RawFormat.HTML
                or document.source_url != BOARD_URL
            ):
                raise ExtractionError("invalid Cheonan web Raw contract")
        if (
            item_document.parent_document_id != list_document.document_id
            or item_document.external_id != APPROVED_EXTERNAL_ID
            or detail_document.external_id != APPROVED_EXTERNAL_ID
        ):
            raise ExtractionError("Cheonan Raw identity relationship mismatch")

        list_item = _parse_approved_list(item_document.raw_bytes)
        detail = _parse_detail(detail_document.raw_bytes)
        provenance = tuple(
            SourceProvenance.from_raw(document)
            for document in (
                list_document,
                item_document,
                detail_document,
            )
        )
        sections = detail.sections
        public_sections = {
            key: list(values)
            for key, values in sections.items()
            if key != "contact"
        }
        institutional_contact = _institutional_contact(sections)
        return (
            ExtractedPolicy(
                source_id=SOURCE_ID,
                source_name=SOURCE_NAME,
                external_id=APPROVED_EXTERNAL_ID,
                title=detail.title,
                organization="천안청년센터이음",
                summary=detail.introduction,
                category_text=None,
                application_period_text=_joined_section(
                    sections,
                    "application_period",
                ),
                region_text=None,
                age_text=None,
                eligibility_text=_joined_section(
                    sections,
                    "eligibility",
                ),
                support_content=_joined_section(
                    sections,
                    "support_content",
                ),
                application_method=_joined_section(
                    sections,
                    "application_method",
                ),
                source_url=CANONICAL_DETAIL_URL,
                collected_at=max(
                    entry.collected_at for entry in provenance
                ),
                provenance=provenance,
                extra={
                    "selector_contract": COLLECTOR_VERSION,
                    "source_fields": {
                        "list_item": {
                            "title": list_item.title,
                            "canonical_url": list_item.canonical_url,
                        },
                        "detail_response": {
                            "published_text": detail.published_text,
                            "sections": public_sections,
                            "institutional_contact": institutional_contact,
                        },
                    },
                },
            ),
        )


def web_http_config_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
) -> HttpClientConfig:
    base = http_config_from_environment(environ=environ)
    return HttpClientConfig(
        timeout_seconds=base.timeout_seconds,
        max_retries=base.max_retries,
        backoff_seconds=base.backoff_seconds,
        request_interval_seconds=max(
            MIN_REQUEST_INTERVAL_SECONDS,
            base.request_interval_seconds,
        ),
        user_agent=base.user_agent,
    )


def create_cheonan_youthcenter_collector() -> CheonanYouthCenterCollector:
    return CheonanYouthCenterCollector(
        http_client=HttpClient(config=web_http_config_from_environment())
    )


def _raw_document(
    *,
    response: TransportResponse,
    role: RawDocumentRole,
    external_id: str | None,
    parent_document_id: str | None,
    collected_at: datetime,
    payload: bytes,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=BOARD_URL,
        collected_at=collected_at,
        content_type=response_content_type(
            response,
            default="text/html; charset=utf-8",
        ),
        raw_format=RawFormat.HTML,
        raw_payload=payload,
        http_status=response.status,
        collector_version=COLLECTOR_VERSION,
    )


def _parse_approved_list(payload: bytes) -> _ListItem:
    parser = _ApprovedListParser()
    parser.feed(_decode_html(payload))
    parser.close()
    return parser.approved_item()


def _parse_detail(payload: bytes) -> _DetailFields:
    parser = _DetailParser()
    parser.feed(_decode_html(payload))
    parser.close()
    return parser.fields()


def _decode_html(payload: bytes) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        raise ExtractionError("Cheonan HTML is not valid UTF-8") from None


def _approved_external_id(href: str) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(
            urllib.parse.urljoin(SOURCE_ORIGIN, href)
        )
        port = parsed.port
    except ValueError:
        return None
    query = urllib.parse.parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )
    values = dict(query)
    if values.get("wr_id") != str(APPROVED_NOTICE_ID):
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.ch2030youth.kr"
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != BOARD_PATH
        or parsed.fragment
        or query
        != [
            ("bo_table", APPROVED_BOARD),
            ("wr_id", str(APPROVED_NOTICE_ID)),
        ]
    ):
        raise ExtractionError("approved Cheonan notice URL drift")
    return APPROVED_EXTERNAL_ID


def _list_item_payload(item: _ListItem) -> bytes:
    return (
        '<article data-external-id="'
        f'{html.escape(item.external_id, quote=True)}">'
        f'<div id="bo_list"><a href="{html.escape(item.canonical_url, quote=True)}">'
        f"{html.escape(item.title)}</a></div></article>"
    ).encode("utf-8")


def _single_document(
    documents: tuple[RawPolicyDocument, ...],
    role: RawDocumentRole,
) -> RawPolicyDocument:
    selected = [
        document for document in documents if document.document_role is role
    ]
    if len(selected) != 1:
        raise ExtractionError(
            f"Cheonan extraction requires exactly one {role.value}"
        )
    return selected[0]


def _clean_inline_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _clean_lines(chunks: list[str]) -> tuple[str, ...]:
    return tuple(
        line
        for line in (
            _clean_inline_text(value)
            for value in "".join(chunks).splitlines()
        )
        if line
    )


def _published_text(value: str) -> str | None:
    match = re.search(r"\b\d{2}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?\b", value)
    return match.group(0) if match else None


def _split_sections(
    lines: tuple[str, ...],
) -> tuple[str | None, dict[str, tuple[str, ...]]]:
    introduction: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        section = _section_key(line)
        if section is not None:
            current = section
            sections.setdefault(section, [])
            continue
        if current is None:
            introduction.append(line)
        else:
            sections[current].append(line)
    return (
        "\n".join(introduction) or None,
        {key: tuple(values) for key, values in sections.items()},
    )


def _section_key(line: str) -> str | None:
    candidate = re.sub(r"^[○●◦*\-\s]+", "", line).strip()
    candidate = re.sub(r"\([^)]*\)$", "", candidate).strip()
    return _SECTION_KEYS.get(candidate)


def _joined_section(
    sections: Mapping[str, tuple[str, ...]],
    key: str,
) -> str | None:
    values = sections.get(key, ())
    return "\n".join(values) or None


def _institutional_contact(
    sections: Mapping[str, tuple[str, ...]],
) -> dict[str, list[str]]:
    lines = sections.get("contact", ())
    phone_numbers: list[str] = []
    channels: list[str] = []
    for line in lines:
        for match in re.findall(
            r"(?<!\d)0\d{1,2}-\d{3,4}-\d{4}(?!\d)",
            line,
        ):
            if match.startswith(("010-", "011-", "016-", "017-", "018-", "019-")):
                continue
            if match not in phone_numbers:
                phone_numbers.append(match)
        if "카카오채널" in line and "카카오채널" not in channels:
            channels.append("카카오채널")
    return {
        "phone_numbers": phone_numbers,
        "channels": channels,
    }
