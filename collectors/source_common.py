"""Shared helpers for source-specific response handling."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping

from collectors.errors import ResponseParseError
from collectors.http import TransportResponse


def response_content_type(
    response: TransportResponse,
    *,
    default: str,
) -> str:
    for name, value in response.headers.items():
        if name.lower() == "content-type":
            return value
    return default


def ensure_secret_not_in_payload(
    *,
    source_id: str,
    source_url: str,
    response: TransportResponse,
    secret: str,
) -> None:
    variants = {
        secret,
        urllib.parse.quote(secret, safe=""),
        urllib.parse.unquote(secret),
    }
    for variant in variants:
        if variant and variant.encode("utf-8") in response.body:
            raise ResponseParseError(
                source_id=source_id,
                safe_url=source_url,
                reason="response payload contains request credential",
                status=response.status,
            )


def safe_parse_error(
    *,
    source_id: str,
    source_url: str,
    response: TransportResponse,
    reason: str,
) -> ResponseParseError:
    return ResponseParseError(
        source_id=source_id,
        safe_url=source_url,
        reason=reason,
        status=response.status,
    )


def query_with_secret(
    secret_name: str,
    secret: str,
    values: Mapping[str, str | int],
) -> dict[str, str | int]:
    return {secret_name: secret, **values}
