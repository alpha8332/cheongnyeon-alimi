from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collectors import default_registry
from collectors.base import CollectionOptions
from collectors.http import TransportResponse
from collectors.incheon_youth_programs import (
    SOURCE_ID,
    SOURCE_PAGE_URL,
    IncheonYouthProgramsCollector,
    IncheonYouthProgramsExtractor,
)
from collectors.normalizer import Normalizer
from collectors.raw import RawDocumentRole, RawFormat
from collectors.storage import RawDocumentStore


COLLECTED_AT = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
CSV_TEXT = """연번,프로그램명,주요내용,모집기간,강의장소,문의처
1,2026년 인천 청년공간 이용 만족도 조사,청년 공간 만족도 조사,2026-04-01~2026-12-31,홈페이지,032-000-0000
2,"[취준클래스] 개발자 취업·창업전략",개발자 취업정보 제공,2026-06-10~2026-09-23,온라인+오프라인,032-000-0001
"""


class StubHttpClient:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.calls: list[dict[str, Any]] = []

    def get(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(kwargs)
        return TransportResponse(
            status=200,
            headers={"Content-Type": "application/octet-stream"},
            body=self.body,
        )


def test_keyless_csv_collection_preserves_raw_and_stable_items() -> None:
    http = StubHttpClient(CSV_TEXT.encode("cp949"))
    with tempfile.TemporaryDirectory() as temporary_directory:
        store = RawDocumentStore(temporary_directory)
        result = IncheonYouthProgramsCollector(
            http_client=http,
            store=store,
            now=lambda: COLLECTED_AT,
        ).collect(CollectionOptions(page=1, limit=500, detail_limit=0))
        documents = [store.load(path) for path in result.stored_paths]

    assert result.total_count == 2
    assert result.external_ids == ("20260713-001", "20260713-002")
    assert result.request_count == 1
    assert result.list_response_document_id == documents[0].document_id
    assert documents[0].document_role is RawDocumentRole.LIST_RESPONSE
    assert documents[0].raw_format is RawFormat.CSV
    assert documents[0].raw_bytes == CSV_TEXT.encode("cp949")
    assert all(
        document.source_url == SOURCE_PAGE_URL for document in documents
    )
    assert http.calls[0]["query"].keys() == {
        "atchFileId",
        "fileDetailSn",
        "dataNm",
    }


def test_extractor_normalizes_regional_scope_dates_and_categories() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        store = RawDocumentStore(temporary_directory)
        result = IncheonYouthProgramsCollector(
            http_client=StubHttpClient(CSV_TEXT.encode("cp949")),
            store=store,
            now=lambda: COLLECTED_AT,
        ).collect(CollectionOptions(limit=500, detail_limit=0))
        documents = [store.load(path) for path in result.stored_paths]

    extracted = IncheonYouthProgramsExtractor().extract(documents)
    normalized = [Normalizer().normalize(policy) for policy in extracted]

    assert len(extracted) == 2
    assert all(result.program is not None for result in normalized)
    survey = normalized[0].program
    employment = normalized[1].program
    assert survey is not None and employment is not None
    assert survey.application_start.isoformat() == "2026-04-01"
    assert survey.application_end.isoformat() == "2026-12-31"
    assert survey.coverage_scope.value == "regional"
    assert survey.regions == ("인천광역시",)
    assert survey.region_rules[0].resolution_status.value == "matched"
    assert [value.value for value in employment.categories] == [
        "employment",
        "startup",
        "education",
    ]
    assert employment.application_status.value == "open"
    assert employment.source_url == SOURCE_PAGE_URL


def test_public_incheon_collector_is_registered() -> None:
    assert SOURCE_ID in default_registry.source_ids()
