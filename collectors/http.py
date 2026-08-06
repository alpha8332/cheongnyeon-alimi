"""Secret-safe HTTP client shared by source collectors."""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, TypeAlias

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


ScalarQueryValue: TypeAlias = str | int | float | bool
QueryValue: TypeAlias = ScalarQueryValue | Sequence[ScalarQueryValue]
JsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)


@dataclass(frozen=True)
class TransportResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class HttpTransport(Protocol):
    def send(
        self,
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> TransportResponse:
        """Send one request attempt."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: urllib.request.Request,
        file_pointer: object,
        code: int,
        message: str,
        headers: Mapping[str, str],
        new_url: str,
    ) -> None:
        return None


class UrllibTransport:
    """Standard-library transport that never forwards credentials on redirects."""

    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(_NoRedirectHandler())

    def send(
        self,
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> TransportResponse:
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return TransportResponse(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )
        except urllib.error.HTTPError as error:
            return TransportResponse(
                status=error.code,
                headers=dict(error.headers.items()) if error.headers else {},
                body=error.read(),
            )


@dataclass(frozen=True)
class HttpClientConfig:
    timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_seconds: float = 0.5
    request_interval_seconds: float = 1.0
    user_agent: str = "cheongnyeon-alimi-collector"

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")
        if self.request_interval_seconds < 0:
            raise ValueError("request_interval_seconds cannot be negative")
        if not self.user_agent.strip():
            raise ValueError("user_agent cannot be empty")


class HttpClient:
    """GET client with bounded retries, pacing, parsing, and safe errors."""

    def __init__(
        self,
        *,
        config: HttpClientConfig | None = None,
        transport: HttpTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config or HttpClientConfig()
        self._transport = transport or UrllibTransport()
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request_started: float | None = None
        self._pacing_lock = threading.Lock()

    def get(
        self,
        *,
        source_id: str,
        url: str,
        query: Mapping[str, QueryValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> TransportResponse:
        request_url = _build_url(url, query or {})
        safe_url = redact_url(request_url)
        request_headers = dict(headers or {})
        request_headers.setdefault("User-Agent", self.config.user_agent)
        request = urllib.request.Request(
            request_url,
            headers=request_headers,
            method="GET",
        )
        max_attempts = self.config.max_retries + 1

        for attempt in range(1, max_attempts + 1):
            self._wait_for_request_slot()
            try:
                response = self._transport.send(
                    request,
                    timeout=self.config.timeout_seconds,
                )
            except (TimeoutError, socket.timeout):
                if attempt < max_attempts:
                    self._backoff(attempt)
                    continue
                raise RequestTimeoutError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="request timed out",
                    attempts=attempt,
                ) from None
            except (urllib.error.URLError, OSError):
                if attempt < max_attempts:
                    self._backoff(attempt)
                    continue
                raise TransportError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="request transport failed",
                    attempts=attempt,
                ) from None
            except Exception:
                raise TransportError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="request transport failed unexpectedly",
                    attempts=attempt,
                ) from None

            if 200 <= response.status < 300:
                return response
            if response.status in (401, 403):
                raise AuthenticationError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="authentication was rejected",
                    status=response.status,
                    attempts=attempt,
                )
            if response.status == 429:
                raise RateLimitError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="source rate limit was reached",
                    status=response.status,
                    attempts=attempt,
                )
            if 400 <= response.status < 500:
                raise ClientResponseError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="source returned a client error",
                    status=response.status,
                    attempts=attempt,
                )
            if 500 <= response.status < 600:
                if attempt < max_attempts:
                    self._backoff(attempt)
                    continue
                raise ServerResponseError(
                    source_id=source_id,
                    safe_url=safe_url,
                    reason="source returned a server error",
                    status=response.status,
                    attempts=attempt,
                )
            raise UnexpectedResponseError(
                source_id=source_id,
                safe_url=safe_url,
                reason="source returned an unexpected HTTP status",
                status=response.status,
                attempts=attempt,
            )

        raise AssertionError("unreachable")

    def get_json(
        self,
        *,
        source_id: str,
        url: str,
        query: Mapping[str, QueryValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> JsonValue:
        response = self.get(
            source_id=source_id,
            url=url,
            query=query,
            headers=headers,
        )
        try:
            return json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ResponseParseError(
                source_id=source_id,
                safe_url=redact_url(_build_url(url, query or {})),
                reason="response is not valid JSON",
                status=response.status,
            ) from None

    def get_xml(
        self,
        *,
        source_id: str,
        url: str,
        query: Mapping[str, QueryValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> ElementTree.Element:
        response = self.get(
            source_id=source_id,
            url=url,
            query=query,
            headers=headers,
        )
        try:
            return ElementTree.fromstring(response.body)
        except (ElementTree.ParseError, UnicodeDecodeError):
            raise ResponseParseError(
                source_id=source_id,
                safe_url=redact_url(_build_url(url, query or {})),
                reason="response is not valid XML",
                status=response.status,
            ) from None

    def _wait_for_request_slot(self) -> None:
        interval = self.config.request_interval_seconds
        with self._pacing_lock:
            now = self._monotonic()
            if self._last_request_started is not None:
                remaining = interval - (now - self._last_request_started)
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._monotonic()
            self._last_request_started = now

    def _backoff(self, failed_attempt: int) -> None:
        delay = self.config.backoff_seconds * (2 ** (failed_attempt - 1))
        if delay > 0:
            self._sleep(delay)


def redact_url(url: str) -> str:
    """Mask every query value and any user information in a URL."""

    parsed = urllib.parse.urlsplit(url)
    netloc = parsed.netloc
    if "@" in netloc:
        netloc = f"<redacted>@{netloc.rsplit('@', 1)[1]}"
    query = "&".join(
        f"{urllib.parse.quote_plus(key)}=<redacted>"
        for key, _ in urllib.parse.parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme, netloc, parsed.path, query, "")
    )


def _build_url(url: str, query: Mapping[str, QueryValue]) -> str:
    parsed = urllib.parse.urlsplit(url)
    existing_query = urllib.parse.parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )
    supplied_query = list(query.items())
    encoded_query = urllib.parse.urlencode(
        [*existing_query, *supplied_query],
        doseq=True,
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, encoded_query, "")
    )
