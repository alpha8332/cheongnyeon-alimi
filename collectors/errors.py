"""Safe, classified errors raised by collector infrastructure."""

from __future__ import annotations


class CollectorError(Exception):
    """Base class for expected collector failures."""


class CollectorConfigurationError(CollectorError):
    """The collector or registry configuration is invalid."""


class HttpRequestError(CollectorError):
    """Base class for HTTP failures with an already-redacted URL."""

    def __init__(
        self,
        *,
        source_id: str,
        safe_url: str,
        reason: str,
        status: int | None = None,
        attempts: int | None = None,
    ) -> None:
        parts = [reason, f"source={source_id}", f"url={safe_url}"]
        if status is not None:
            parts.append(f"status={status}")
        if attempts is not None:
            parts.append(f"attempts={attempts}")
        super().__init__("; ".join(parts))
        self.source_id = source_id
        self.safe_url = safe_url
        self.status = status
        self.attempts = attempts


class AuthenticationError(HttpRequestError):
    """The server rejected authentication or authorization."""


class RateLimitError(HttpRequestError):
    """The source rejected the request because of rate limiting."""


class ClientResponseError(HttpRequestError):
    """A non-authentication 4xx response was returned."""


class ServerResponseError(HttpRequestError):
    """A retryable 5xx response remained unsuccessful."""


class UnexpectedResponseError(HttpRequestError):
    """A response outside the accepted 2xx/4xx/5xx ranges was returned."""


class RequestTimeoutError(HttpRequestError):
    """The request timed out after the configured attempts."""


class TransportError(HttpRequestError):
    """The transport failed after the configured attempts."""


class ResponseParseError(HttpRequestError):
    """The successful response body could not be parsed."""


class EmptyResponseError(HttpRequestError):
    """The source returned a valid envelope without collection items."""
