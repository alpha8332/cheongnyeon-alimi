"""Cross-field validation for the Data 06 supplemental Source inventory."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from collectors.validation import JsonSchemaValidator, ValidationIssue


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = (
    ROOT
    / "data/schema/supplemental_official_policy_inventory.schema.json"
)


class SupplementalInventoryValidator:
    """Validate schema plus lineage and Source lifecycle invariants."""

    def __init__(self, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
        self.schema_validator = JsonSchemaValidator(schema_path)

    def issues(self, candidate: Any) -> tuple[ValidationIssue, ...]:
        schema_issues = self.schema_validator.schema_issues(candidate)
        if schema_issues:
            return schema_issues
        return tuple(supplemental_inventory_issues(candidate))


def supplemental_inventory_issues(
    inventory: Mapping[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    candidates = inventory["policy_candidates"]
    source_groups = inventory["source_groups"]
    group_by_id = {group["source_group_id"]: group for group in source_groups}

    candidate_ids: set[str] = set()
    covered_rows: list[int] = []
    for index, candidate in enumerate(candidates):
        path = f"$.policy_candidates[{index}]"
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            issues.append(_error(f"{path}.candidate_id", "duplicate_candidate_id"))
        candidate_ids.add(candidate_id)
        covered_rows.extend(candidate["input_rows"])
        group = group_by_id.get(candidate["source_group"])
        if group is None:
            issues.append(_error(f"{path}.source_group", "unknown_source_group"))
        else:
            if not set(candidate["input_rows"]).issubset(group["input_rows"]):
                issues.append(_error(f"{path}.input_rows", "source_row_mismatch"))
            if candidate["hostname"] not in group["input_domains"]:
                issues.append(_error(f"{path}.hostname", "source_domain_mismatch"))
        _public_https(candidate["url"], f"{path}.url", issues)
        _public_https(candidate["canonical_url"], f"{path}.canonical_url", issues)
        untrusted = candidate["untrusted_input"]
        if untrusted["note_present"] != (untrusted["note_sha256"] is not None):
            issues.append(_error(f"{path}.untrusted_input", "note_hash_mismatch"))

    if len(covered_rows) != 64 or len(set(covered_rows)) != 64:
        issues.append(_error("$.policy_candidates", "input_lineage_not_exact"))

    group_ids: set[str] = set()
    approved_source_ids: set[str] = set()
    grouped_rows: list[int] = []
    for index, group in enumerate(source_groups):
        path = f"$.source_groups[{index}]"
        group_id = group["source_group_id"]
        if group_id in group_ids:
            issues.append(_error(f"{path}.source_group_id", "duplicate_source_group"))
        group_ids.add(group_id)
        grouped_rows.extend(group["input_rows"])
        status = group["status"]
        if status == "approved":
            if group["implementation_status"] not in {
                "pending",
                "adapter_ready",
                "implemented_http",
            }:
                issues.append(
                    _error(
                        f"{path}.implementation_status",
                        "approved_implementation_status",
                    )
                )
            source_id = group["source_id"]
            if source_id in approved_source_ids:
                issues.append(_error(f"{path}.source_id", "duplicate_source_id"))
            approved_source_ids.add(source_id)
            if (
                not group["approved_list_urls"]
                or not group["approved_detail_url_patterns"]
            ):
                issues.append(_error(path, "approved_allowlist_missing"))
            if group["request_budget"] is None or group["external_identity"] is None:
                issues.append(_error(path, "approved_execution_boundary_missing"))
            if group["preflight"]["robots"]["status"] != "allowed":
                issues.append(
                    _error(
                        f"{path}.preflight.robots",
                        "approved_robots_not_allowed",
                    )
                )
            if group["preflight"]["technical_access"] != "available":
                issues.append(
                    _error(
                        f"{path}.preflight.technical_access",
                        "approved_access_unavailable",
                    )
                )
            if group["resume_condition"] is not None:
                issues.append(
                    _error(
                        f"{path}.resume_condition",
                        "approved_resume_condition",
                    )
                )
        else:
            expected = "blocked" if status == "blocked" else "rejected"
            if group["implementation_status"] != expected:
                issues.append(
                    _error(
                        f"{path}.implementation_status",
                        "inactive_status_mismatch",
                    )
                )
            if group["source_id"] is not None:
                issues.append(_error(f"{path}.source_id", "inactive_source_id"))
            if group["approved_list_urls"] or group["approved_detail_url_patterns"]:
                issues.append(_error(path, "inactive_allowlist"))
            if (
                group["request_budget"] is not None
                or group["external_identity"] is not None
            ):
                issues.append(_error(path, "inactive_execution_boundary"))
            if not group["resume_condition"]:
                issues.append(
                    _error(
                        f"{path}.resume_condition",
                        "inactive_resume_missing",
                    )
                )
        for url_index, url in enumerate(group["approved_list_urls"]):
            _public_https(url, f"{path}.approved_list_urls[{url_index}]", issues)

    if set(grouped_rows) != set(covered_rows):
        issues.append(_error("$.source_groups", "source_lineage_not_exact"))
    if len(approved_source_ids) != 5:
        issues.append(_error("$.source_groups", "approved_source_count"))

    conflict_ids = {
        candidate_id
        for conflict in inventory["same_url_title_conflicts"]
        for candidate_id in conflict["candidate_ids"]
    }
    statuses_by_id = {
        candidate["candidate_id"]: candidate["inventory_status"]
        for candidate in candidates
    }
    if not any(statuses_by_id[item] == "data_error" for item in conflict_ids):
        issues.append(_error("$.same_url_title_conflicts", "conflict_not_quarantined"))
    return issues


def _public_https(
    value: str,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        issues.append(_error(path, "non_public_https_url"))


def _error(path: str, code: str) -> ValidationIssue:
    return ValidationIssue(
        path=path,
        code=code,
        message=code.replace("_", " "),
        severity="error",
    )
