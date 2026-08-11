"""Cross-field validation for the regional policy source inventory."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from collectors.validation import JsonSchemaValidator, ValidationIssue


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = (
    ROOT
    / "data/schema/regional_youth_policy_source_inventory.schema.json"
)


class RegionalSourceInventoryValidator:
    """Validate schema and lifecycle-dependent regional source rules."""

    def __init__(
        self,
        schema_path: str | Path = DEFAULT_SCHEMA_PATH,
        *,
        require_decisions: bool = False,
    ) -> None:
        self.schema_validator = JsonSchemaValidator(schema_path)
        self.require_decisions = require_decisions

    def issues(self, candidate: Any) -> tuple[ValidationIssue, ...]:
        schema_issues = self.schema_validator.schema_issues(candidate)
        if schema_issues:
            return schema_issues
        return tuple(
            regional_source_inventory_issues(
                candidate,
                require_decisions=self.require_decisions,
            )
        )


def regional_source_inventory_issues(
    candidate: Mapping[str, Any],
    *,
    require_decisions: bool = False,
) -> list[ValidationIssue]:
    """Return semantic errors not expressible in the shared schema subset."""

    issues: list[ValidationIssue] = []
    sources = candidate.get("sources", [])
    source_ids: set[str] = set()

    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        status = source["status"]
        source_id = source["source_id"]
        preflight = source["preflight"]
        mapping = source["region_reference"]

        if require_decisions and status == "candidate":
            issues.append(
                _error(
                    f"{path}.status",
                    "source_decision_required",
                    "RYP1 inventory cannot retain candidate sources",
                )
            )

        if status != "candidate":
            for field in (
                "operator",
                "robots",
                "terms",
                "license",
                "technical_access",
            ):
                if preflight[field] == "unchecked":
                    issues.append(
                        _error(
                            f"{path}.preflight.{field}",
                            "preflight_required",
                            "decided sources require completed preflight",
                        )
                    )
            if preflight["last_checked_at"] is None:
                issues.append(
                    _error(
                        f"{path}.preflight.last_checked_at",
                        "preflight_timestamp_required",
                        "decided sources require a preflight timestamp",
                    )
                )

        if mapping["mapping_status"] == "matched_active":
            if mapping["active_code"] is None:
                issues.append(
                    _error(
                        f"{path}.region_reference.active_code",
                        "active_region_code_required",
                        "matched_active requires an active region code",
                    )
                )
            if mapping["historical_codes"]:
                issues.append(
                    _error(
                        f"{path}.region_reference.historical_codes",
                        "active_region_has_history",
                        "matched_active cannot retain historical codes",
                    )
                )
        else:
            if mapping["active_code"] is not None:
                issues.append(
                    _error(
                        f"{path}.region_reference.active_code",
                        "historical_region_has_active_code",
                        "historical review cannot claim an active code",
                    )
                )
            if not mapping["historical_codes"]:
                issues.append(
                    _error(
                        f"{path}.region_reference.historical_codes",
                        "historical_region_code_required",
                        "historical review requires at least one retired code",
                    )
                )

        if status == "approved":
            _approved_source_issues(source, path, issues)
            if source_id is not None and source_id in source_ids:
                issues.append(
                    _error(
                        f"{path}.source_id",
                        "duplicate_source_id",
                        "approved source IDs must be unique",
                    )
                )
            if source_id is not None:
                source_ids.add(source_id)
        elif status in {"candidate", "blocked", "rejected"}:
            if source_id is not None:
                issues.append(
                    _error(
                        f"{path}.source_id",
                        "inactive_source_id",
                        "non-approved sources cannot have a source ID",
                    )
                )
            for field in (
                "approved_list_urls",
                "approved_detail_url_patterns",
            ):
                if source[field]:
                    issues.append(
                        _error(
                            f"{path}.{field}",
                            "inactive_source_allowlist",
                            "non-approved sources cannot have allowlists",
                        )
                    )
            if source["request_budget"] is not None:
                issues.append(
                    _error(
                        f"{path}.request_budget",
                        "inactive_source_request_budget",
                        "non-approved sources cannot have a request budget",
                    )
                )

    return issues


def _approved_source_issues(
    source: Mapping[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    source_id = source["source_id"]
    preflight = source["preflight"]
    if not source_id:
        issues.append(
            _error(
                f"{path}.source_id",
                "approved_source_id_required",
                "approved sources require a stable source ID",
            )
        )
    if not source["approved_list_urls"]:
        issues.append(
            _error(
                f"{path}.approved_list_urls",
                "approved_list_url_required",
                "approved sources require at least one list URL",
            )
        )
    if not source["approved_detail_url_patterns"]:
        issues.append(
            _error(
                f"{path}.approved_detail_url_patterns",
                "approved_detail_pattern_required",
                "approved sources require at least one detail URL pattern",
            )
        )

    budget = source["request_budget"]
    if budget is None:
        issues.append(
            _error(
                f"{path}.request_budget",
                "approved_request_budget_required",
                "approved sources require an explicit request budget",
            )
        )
    else:
        if budget["max_list_requests"] > 1:
            issues.append(
                _error(
                    f"{path}.request_budget.max_list_requests",
                    "list_request_budget_exceeded",
                    "RYP1 permits at most one list request per pilot run",
                )
            )
        if budget["max_detail_requests"] > 5:
            issues.append(
                _error(
                    f"{path}.request_budget.max_detail_requests",
                    "detail_request_budget_exceeded",
                    "RYP1 permits at most five detail requests per pilot run",
                )
            )
        if budget["minimum_interval_seconds"] < 2:
            issues.append(
                _error(
                    f"{path}.request_budget.minimum_interval_seconds",
                    "request_interval_too_short",
                    "regional source requests require at least a two-second interval",
                )
            )

    if preflight["operator"] != "verified":
        issues.append(
            _error(
                f"{path}.preflight.operator",
                "approved_operator_unverified",
                "approved sources require a verified operator",
            )
        )
    if preflight["robots"] not in {"allowed", "not_published"}:
        issues.append(
            _error(
                f"{path}.preflight.robots",
                "approved_robots_disallowed",
                "approved source paths must not be disallowed by robots rules",
            )
        )
    if preflight["technical_access"] != "available":
        issues.append(
            _error(
                f"{path}.preflight.technical_access",
                "approved_source_unavailable",
                "approved sources require deterministic HTTP access",
            )
        )

    home_host = urlsplit(source["home_url"]).hostname
    for index, url in enumerate(source["approved_list_urls"]):
        if urlsplit(url).hostname != home_host:
            issues.append(
                _error(
                    f"{path}.approved_list_urls[{index}]",
                    "list_url_host_mismatch",
                    "approved list URLs must remain on the source home host",
                )
            )
    for index, pattern in enumerate(
        source["approved_detail_url_patterns"]
    ):
        target = pattern.removeprefix("POST ").split(" (", 1)[0]
        if urlsplit(target).hostname != home_host:
            issues.append(
                _error(
                    f"{path}.approved_detail_url_patterns[{index}]",
                    "detail_url_host_mismatch",
                    "approved detail patterns must remain on the source home host",
                )
            )


def _error(path: str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        path=path,
        code=code,
        message=message,
        severity="error",
    )
