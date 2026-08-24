"""Keyless collector for Incheon's licensed youth-program CSV."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable, Iterable
from copy import deepcopy
from datetime import datetime

from collectors.base import CollectionOptions, CollectionResult
from collectors.config import http_config_from_environment
from collectors.errors import EmptyResponseError
from collectors.extracted import (
    ExtractedCoverageScope,
    ExtractedPolicy,
    ExtractedRegionRelation,
    ExtractionError,
    SourceProvenance,
    SourceRegionEvidence,
)
from collectors.http import HttpClient, TransportResponse
from collectors.profile import SourceFieldProfile, build_field_profile
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
    utc_now,
)
from collectors.source_common import response_content_type, safe_parse_error
from collectors.storage import RawDocumentStore


SOURCE_ID = "data-go-kr-incheon-youth-programs"
SOURCE_NAME = "인천광역시 청년공간 유유기지 프로그램"
SOURCE_PAGE_URL = "https://www.data.go.kr/data/15038491/fileData.do"
DOWNLOAD_URL = "https://www.data.go.kr/cmm/cmm/fileDownload.do"
DATASET_DATE = "20260713"
ATTACHMENT_ID = "FILE_000000003674990"
DOWNLOAD_NAME = (
    "인천광역시_청년공간 유유기지 인천 프로그램 "
    f"정보제공_{DATASET_DATE}"
)
COLLECTOR_VERSION = "data-go-kr-incheon-youth-programs/1.0"
REGION_NAME = "인천광역시"
ORGANIZATION = "인천광역시 청년지원센터 유유기지 인천"
EXPECTED_HEADERS = (
    "연번",
    "프로그램명",
    "주요내용",
    "모집기간",
    "강의장소",
    "문의처",
)


class IncheonYouthProgramsCollector:
    source_id = SOURCE_ID

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._http_client = http_client or HttpClient()
        self._store = store or RawDocumentStore()
        self._now = now

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        response = self._http_client.get(
            source_id=self.source_id,
            url=DOWNLOAD_URL,
            query={
                "atchFileId": ATTACHMENT_ID,
                "fileDetailSn": "1",
                "dataNm": DOWNLOAD_NAME,
            },
        )
        rows = self._parse_rows(response)
        offset = (selected.page - 1) * selected.limit
        page_rows = rows[offset : offset + selected.limit]
        if not page_rows:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=SOURCE_PAGE_URL,
                reason="source page contains no rows for the requested page",
                status=response.status,
            )

        prepared_items: list[tuple[str, bytes]] = []
        for row in page_rows:
            sequence = row["연번"]
            if not sequence.isdigit():
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=SOURCE_PAGE_URL,
                    response=response,
                    reason="program row has an invalid sequence number",
                )
            external_id = f"{DATASET_DATE}-{int(sequence):03d}"
            prepared_items.append(
                (
                    external_id,
                    json.dumps(
                        row,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8"),
                )
            )

        collected_at = self._now()
        list_document = RawPolicyDocument.from_bytes(
            source_id=self.source_id,
            source_type=SourceType.WEB,
            document_role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=SOURCE_PAGE_URL,
            collected_at=collected_at,
            content_type=response_content_type(
                response,
                default="text/csv; charset=cp949",
            ),
            raw_format=RawFormat.CSV,
            raw_payload=response.body,
            http_status=response.status,
            collector_version=COLLECTOR_VERSION,
        )
        stored_paths = [self._store.save(list_document)]
        for external_id, payload in prepared_items:
            item_document = RawPolicyDocument.from_bytes(
                source_id=self.source_id,
                source_type=SourceType.WEB,
                document_role=RawDocumentRole.LIST_ITEM,
                external_id=external_id,
                parent_document_id=list_document.document_id,
                source_url=SOURCE_PAGE_URL,
                collected_at=collected_at,
                content_type="application/json",
                raw_format=RawFormat.JSON,
                raw_payload=payload,
                http_status=response.status,
                collector_version=COLLECTOR_VERSION,
            )
            stored_paths.append(self._store.save(item_document))

        return CollectionResult(
            source_id=self.source_id,
            request_count=1,
            item_count=len(page_rows),
            detail_count=0,
            stored_paths=tuple(stored_paths),
            page=selected.page,
            page_size=selected.limit,
            total_count=len(rows),
            external_ids=tuple(item[0] for item in prepared_items),
            list_response_document_id=list_document.document_id,
        )

    def _parse_rows(
        self,
        response: TransportResponse,
    ) -> list[dict[str, str]]:
        try:
            text = response.body.decode("cp949")
            reader = csv.DictReader(io.StringIO(text))
            if tuple(reader.fieldnames or ()) != EXPECTED_HEADERS:
                raise ValueError("unexpected CSV headers")
            rows = [
                {
                    key: (value or "").strip()
                    for key, value in row.items()
                }
                for row in reader
            ]
        except (UnicodeDecodeError, csv.Error, ValueError):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_PAGE_URL,
                response=response,
                reason="response is not the approved Incheon CSV contract",
            ) from None
        if not rows:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=SOURCE_PAGE_URL,
                reason="source returned an empty program list",
                status=response.status,
            )
        if any(not row["프로그램명"] or not row["모집기간"] for row in rows):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_PAGE_URL,
                response=response,
                reason="program row is missing a required public field",
            )
        return rows


class IncheonYouthProgramsExtractor:
    source_id = SOURCE_ID

    def extract(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[ExtractedPolicy, ...]:
        selected = [
            document for document in documents
            if document.source_id == self.source_id
        ]
        if not selected:
            raise ExtractionError(f"no Raw documents found for {self.source_id}")
        list_responses = {
            document.document_id: document
            for document in selected
            if document.document_role is RawDocumentRole.LIST_RESPONSE
            and document.raw_format is RawFormat.CSV
        }
        items = sorted(
            (
                document for document in selected
                if document.document_role is RawDocumentRole.LIST_ITEM
                and document.raw_format is RawFormat.JSON
            ),
            key=lambda document: document.external_id or "",
        )
        if not list_responses or not items:
            raise ExtractionError("Incheon CSV Raw batch is incomplete")

        policies: list[ExtractedPolicy] = []
        seen_external_ids: set[str] = set()
        for item in items:
            if item.external_id is None or item.external_id in seen_external_ids:
                raise ExtractionError("Incheon CSV item identity is invalid")
            seen_external_ids.add(item.external_id)
            parent = list_responses.get(item.parent_document_id or "")
            if parent is None:
                raise ExtractionError("Incheon CSV item has no list response")
            try:
                fields = json.loads(item.raw_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ExtractionError("Incheon CSV item is not valid JSON") from None
            if not isinstance(fields, dict) or set(fields) != set(EXPECTED_HEADERS):
                raise ExtractionError("Incheon CSV item fields do not match")
            provenance = (
                SourceProvenance.from_raw(parent),
                SourceProvenance.from_raw(item),
            )
            summary = _present_text(fields.get("주요내용"))
            title = _present_text(fields.get("프로그램명"))
            policies.append(
                ExtractedPolicy(
                    source_id=self.source_id,
                    source_name=SOURCE_NAME,
                    external_id=item.external_id,
                    title=title,
                    organization=ORGANIZATION,
                    summary=summary,
                    category_text=_category_text(title, summary),
                    keywords=_keywords(title, summary),
                    life_stages=("청년",),
                    target_groups=("청년",),
                    application_period_text=_present_text(fields.get("모집기간")),
                    region_text=REGION_NAME,
                    coverage_scope_hint=ExtractedCoverageScope.REGIONAL,
                    region_evidence=(
                        SourceRegionEvidence(
                            relation=ExtractedRegionRelation.INCLUDE,
                            external_scheme=None,
                            source_code=None,
                            source_text=REGION_NAME,
                        ),
                    ),
                    age_text=None,
                    eligibility_text=None,
                    support_content=summary,
                    application_method=None,
                    source_url=SOURCE_PAGE_URL,
                    collected_at=max(value.collected_at for value in provenance),
                    provenance=provenance,
                    extra={
                        "source_fields": {
                            "list_item": deepcopy(fields),
                            "detail_response": None,
                        }
                    },
                )
            )
        return tuple(policies)

    def profiles(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[SourceFieldProfile, ...]:
        records = []
        for document in documents:
            if (
                document.source_id == self.source_id
                and document.document_role is RawDocumentRole.LIST_ITEM
                and document.raw_format is RawFormat.JSON
            ):
                value = json.loads(document.raw_bytes)
                if isinstance(value, dict):
                    records.append(value)
        if not records:
            raise ExtractionError(f"no Raw documents found for {self.source_id}")
        return (
            build_field_profile(
                source_id=self.source_id,
                document_role=RawDocumentRole.LIST_ITEM,
                records=records,
            ),
        )


def _present_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    selected = " ".join(value.split())
    return selected or None


def _category_text(title: str | None, summary: str | None) -> str:
    text = " ".join(value for value in (title, summary) if value)
    selected: list[str] = []
    if any(
        token in text
        for token in ("취업", "취준", "진로", "커리어", "취·창업", "취, 창업")
    ):
        selected.append("취업")
    if "창업" in text:
        selected.append("창업")
    if any(token in text for token in ("강의", "클래스", "교육")):
        selected.append("교육")
    return ",".join(selected) if selected else "기타"


def _keywords(title: str | None, summary: str | None) -> tuple[str, ...]:
    text = " ".join(value for value in (title, summary) if value)
    selected = ["청년", "인천광역시"]
    for token in ("취업", "창업", "진로", "개발자", "커리어", "컨설팅"):
        if token in text and token not in selected:
            selected.append(token)
    return tuple(selected)


def create_incheon_youth_programs_collector() -> IncheonYouthProgramsCollector:
    return IncheonYouthProgramsCollector(
        http_client=HttpClient(config=http_config_from_environment()),
    )
