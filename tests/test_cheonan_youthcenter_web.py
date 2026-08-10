from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from collectors import default_registry
from collectors.base import CollectionOptions
from collectors.cheonan_youthcenter import (
    APPROVED_EXTERNAL_ID,
    BOARD_URL,
    CANONICAL_DETAIL_URL,
    DETAIL_QUERY,
    LIST_QUERY,
    SOURCE_ID,
    CheonanYouthCenterCollector,
    CheonanYouthCenterExtractor,
    web_http_config_from_environment,
)
from collectors.errors import (
    CollectorConfigurationError,
    ResponseParseError,
)
from collectors.extracted import ExtractionError
from collectors.http import TransportResponse
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.storage import RawDocumentStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    ROOT / "data/fixtures/html/cheonan-youthcenter-web"
)
COLLECTED_AT = datetime(2026, 8, 10, 3, 0, tzinfo=timezone.utc)


def fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def response(body: bytes) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        body=body,
    )


class StubHttpClient:
    def __init__(self, outcomes: list[TransportResponse | BaseException]):
        self._outcomes = iter(outcomes)
        self.calls: list[dict[str, Any]] = []

    def get(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(kwargs)
        outcome = next(self._outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def raw_document(
    *,
    number: int,
    role: RawDocumentRole,
    payload: bytes,
    external_id: str | None = None,
    parent_document_id: str | None = None,
    collected_at: datetime = COLLECTED_AT,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        document_id=f"{number:032x}",
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=BOARD_URL,
        collected_at=collected_at,
        content_type="text/html; charset=utf-8",
        raw_format=RawFormat.HTML,
        raw_payload=payload,
        http_status=200,
        collector_version="test/1.0",
    )


def extraction_documents(
    detail_name: str = "detail_normal.html",
    *,
    list_payload: bytes | None = None,
) -> tuple[RawPolicyDocument, ...]:
    parent = raw_document(
        number=1,
        role=RawDocumentRole.LIST_RESPONSE,
        payload=fixture("list_normal.html"),
    )
    item = raw_document(
        number=2,
        role=RawDocumentRole.LIST_ITEM,
        payload=list_payload or fixture("list_normal.html"),
        external_id=APPROVED_EXTERNAL_ID,
        parent_document_id=parent.document_id,
    )
    detail = raw_document(
        number=3,
        role=RawDocumentRole.DETAIL_RESPONSE,
        payload=fixture(detail_name),
        external_id=APPROVED_EXTERNAL_ID,
        collected_at=COLLECTED_AT + timedelta(minutes=1),
    )
    return parent, item, detail


class CheonanCollectorTests(unittest.TestCase):
    def test_registry_includes_approved_web_source(self) -> None:
        self.assertIn(SOURCE_ID, default_registry.source_ids())

    def test_web_http_config_enforces_two_second_floor(self) -> None:
        minimum = web_http_config_from_environment(
            environ={"HTTP_REQUEST_DELAY_SECONDS": "0.25"}
        )
        larger = web_http_config_from_environment(
            environ={"HTTP_REQUEST_DELAY_SECONDS": "3.5"}
        )

        self.assertEqual(2.0, minimum.request_interval_seconds)
        self.assertEqual(3.5, larger.request_interval_seconds)

    def test_collects_only_approved_list_and_detail_as_html_raw(self) -> None:
        client = StubHttpClient(
            [
                response(fixture("list_normal.html")),
                response(fixture("detail_normal.html")),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            collector = CheonanYouthCenterCollector(
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            )

            result = collector.collect()
            documents = tuple(store.load(path) for path in result.stored_paths)

        self.assertEqual(2, result.request_count)
        self.assertEqual(1, result.item_count)
        self.assertEqual(1, result.detail_count)
        self.assertEqual((APPROVED_EXTERNAL_ID,), result.external_ids)
        self.assertEqual(3, result.raw_document_count)
        self.assertEqual(
            [LIST_QUERY, DETAIL_QUERY],
            [call["query"] for call in client.calls],
        )
        self.assertTrue(all(call["url"] == BOARD_URL for call in client.calls))
        self.assertTrue(
            all(document.source_type is SourceType.WEB for document in documents)
        )
        self.assertTrue(
            all(document.raw_format is RawFormat.HTML for document in documents)
        )
        self.assertTrue(
            all(document.source_url == BOARD_URL for document in documents)
        )
        self.assertTrue(
            all("?" not in document.source_url for document in documents)
        )

    def test_detail_limit_zero_never_calls_detail(self) -> None:
        client = StubHttpClient([response(fixture("list_normal.html"))])
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = CheonanYouthCenterCollector(
                http_client=client,
                store=RawDocumentStore(temporary_directory),
                now=lambda: COLLECTED_AT,
            ).collect(CollectionOptions(detail_limit=0))

        self.assertEqual(1, result.request_count)
        self.assertEqual(0, result.detail_count)
        self.assertEqual(1, len(client.calls))

    def test_rejects_page_expansion_before_request(self) -> None:
        client = StubHttpClient([])
        with self.assertRaises(CollectorConfigurationError):
            CheonanYouthCenterCollector(http_client=client).collect(
                CollectionOptions(page=2)
            )
        self.assertEqual([], client.calls)

    def test_selector_drift_is_safe_and_stores_no_raw(self) -> None:
        client = StubHttpClient(
            [
                response(fixture("list_normal.html")),
                response(fixture("detail_selector_drift.html")),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ResponseParseError) as raised:
                CheonanYouthCenterCollector(
                    http_client=client,
                    store=RawDocumentStore(temporary_directory),
                    now=lambda: COLLECTED_AT,
                ).collect()
            self.assertEqual(
                [],
                list(Path(temporary_directory).rglob("*.json")),
            )

        self.assertNotIn("구조가 바뀐", str(raised.exception))
        self.assertNotIn("wr_id", str(raised.exception))


class CheonanExtractorTests(unittest.TestCase):
    def test_extracts_source_backed_sections_and_institutional_contact(self) -> None:
        policy = CheonanYouthCenterExtractor().extract(
            extraction_documents()
        )[0]

        self.assertEqual(APPROVED_EXTERNAL_ID, policy.external_id)
        self.assertEqual(CANONICAL_DETAIL_URL, policy.source_url)
        self.assertEqual(
            "2026년 합성 청년 주거안전 지원사업 신청자 모집",
            policy.title,
        )
        self.assertEqual("천안시에 거주하는 1인가구 청년", policy.eligibility_text)
        self.assertEqual("주거 안전장비를 1년간 지원", policy.support_content)
        self.assertEqual(
            "공개 안내를 확인한 뒤 신청서 제출",
            policy.application_method,
        )
        detail_fields = policy.extra["source_fields"]["detail_response"]
        self.assertEqual("26-07-24 15:22", detail_fields["published_text"])
        self.assertNotIn("contact", detail_fields["sections"])
        self.assertEqual(
            {
                "phone_numbers": ["041-000-0000"],
                "channels": ["카카오채널"],
            },
            detail_fields["institutional_contact"],
        )
        self.assertEqual(3, len(policy.provenance))

    def test_personal_mobile_number_is_not_extracted(self) -> None:
        detail = fixture("detail_normal.html").replace(
            b"041-000-0000",
            b"010-1234-5678",
        )
        documents = list(extraction_documents())
        documents[2] = raw_document(
            number=3,
            role=RawDocumentRole.DETAIL_RESPONSE,
            payload=detail,
            external_id=APPROVED_EXTERNAL_ID,
            collected_at=COLLECTED_AT + timedelta(minutes=1),
        )

        policy = CheonanYouthCenterExtractor().extract(documents)[0]
        contact = policy.extra["source_fields"]["detail_response"][
            "institutional_contact"
        ]
        self.assertEqual([], contact["phone_numbers"])

    def test_missing_optional_fields_remain_null(self) -> None:
        policy = CheonanYouthCenterExtractor().extract(
            extraction_documents("detail_missing_optional.html")
        )[0]

        detail_fields = policy.extra["source_fields"]["detail_response"]
        self.assertIsNone(detail_fields["published_text"])
        self.assertIsNone(policy.application_period_text)
        self.assertIsNone(policy.support_content)
        self.assertEqual("천안시 청년", policy.eligibility_text)

    def test_detail_selector_drift_is_not_treated_as_empty_fields(self) -> None:
        with self.assertRaisesRegex(ExtractionError, "selector drift"):
            CheonanYouthCenterExtractor().extract(
                extraction_documents("detail_selector_drift.html")
            )

    def test_approved_link_with_extra_query_is_rejected(self) -> None:
        changed = fixture("list_normal.html").replace(
            b"wr_id=674",
            b"wr_id=674&amp;page=1",
        )

        with self.assertRaisesRegex(ExtractionError, "URL drift"):
            CheonanYouthCenterExtractor().extract(
                extraction_documents(list_payload=changed)
            )


if __name__ == "__main__":
    unittest.main()
