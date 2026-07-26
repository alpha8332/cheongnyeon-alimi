from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collectors.base import CollectionOptions
from collectors.bokjiro import BokjiroCollector
from collectors.config import (
    http_config_from_environment,
    required_secret,
)
from collectors.errors import (
    AuthenticationError,
    ClientResponseError,
    CollectorConfigurationError,
    EmptyResponseError,
    RateLimitError,
    ResponseParseError,
)
from collectors.http import TransportResponse
from collectors.raw import RawDocumentRole
from collectors.storage import RawDocumentStore
from collectors.youthcenter import YouthCenterCollector


COLLECTED_AT = datetime(2026, 7, 26, 16, 30, tzinfo=timezone.utc)


class StubHttpClient:
    def __init__(
        self,
        outcomes: list[TransportResponse | BaseException],
    ) -> None:
        self._outcomes = iter(outcomes)
        self.calls: list[dict[str, Any]] = []

    def get(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(kwargs)
        outcome = next(self._outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def response(
    body: bytes,
    *,
    content_type: str,
) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": content_type},
        body=body,
    )


def youth_response(count: int, *, result_code: int = 200) -> bytes:
    return json.dumps(
        {
            "resultCode": result_code,
            "resultMessage": "test message",
            "result": {
                "pagging": {
                    "pageNum": 1,
                    "pageSize": count,
                    "totCount": count,
                },
                "youthPolicyList": [
                    {
                        "plcyNo": f"R{index:09d}",
                        "plcyNm": f"Policy {index}",
                        "optional": "",
                    }
                    for index in range(1, count + 1)
                ],
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")


def bokjiro_list_response(count: int, *, result_code: str = "0") -> bytes:
    items = "".join(
        (
            "<servList>"
            f"<servId>WLF{index:06d}</servId>"
            f"<servNm>Service {index}</servNm>"
            "</servList>"
        )
        for index in range(1, count + 1)
    )
    return (
        "<wantedList>"
        f"<resultCode>{result_code}</resultCode>"
        "<resultMessage>test message</resultMessage>"
        f"<numOfRows>{count}</numOfRows>"
        f"<totalCount>{count}</totalCount>"
        f"{items}"
        "</wantedList>"
    ).encode("utf-8")


def bokjiro_detail_response(service_id: str) -> bytes:
    return (
        "<wantedDtl>"
        "<resultCode>0</resultCode>"
        "<resultMessage>test message</resultMessage>"
        f"<servId>{service_id}</servId>"
        "<servNm>Detail service</servNm>"
        "</wantedDtl>"
    ).encode("utf-8")


class ConfigurationTests(unittest.TestCase):
    def test_required_secret_never_includes_value_in_error(self) -> None:
        with self.assertRaises(CollectorConfigurationError) as raised:
            required_secret(
                "YOUTHCENTER_API_KEY",
                environ={"YOUTHCENTER_API_KEY": " secret-value "},
            )

        self.assertNotIn("secret-value", str(raised.exception))
        self.assertIn("YOUTHCENTER_API_KEY", str(raised.exception))

    def test_http_environment_values_are_parsed(self) -> None:
        config = http_config_from_environment(
            environ={
                "HTTP_TIMEOUT_SECONDS": "4.5",
                "HTTP_MAX_RETRIES": "2",
                "HTTP_REQUEST_DELAY_SECONDS": "0.25",
            }
        )

        self.assertEqual(4.5, config.timeout_seconds)
        self.assertEqual(2, config.max_retries)
        self.assertEqual(0.25, config.request_interval_seconds)


class YouthCenterCollectorTests(unittest.TestCase):
    def test_collects_requested_page_and_limit_as_raw_documents(self) -> None:
        client = StubHttpClient(
            [response(youth_response(12), content_type="application/json")]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            collector = YouthCenterCollector(
                api_key="test-youth-secret",
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            )

            result = collector.collect(
                CollectionOptions(page=2, limit=10, detail_limit=0)
            )
            documents = [store.load(path) for path in result.stored_paths]

        self.assertEqual(1, result.request_count)
        self.assertEqual(10, result.item_count)
        self.assertEqual(11, result.raw_document_count)
        self.assertEqual(2, client.calls[0]["query"]["pageNum"])
        self.assertEqual(10, client.calls[0]["query"]["pageSize"])
        self.assertEqual(
            1,
            sum(
                document.document_role is RawDocumentRole.LIST_RESPONSE
                for document in documents
            ),
        )
        items = [
            document
            for document in documents
            if document.document_role is RawDocumentRole.LIST_ITEM
        ]
        self.assertEqual(10, len(items))
        self.assertTrue(
            all(
                item.parent_document_id == documents[0].document_id
                for item in items
            )
        )
        self.assertTrue(
            all("?" not in document.source_url for document in documents)
        )

    def test_empty_policy_list_is_classified(self) -> None:
        client = StubHttpClient(
            [response(youth_response(0), content_type="application/json")]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            collector = YouthCenterCollector(
                api_key="test-youth-secret",
                http_client=client,
                store=RawDocumentStore(temporary_directory),
            )
            with self.assertRaises(EmptyResponseError):
                collector.collect(CollectionOptions(limit=10))

        self.assertEqual([], list(Path(temporary_directory).rglob("*.json")))

    def test_application_error_codes_are_classified(self) -> None:
        cases = (
            (401, AuthenticationError),
            (429, RateLimitError),
            (500, ClientResponseError),
        )
        for result_code, expected_error in cases:
            with self.subTest(result_code=result_code):
                client = StubHttpClient(
                    [
                        response(
                            youth_response(0, result_code=result_code),
                            content_type="application/json",
                        )
                    ]
                )
                collector = YouthCenterCollector(
                    api_key="test-youth-secret",
                    http_client=client,
                )
                with self.assertRaises(expected_error):
                    collector.collect()

    def test_invalid_json_and_credential_echo_are_rejected(self) -> None:
        cases = (
            b"not-json",
            b'{"resultCode":200,"echo":"test-youth-secret"}',
        )
        for body in cases:
            with self.subTest(body_kind=body[:4]):
                collector = YouthCenterCollector(
                    api_key="test-youth-secret",
                    http_client=StubHttpClient(
                        [response(body, content_type="application/json")]
                    ),
                )
                with self.assertRaises(ResponseParseError) as raised:
                    collector.collect()
                self.assertNotIn(
                    "test-youth-secret",
                    str(raised.exception),
                )


class BokjiroCollectorTests(unittest.TestCase):
    def test_collects_list_items_and_limited_details(self) -> None:
        outcomes = [
            response(
                bokjiro_list_response(12),
                content_type="application/xml;charset=UTF-8",
            ),
            *[
                response(
                    bokjiro_detail_response(f"WLF{index:06d}"),
                    content_type="application/xml",
                )
                for index in range(1, 4)
            ],
        ]
        client = StubHttpClient(outcomes)
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            collector = BokjiroCollector(
                api_key="test-bokjiro-secret",
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            )

            result = collector.collect(
                CollectionOptions(page=2, limit=10, detail_limit=3)
            )
            documents = [store.load(path) for path in result.stored_paths]

        self.assertEqual(4, result.request_count)
        self.assertEqual(10, result.item_count)
        self.assertEqual(3, result.detail_count)
        self.assertEqual(14, result.raw_document_count)
        self.assertEqual(2, client.calls[0]["query"]["pageNo"])
        self.assertEqual(10, client.calls[0]["query"]["numOfRows"])
        self.assertEqual(
            ["WLF000001", "WLF000002", "WLF000003"],
            [
                call["query"]["servId"]
                for call in client.calls[1:]
            ],
        )
        self.assertEqual(
            3,
            sum(
                document.document_role
                is RawDocumentRole.DETAIL_RESPONSE
                for document in documents
            ),
        )

    def test_encoded_service_key_is_normalized_before_query_encoding(
        self,
    ) -> None:
        client = StubHttpClient(
            [
                response(
                    bokjiro_list_response(1),
                    content_type="application/xml",
                )
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            collector = BokjiroCollector(
                api_key="test%2Bkey%3D",
                http_client=client,
                store=RawDocumentStore(temporary_directory),
            )
            collector.collect(CollectionOptions(limit=1, detail_limit=0))

        self.assertEqual(
            "test+key=",
            client.calls[0]["query"]["serviceKey"],
        )

    def test_xml_application_error_codes_are_classified(self) -> None:
        cases = (
            ("30", AuthenticationError),
            ("22", RateLimitError),
            ("10", ClientResponseError),
        )
        for result_code, expected_error in cases:
            with self.subTest(result_code=result_code):
                client = StubHttpClient(
                    [
                        response(
                            bokjiro_list_response(
                                0,
                                result_code=result_code,
                            ),
                            content_type="application/xml",
                        )
                    ]
                )
                collector = BokjiroCollector(
                    api_key="test-bokjiro-secret",
                    http_client=client,
                )
                with self.assertRaises(expected_error):
                    collector.collect()

    def test_empty_list_and_invalid_xml_are_classified(self) -> None:
        cases = (
            (
                bokjiro_list_response(0),
                EmptyResponseError,
            ),
            (b"<not-closed>", ResponseParseError),
        )
        for body, expected_error in cases:
            with self.subTest(expected_error=expected_error.__name__):
                collector = BokjiroCollector(
                    api_key="test-bokjiro-secret",
                    http_client=StubHttpClient(
                        [response(body, content_type="application/xml")]
                    ),
                )
                with self.assertRaises(expected_error):
                    collector.collect()

    def test_mismatched_detail_id_is_rejected(self) -> None:
        client = StubHttpClient(
            [
                response(
                    bokjiro_list_response(1),
                    content_type="application/xml",
                ),
                response(
                    bokjiro_detail_response("OTHER-ID"),
                    content_type="application/xml",
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            collector = BokjiroCollector(
                api_key="test-bokjiro-secret",
                http_client=client,
                store=RawDocumentStore(temporary_directory),
            )
            with self.assertRaises(ResponseParseError):
                collector.collect(
                    CollectionOptions(limit=1, detail_limit=1)
                )


if __name__ == "__main__":
    unittest.main()
