from __future__ import annotations

import unittest
import urllib.request
from collections.abc import Iterable

from collectors.errors import (
    AuthenticationError,
    ClientResponseError,
    RateLimitError,
    RequestTimeoutError,
    ResponseParseError,
    ServerResponseError,
    TransportError,
    UnexpectedResponseError,
)
from collectors.http import (
    HttpClient,
    HttpClientConfig,
    TransportResponse,
    redact_url,
)


def response(status: int, body: bytes = b"") -> TransportResponse:
    return TransportResponse(status=status, headers={}, body=body)


class StubTransport:
    def __init__(
        self,
        outcomes: Iterable[TransportResponse | BaseException],
    ) -> None:
        self._outcomes = iter(outcomes)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float] = []

    def send(
        self,
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> TransportResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        outcome = next(self._outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def client_for(
    transport: StubTransport,
    *,
    max_retries: int = 3,
    backoff_seconds: float = 0,
    request_interval_seconds: float = 0,
    clock: FakeClock | None = None,
) -> HttpClient:
    clock = clock or FakeClock()
    return HttpClient(
        config=HttpClientConfig(
            timeout_seconds=2.5,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            request_interval_seconds=request_interval_seconds,
        ),
        transport=transport,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )


class HttpClientTests(unittest.TestCase):
    def test_json_response_and_query_are_sent(self) -> None:
        transport = StubTransport([response(200, b'{"items": [1]}')])
        client = client_for(transport)

        payload = client.get_json(
            source_id="youthcenter-api",
            url="https://example.test/policies",
            query={"apiKeyNm": "secret-value", "pageNum": 1},
        )

        self.assertEqual({"items": [1]}, payload)
        self.assertEqual(1, len(transport.requests))
        self.assertIn("apiKeyNm=secret-value", transport.requests[0].full_url)
        self.assertEqual(
            "cheongnyeon-alimi-collector",
            transport.requests[0].get_header("User-agent"),
        )
        self.assertEqual([2.5], transport.timeouts)

    def test_xml_response_is_parsed(self) -> None:
        transport = StubTransport(
            [response(200, b"<response><totalCount>1</totalCount></response>")]
        )
        client = client_for(transport)

        root = client.get_xml(
            source_id="bokjiro-central-welfare-api",
            url="https://example.test/welfare",
        )

        self.assertEqual("response", root.tag)
        self.assertEqual("1", root.findtext("totalCount"))

    def test_form_post_encodes_body_and_preserves_headers(self) -> None:
        transport = StubTransport([response(200, b'{"ok": true}')])
        client = client_for(transport)

        result = client.post_form(
            source_id="regional-test-source",
            url="https://example.test/policies.json",
            form={"pageIndex": 1, "policyType": ["job", "housing"]},
            headers={"X-CSRF-TOKEN": "token-value"},
        )

        request = transport.requests[0]
        self.assertEqual(200, result.status)
        self.assertEqual("POST", request.get_method())
        self.assertEqual(
            b"pageIndex=1&policyType=job&policyType=housing",
            request.data,
        )
        self.assertEqual("token-value", request.get_header("X-csrf-token"))
        self.assertEqual(
            "application/x-www-form-urlencoded; charset=utf-8",
            request.get_header("Content-type"),
        )

    def test_timeout_is_retried_and_classified_without_original_message(
        self,
    ) -> None:
        transport = StubTransport(
            [
                TimeoutError("secret-value"),
                TimeoutError("secret-value"),
            ]
        )
        client = client_for(transport, max_retries=1)

        with self.assertRaises(RequestTimeoutError) as raised:
            client.get(
                source_id="youthcenter-api",
                url="https://example.test/policies",
                query={"apiKeyNm": "secret-value"},
            )

        self.assertEqual(2, len(transport.requests))
        self.assertNotIn("secret-value", str(raised.exception))
        self.assertIn("apiKeyNm=<redacted>", str(raised.exception))

    def test_unexpected_transport_error_is_safely_wrapped(self) -> None:
        transport = StubTransport([RuntimeError("serviceKey=secret-value")])
        client = client_for(transport)

        with self.assertRaises(TransportError) as raised:
            client.get(
                source_id="bokjiro-central-welfare-api",
                url="https://example.test/welfare",
                query={"serviceKey": "secret-value"},
            )

        self.assertEqual(1, len(transport.requests))
        self.assertNotIn("secret-value", str(raised.exception))
        self.assertIn("serviceKey=<redacted>", str(raised.exception))

    def test_429_is_not_retried(self) -> None:
        transport = StubTransport([response(429)])
        client = client_for(transport, max_retries=3)

        with self.assertRaises(RateLimitError) as raised:
            client.get(
                source_id="youthcenter-api",
                url="https://example.test/policies",
            )

        self.assertEqual(429, raised.exception.status)
        self.assertEqual(1, len(transport.requests))

    def test_authentication_status_is_distinct_from_other_4xx(self) -> None:
        for status in (401, 403):
            with self.subTest(status=status):
                client = client_for(StubTransport([response(status)]))
                with self.assertRaises(AuthenticationError):
                    client.get(
                        source_id="youthcenter-api",
                        url="https://example.test/policies",
                    )

        client = client_for(StubTransport([response(404)]))
        with self.assertRaises(ClientResponseError):
            client.get(
                source_id="youthcenter-api",
                url="https://example.test/policies",
            )

    def test_5xx_is_retried_until_success(self) -> None:
        transport = StubTransport(
            [response(500), response(503), response(200, b"ok")]
        )
        client = client_for(transport, max_retries=2)

        result = client.get(
            source_id="youthcenter-api",
            url="https://example.test/policies",
        )

        self.assertEqual(b"ok", result.body)
        self.assertEqual(3, len(transport.requests))

    def test_exhausted_5xx_is_classified(self) -> None:
        transport = StubTransport([response(500), response(503)])
        client = client_for(transport, max_retries=1)

        with self.assertRaises(ServerResponseError) as raised:
            client.get(
                source_id="youthcenter-api",
                url="https://example.test/policies",
            )

        self.assertEqual(503, raised.exception.status)
        self.assertEqual(2, raised.exception.attempts)

    def test_backoff_and_request_interval_are_both_bounded(self) -> None:
        clock = FakeClock()
        transport = StubTransport([response(500), response(200)])
        client = client_for(
            transport,
            max_retries=1,
            backoff_seconds=0.5,
            request_interval_seconds=1.0,
            clock=clock,
        )

        client.get(
            source_id="youthcenter-api",
            url="https://example.test/policies",
        )

        self.assertEqual([0.5, 0.5], clock.sleeps)
        self.assertEqual(2, len(transport.requests))

    def test_parse_errors_do_not_include_body_or_secret_query_value(
        self,
    ) -> None:
        cases = (
            ("JSON", b"secret-response-body", "get_json"),
            ("XML", b"<secret-response-body>", "get_xml"),
        )
        for response_type, body, method_name in cases:
            with self.subTest(response_type=response_type):
                client = client_for(StubTransport([response(200, body)]))
                method = getattr(client, method_name)
                with self.assertRaises(ResponseParseError) as raised:
                    method(
                        source_id="test-source",
                        url="https://example.test/data",
                        query={"serviceKey": "secret-query-value"},
                    )

                message = str(raised.exception)
                self.assertNotIn("secret-response-body", message)
                self.assertNotIn("secret-query-value", message)
                self.assertIn("serviceKey=<redacted>", message)

    def test_redirect_status_is_not_followed_by_client_policy(self) -> None:
        transport = StubTransport([response(302)])
        client = client_for(transport)

        with self.assertRaises(UnexpectedResponseError) as raised:
            client.get(
                source_id="youthcenter-api",
                url="https://example.test/policies",
            )

        self.assertEqual(302, raised.exception.status)
        self.assertEqual(1, len(transport.requests))

    def test_redact_url_masks_all_query_values_and_user_information(self) -> None:
        safe = redact_url(
            "https://user:password@example.test/data"
            "?apiKeyNm=secret&pageNum=1#fragment"
        )

        self.assertEqual(
            "https://<redacted>@example.test/data"
            "?apiKeyNm=<redacted>&pageNum=<redacted>",
            safe,
        )
        self.assertNotIn("password", safe)
        self.assertNotIn("secret", safe)


if __name__ == "__main__":
    unittest.main()
