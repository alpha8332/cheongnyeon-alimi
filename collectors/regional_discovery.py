"""Bounded semantic discovery for public regional policy fixtures."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser

from collectors.regional_profile import RegionalAction


_MENU_KEYWORDS = ("청년정책", "정책지원", "지원정책", "정책")
_DETAIL_KEYWORDS = ("지원", "사업", "정책", "모집")
_FIELD_ALIASES = {
    "정책명": "title",
    "사업명": "title",
    "주관기관": "organization",
    "운영기관": "organization",
    "정책유형": "category_text",
    "신청기간": "application_period_text",
    "지원대상": "eligibility_text",
    "지원규모": "eligibility_text",
    "지원내용": "support_content",
    "정책내용 상세": "support_content",
    "신청방법": "application_method",
    "지역구분": "region_text",
    "문의처": "institutional_contact",
    "제출서류": "required_documents",
    "첨부파일": "required_documents",
}
_SEMANTIC_TAGS = {"h1", "h2", "h3", "h4", "dt", "dd", "th", "td", "p", "li"}
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
_EXTERNAL_ID_KEYS = ("no", "id", "bizId", "policy_no", "wr_id", "arcNo")


class DiscoveryDriftError(ValueError):
    """Discovery or replay failed before reaching a policy detail."""


@dataclass(frozen=True, slots=True)
class DiscoveredActionProfile:
    home_url: str
    actions: tuple[RegionalAction, ...]
    sample_external_id: str
    sample_title: str


@dataclass(frozen=True, slots=True)
class DiscoveredPolicyCandidate:
    external_id: str
    title: str
    detail_url: str
    fields: dict[str, str]


class BrowserDiscoveryEngine:
    """Discover and replay a same-host home → list → detail path."""

    def discover(
        self,
        *,
        home_url: str,
        pages: Mapping[str, bytes | str],
    ) -> DiscoveredActionProfile:
        home = _page(pages, home_url)
        home_parser = _SemanticHtmlParser(home)
        menu_text, list_url = _best_link(
            home_parser.links,
            base_url=home_url,
            pages=pages,
            keywords=_MENU_KEYWORDS,
        )
        list_parser = _SemanticHtmlParser(_page(pages, list_url))
        detail_title, detail_url = _best_link(
            list_parser.links,
            base_url=list_url,
            pages=pages,
            keywords=_DETAIL_KEYWORDS,
        )
        detail = _candidate(detail_url, detail_title, pages)
        return DiscoveredActionProfile(
            home_url=home_url,
            actions=(
                RegionalAction("goto", home_url, None),
                RegionalAction("click", menu_text, None),
                RegionalAction("observe_list", list_url, None),
                RegionalAction("observe_detail", detail_url, None),
            ),
            sample_external_id=detail.external_id,
            sample_title=detail.title,
        )

    def replay(
        self,
        profile: DiscoveredActionProfile,
        *,
        pages: Mapping[str, bytes | str],
    ) -> DiscoveredPolicyCandidate:
        if len(profile.actions) != 4:
            raise DiscoveryDriftError("discovery action count drifted")
        goto, click, observe_list, observe_detail = profile.actions
        if (
            goto.kind != "goto"
            or goto.target != profile.home_url
            or click.kind != "click"
            or observe_list.kind != "observe_list"
            or observe_detail.kind != "observe_detail"
        ):
            raise DiscoveryDriftError("discovery action sequence drifted")
        home_parser = _SemanticHtmlParser(_page(pages, goto.target))
        if not _has_link(home_parser.links, goto.target, observe_list.target):
            raise DiscoveryDriftError("policy menu link drifted")
        list_parser = _SemanticHtmlParser(_page(pages, observe_list.target))
        if not _has_link(
            list_parser.links,
            observe_list.target,
            observe_detail.target,
        ):
            raise DiscoveryDriftError("policy detail link drifted")
        detail = _candidate(
            observe_detail.target,
            profile.sample_title,
            pages,
        )
        if (
            detail.external_id != profile.sample_external_id
            or detail.title != profile.sample_title
        ):
            raise DiscoveryDriftError("policy detail identity drifted")
        return detail


class _SemanticHtmlParser(HTMLParser):
    def __init__(self, payload: str) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.elements: list[tuple[str, str]] = []
        self._tag: str | None = None
        self._depth = 0
        self._chunks: list[str] = []
        self._href: str | None = None
        self.feed(payload)
        self.close()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in _VOID_TAGS:
            return
        if self._tag is not None:
            self._depth += 1
            return
        if tag == "a" or tag in _SEMANTIC_TAGS:
            self._tag = tag
            self._depth = 1
            self._chunks = []
            self._href = dict(attrs).get("href") if tag == "a" else None

    def handle_data(self, data: str) -> None:
        if self._tag is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if self._tag is None:
            return
        self._depth -= 1
        if self._depth > 0:
            return
        text = _clean("".join(self._chunks))
        if self._tag == "a" and self._href and text:
            self.links.append((text, self._href))
        elif text:
            self.elements.append((self._tag, text))
        self._tag = None
        self._chunks = []
        self._href = None

    def fields(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for index, (tag, label) in enumerate(self.elements[:-1]):
            key = _FIELD_ALIASES.get(label.rstrip(":"))
            if key is None or tag not in {"dt", "th", "h3", "h4"}:
                continue
            value_tag, value = self.elements[index + 1]
            if value_tag in {"dd", "td", "p", "li"} and value:
                result.setdefault(key, value)
        title = next(
            (text for tag, text in self.elements if tag in {"h1", "h2"}),
            None,
        )
        if title:
            result.setdefault("title", title)
        return result


def _page(pages: Mapping[str, bytes | str], url: str) -> str:
    try:
        payload = pages[url]
    except KeyError:
        raise DiscoveryDriftError("discovery page is missing") from None
    if isinstance(payload, bytes):
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError:
            raise DiscoveryDriftError(
                "discovery page is not valid UTF-8"
            ) from None
    if not isinstance(payload, str):
        raise DiscoveryDriftError("discovery page has an invalid payload")
    return payload


def _best_link(
    links: list[tuple[str, str]],
    *,
    base_url: str,
    pages: Mapping[str, bytes | str],
    keywords: tuple[str, ...],
) -> tuple[str, str]:
    base_host = urllib.parse.urlsplit(base_url).hostname
    candidates: list[tuple[int, str, str]] = []
    for text, href in links:
        target = urllib.parse.urljoin(base_url, href)
        if (
            target not in pages
            or urllib.parse.urlsplit(target).hostname != base_host
        ):
            continue
        score = max(
            (len(keyword) for keyword in keywords if keyword in text),
            default=0,
        )
        if score:
            candidates.append((score, text, target))
    if not candidates:
        raise DiscoveryDriftError("policy navigation was not discovered")
    _, text, target = sorted(
        candidates,
        key=lambda item: (-item[0], item[1], item[2]),
    )[0]
    return text, target


def _has_link(
    links: list[tuple[str, str]],
    base_url: str,
    target: str,
) -> bool:
    return any(
        urllib.parse.urljoin(base_url, href) == target
        for _, href in links
    )


def _candidate(
    detail_url: str,
    link_title: str,
    pages: Mapping[str, bytes | str],
) -> DiscoveredPolicyCandidate:
    parser = _SemanticHtmlParser(_page(pages, detail_url))
    fields = parser.fields()
    title = fields.get("title") or _clean(link_title)
    if not title:
        raise DiscoveryDriftError("policy detail title is empty")
    return DiscoveredPolicyCandidate(
        external_id=_external_id(detail_url),
        title=title,
        detail_url=detail_url,
        fields=fields,
    )


def _external_id(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(parsed.query))
    for key in _EXTERNAL_ID_KEYS:
        value = query.get(key)
        if value:
            return value
    value = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    if value and "." not in value:
        return value
    raise DiscoveryDriftError("policy detail external ID was not discovered")


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())
