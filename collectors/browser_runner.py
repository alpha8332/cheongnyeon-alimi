"""JSON boundary for a Data-owned Browser discovery subprocess."""

from __future__ import annotations

import json
import subprocess
import urllib.parse
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from collectors.regional_profile import RegionalAction


class BrowserRunnerError(RuntimeError):
    """The Browser subprocess failed without exposing response payloads."""


class BrowserRunnerTimeout(BrowserRunnerError):
    """The Browser subprocess exceeded its bounded timeout."""


@dataclass(frozen=True, slots=True)
class BrowserRunnerResult:
    final_url: str
    observations: tuple[dict[str, Any], ...]
    sample_external_id: str | None
    sample_title: str | None


class BrowserRunner:
    """Invoke a Browser implementation through one JSON stdin/stdout message."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not command or not all(
            isinstance(value, str) and value for value in command
        ):
            raise BrowserRunnerError("Browser runner command is invalid")
        if not 1 <= timeout_seconds <= 120:
            raise BrowserRunnerError(
                "Browser runner timeout must be between 1 and 120 seconds"
            )
        self._command = tuple(command)
        self._timeout_seconds = timeout_seconds

    def run(
        self,
        *,
        home_url: str,
        actions: Sequence[RegionalAction],
        allowed_hosts: Sequence[str] | None = None,
    ) -> BrowserRunnerResult:
        home_host = urllib.parse.urlsplit(home_url).hostname
        if not home_host or not home_url.startswith("https://"):
            raise BrowserRunnerError("Browser runner home URL is invalid")
        selected_hosts = tuple(
            value.lower() for value in (allowed_hosts or (home_host,))
        )
        if (
            not selected_hosts
            or home_host.lower() not in selected_hosts
            or any(not value or "/" in value for value in selected_hosts)
        ):
            raise BrowserRunnerError("Browser runner host allowlist is invalid")
        request = {
            "schema_version": "1.0.0",
            "home_url": home_url,
            "allowed_hosts": list(selected_hosts),
            "actions": [
                {
                    "kind": action.kind,
                    "target": action.target,
                    "value": action.value,
                }
                for action in actions
            ],
        }
        try:
            completed = subprocess.run(
                self._command,
                input=json.dumps(request, ensure_ascii=False).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise BrowserRunnerTimeout("Browser runner timed out") from None
        except OSError:
            raise BrowserRunnerError("Browser runner could not start") from None
        if completed.returncode != 0:
            raise BrowserRunnerError("Browser runner returned a failure")
        try:
            response = json.loads(completed.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise BrowserRunnerError(
                "Browser runner returned invalid JSON"
            ) from None
        result = _result(response)
        final_host = urllib.parse.urlsplit(result.final_url).hostname
        if not final_host or final_host.lower() not in selected_hosts:
            raise BrowserRunnerError("Browser runner left the allowed hosts")
        if result.observations != tuple(request["actions"]):
            raise BrowserRunnerError("Browser runner action replay drifted")
        return result


def _result(value: Any) -> BrowserRunnerResult:
    if not isinstance(value, dict) or value.get("status") != "ok":
        raise BrowserRunnerError("Browser runner response is not successful")
    final_url = value.get("final_url")
    observations = value.get("observations")
    if (
        not isinstance(final_url, str)
        or not final_url.startswith("https://")
        or not isinstance(observations, list)
        or not all(isinstance(item, dict) for item in observations)
    ):
        raise BrowserRunnerError("Browser runner response is invalid")
    sample_external_id = value.get("sample_external_id")
    sample_title = value.get("sample_title")
    if sample_external_id is not None and not isinstance(
        sample_external_id, str
    ):
        raise BrowserRunnerError("Browser runner sample ID is invalid")
    if sample_title is not None and not isinstance(sample_title, str):
        raise BrowserRunnerError("Browser runner sample title is invalid")
    return BrowserRunnerResult(
        final_url=final_url,
        observations=tuple(observations),
        sample_external_id=sample_external_id,
        sample_title=sample_title,
    )
