"""Environment configuration for live source collectors."""

from __future__ import annotations

import os
from collections.abc import Mapping

from collectors.errors import CollectorConfigurationError
from collectors.http import HttpClientConfig


def required_secret(
    name: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    source = os.environ if environ is None else environ
    value = source.get(name)
    if value is None or not value or value != value.strip():
        raise CollectorConfigurationError(
            f"required environment variable is missing: {name}"
        )
    if any(character in value for character in "\r\n"):
        raise CollectorConfigurationError(
            f"required environment variable is invalid: {name}"
        )
    return value


def http_config_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
) -> HttpClientConfig:
    source = os.environ if environ is None else environ
    defaults = HttpClientConfig()
    return HttpClientConfig(
        timeout_seconds=_float_value(
            source,
            "HTTP_TIMEOUT_SECONDS",
            defaults.timeout_seconds,
        ),
        max_retries=_int_value(
            source,
            "HTTP_MAX_RETRIES",
            defaults.max_retries,
        ),
        backoff_seconds=defaults.backoff_seconds,
        request_interval_seconds=_float_value(
            source,
            "HTTP_REQUEST_DELAY_SECONDS",
            defaults.request_interval_seconds,
        ),
        user_agent=defaults.user_agent,
    )


def _float_value(
    environ: Mapping[str, str],
    name: str,
    default: float,
) -> float:
    value = environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise CollectorConfigurationError(
            f"environment variable must be numeric: {name}"
        ) from None


def _int_value(
    environ: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    value = environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise CollectorConfigurationError(
            f"environment variable must be an integer: {name}"
        ) from None
