"""Verify Release 1 technical and independent manual evidence alignment."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_release_1 import AcceptanceAuditError, load_contract  # noqa: E402


DEFAULT_CONTRACT = ROOT / "data" / "release_1_acceptance.json"

REQUIRED_CHECKS: dict[str, tuple[str, ...]] = {
    "qa": (
        "actual-golden-search",
        "empty-results",
        "partial-unknown-boundary",
        "api-error-retry",
    ),
    "usability-review": (
        "query-and-condition-understanding",
        "result-reason-understanding",
        "source-and-freshness-understanding",
        "eligibility-guidance-understanding",
    ),
    "report-review": (
        "dataset-baseline",
        "contract-and-query-identity",
        "technical-results",
        "scope-risk-and-gate-status",
    ),
}


class EvidenceVerificationError(RuntimeError):
    """Raised when an evidence document cannot be loaded safely."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that Release 1 technical evidence and independent role "
            "reviews use the approved contract and actual snapshot."
        )
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Release 1 acceptance contract JSON",
    )
    parser.add_argument(
        "--technical-evidence",
        type=Path,
        required=True,
        help="sanitized JSON emitted by audit_release_1.py",
    )
    parser.add_argument(
        "--manual-evidence",
        type=Path,
        required=True,
        help="QA, usability and report review JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional verification report path; stdout is used when omitted",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="return zero only for an unexecuted pending review template",
    )
    return parser


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceVerificationError(f"could not load {label}: {path}") from error
    if not isinstance(value, dict):
        raise EvidenceVerificationError(f"{label} must be a JSON object")
    return value


def _blocker(
    code: str,
    message: str,
    *,
    role: str | None = None,
    check_id: str | None = None,
) -> dict[str, str]:
    blocker = {"code": code, "message": message}
    if role is not None:
        blocker["role"] = role
    if check_id is not None:
        blocker["check_id"] = check_id
    return blocker


def _has_timezone(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _valid_evidence_ref(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlsplit(value)
    if parsed.scheme:
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (ROOT / path).is_file()


def _validate_identity(
    *,
    document: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_sha256: str,
    label: str,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    comparisons = (
        ("release", contract.get("release")),
        ("gate", contract.get("gate")),
        ("contract_sha256", contract_sha256),
        ("dataset_baseline", contract.get("dataset_baseline")),
    )
    for field, expected in comparisons:
        if document.get(field) != expected:
            blockers.append(
                _blocker(
                    "EVIDENCE_IDENTITY_MISMATCH",
                    f"{label} field {field} does not match the acceptance contract.",
                )
            )
    return blockers


def validate_technical_evidence(
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    evidence: Mapping[str, Any],
) -> list[dict[str, str]]:
    blockers = _validate_identity(
        document=evidence,
        contract=contract,
        contract_sha256=contract_sha256,
        label="technical evidence",
    )
    if evidence.get("evidence_version") != "1.0.0":
        blockers.append(
            _blocker(
                "TECHNICAL_EVIDENCE_VERSION_INVALID",
                "Technical evidence_version must be 1.0.0.",
            )
        )
    if not _has_timezone(evidence.get("generated_at")):
        blockers.append(
            _blocker(
                "TECHNICAL_EVIDENCE_TIME_INVALID",
                "Technical generated_at must include a timezone.",
            )
        )
    if evidence.get("required_manual_evidence") != contract.get(
        "required_manual_evidence"
    ):
        blockers.append(
            _blocker(
                "TECHNICAL_MANUAL_ROLES_MISMATCH",
                "Technical evidence manual roles changed from the contract.",
            )
        )
    if evidence.get("technical_verdict") != "pass":
        blockers.append(
            _blocker(
                "TECHNICAL_EVIDENCE_BLOCKED",
                "Technical acceptance must pass before independent review is accepted.",
            )
        )
    if evidence.get("gate_verdict") != "blocked":
        blockers.append(
            _blocker(
                "TECHNICAL_GATE_VERDICT_INVALID",
                "Technical evidence must not issue a Gate G4 pass decision.",
            )
        )
    if evidence.get("gate_readiness") != "technical-pass-evidence-pending":
        blockers.append(
            _blocker(
                "TECHNICAL_GATE_READINESS_INVALID",
                "Passing technical evidence must still require independent reviews.",
            )
        )

    expected_scenarios = {
        scenario["id"]: scenario for scenario in contract.get("scenarios", [])
    }
    actual_results = evidence.get("scenarios")
    if not isinstance(actual_results, list):
        blockers.append(
            _blocker(
                "TECHNICAL_SCENARIOS_INVALID",
                "Technical evidence scenarios must be a list.",
            )
        )
        return blockers

    actual_by_id: dict[str, Mapping[str, Any]] = {}
    for result in actual_results:
        if not isinstance(result, Mapping) or not isinstance(result.get("id"), str):
            blockers.append(
                _blocker(
                    "TECHNICAL_SCENARIOS_INVALID",
                    "Every technical scenario result must have an id.",
                )
            )
            continue
        scenario_id = result["id"]
        if scenario_id in actual_by_id:
            blockers.append(
                _blocker(
                    "TECHNICAL_SCENARIO_DUPLICATED",
                    f"Technical scenario is duplicated: {scenario_id}.",
                )
            )
        actual_by_id[scenario_id] = result

    for scenario_id, scenario in expected_scenarios.items():
        result = actual_by_id.get(scenario_id)
        if result is None:
            blockers.append(
                _blocker(
                    "TECHNICAL_SCENARIO_MISSING",
                    f"Technical scenario is missing: {scenario_id}.",
                )
            )
            continue
        if result.get("status") != "pass":
            blockers.append(
                _blocker(
                    "TECHNICAL_SCENARIO_BLOCKED",
                    f"Technical scenario did not pass: {scenario_id}.",
                )
            )
        if result.get("query") != scenario.get("params", {}).get("q"):
            blockers.append(
                _blocker(
                    "TECHNICAL_QUERY_MISMATCH",
                    f"Technical scenario query changed: {scenario_id}.",
                )
            )
        target = result.get("target")
        expected_policy = scenario.get("expected_policy", {})
        if not isinstance(target, Mapping) or any(
            target.get(field) != expected_policy.get(field)
            for field in ("source_id", "external_id", "title")
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_TARGET_MISMATCH",
                    f"Technical target identity changed: {scenario_id}.",
                )
            )
            continue
        elapsed_ms = result.get("elapsed_ms")
        if (
            isinstance(elapsed_ms, bool)
            or not isinstance(elapsed_ms, (int, float))
            or elapsed_ms > scenario["maximum_elapsed_ms"]
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_RESPONSE_TIME_INVALID",
                    f"Technical response time is outside the contract: {scenario_id}.",
                )
            )
        rank = target.get("rank")
        if (
            isinstance(rank, bool)
            or not isinstance(rank, int)
            or rank < 1
            or rank > scenario["maximum_rank"]
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_TARGET_RANK_INVALID",
                    f"Technical target rank is outside the contract: {scenario_id}.",
                )
            )
        unknown_count = target.get("unknown_count")
        if (
            isinstance(unknown_count, bool)
            or not isinstance(unknown_count, int)
            or unknown_count > scenario["maximum_unknown_count"]
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_UNKNOWN_COUNT_INVALID",
                    f"Technical unknown count is outside the contract: {scenario_id}.",
                )
            )
        for field, expected in expected_policy.get("required_fields", {}).items():
            if target.get(field) != expected:
                blockers.append(
                    _blocker(
                        "TECHNICAL_TARGET_FIELD_MISMATCH",
                        f"Technical target field changed: {scenario_id}.{field}.",
                    )
                )
        categories = target.get("categories")
        if not isinstance(categories, list) or any(
            category not in categories
            for category in expected_policy.get("required_categories", [])
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_TARGET_CATEGORY_MISMATCH",
                    f"Technical target category changed: {scenario_id}.",
                )
            )
        verdicts = target.get("verdicts")
        if not isinstance(verdicts, Mapping) or any(
            verdicts.get(dimension) != expected
            for dimension, expected in scenario.get("required_verdicts", {}).items()
        ):
            blockers.append(
                _blocker(
                    "TECHNICAL_TARGET_VERDICT_MISMATCH",
                    f"Technical target verdict changed: {scenario_id}.",
                )
            )

    unexpected = sorted(set(actual_by_id) - set(expected_scenarios))
    if unexpected:
        blockers.append(
            _blocker(
                "TECHNICAL_SCENARIO_UNEXPECTED",
                f"Technical evidence has unexpected scenarios: {', '.join(unexpected)}.",
            )
        )
    return blockers


def validate_manual_evidence(
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    evidence: Mapping[str, Any],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    blockers = _validate_identity(
        document=evidence,
        contract=contract,
        contract_sha256=contract_sha256,
        label="manual evidence",
    )
    if evidence.get("evidence_version") != "1.0.0":
        blockers.append(
            _blocker(
                "MANUAL_EVIDENCE_VERSION_INVALID",
                "Manual evidence_version must be 1.0.0.",
            )
        )
    required_roles = contract.get("required_manual_evidence", [])
    if required_roles != list(REQUIRED_CHECKS):
        blockers.append(
            _blocker(
                "MANUAL_ROLE_CONTRACT_UNSUPPORTED",
                "Manual evidence roles do not match the DT7E verification contract.",
            )
        )

    reviews = evidence.get("reviews")
    if not isinstance(reviews, list):
        blockers.append(
            _blocker(
                "MANUAL_REVIEWS_INVALID",
                "Manual evidence reviews must be a list.",
            )
        )
        return blockers, {role: "missing" for role in REQUIRED_CHECKS}

    by_role: dict[str, Mapping[str, Any]] = {}
    for review in reviews:
        if not isinstance(review, Mapping) or not isinstance(review.get("role"), str):
            blockers.append(
                _blocker(
                    "MANUAL_REVIEW_INVALID",
                    "Every manual review must have a role.",
                )
            )
            continue
        role = review["role"]
        if role in by_role:
            blockers.append(
                _blocker(
                    "MANUAL_ROLE_DUPLICATED",
                    f"Manual review role is duplicated: {role}.",
                    role=role,
                )
            )
        by_role[role] = review

    role_statuses: dict[str, str] = {}
    for role, required_checks in REQUIRED_CHECKS.items():
        review = by_role.get(role)
        if review is None:
            role_statuses[role] = "missing"
            blockers.append(
                _blocker(
                    "MANUAL_ROLE_MISSING",
                    f"Required independent review is missing: {role}.",
                    role=role,
                )
            )
            continue

        verdict = review.get("verdict")
        role_statuses[role] = verdict if isinstance(verdict, str) else "invalid"
        reviewer = review.get("reviewer")
        if (
            not isinstance(reviewer, str)
            or not reviewer.strip()
            or reviewer.strip().upper() in {"TBD", "TODO", "REPLACE_ME"}
        ):
            blockers.append(
                _blocker(
                    "REVIEWER_MISSING",
                    "Reviewer name or team handle is required.",
                    role=role,
                )
            )
        if not _has_timezone(review.get("performed_at")):
            blockers.append(
                _blocker(
                    "REVIEW_TIME_INVALID",
                    "Review time must be an ISO 8601 timestamp with timezone.",
                    role=role,
                )
            )
        if review.get("independence_confirmed") is not True:
            blockers.append(
                _blocker(
                    "INDEPENDENCE_NOT_CONFIRMED",
                    "The reviewer must confirm role separation from the implementation.",
                    role=role,
                )
            )
        if verdict not in {"pass", "blocked"}:
            blockers.append(
                _blocker(
                    "REVIEW_PENDING",
                    "Review verdict must be pass or blocked after execution.",
                    role=role,
                )
            )

        checks = review.get("checks")
        if not isinstance(checks, list):
            blockers.append(
                _blocker(
                    "REVIEW_CHECKS_INVALID",
                    "Review checks must be a list.",
                    role=role,
                )
            )
            continue
        check_by_id: dict[str, Mapping[str, Any]] = {}
        for check in checks:
            if not isinstance(check, Mapping) or not isinstance(check.get("id"), str):
                blockers.append(
                    _blocker(
                        "REVIEW_CHECK_INVALID",
                        "Every review check must have an id.",
                        role=role,
                    )
                )
                continue
            check_id = check["id"]
            if check_id in check_by_id:
                blockers.append(
                    _blocker(
                        "REVIEW_CHECK_DUPLICATED",
                        f"Review check is duplicated: {check_id}.",
                        role=role,
                        check_id=check_id,
                    )
                )
            check_by_id[check_id] = check

        for check_id in required_checks:
            check = check_by_id.get(check_id)
            if check is None:
                blockers.append(
                    _blocker(
                        "REVIEW_CHECK_MISSING",
                        f"Required review check is missing: {check_id}.",
                        role=role,
                        check_id=check_id,
                    )
                )
                continue
            status = check.get("status")
            if status not in {"pass", "blocked"}:
                blockers.append(
                    _blocker(
                        "CHECK_PENDING",
                        "Check status must be pass or blocked after execution.",
                        role=role,
                        check_id=check_id,
                    )
                )
            notes = check.get("notes")
            if not isinstance(notes, str) or not notes.strip():
                blockers.append(
                    _blocker(
                        "CHECK_NOTES_MISSING",
                        "Executed checks require a concise observation.",
                        role=role,
                        check_id=check_id,
                    )
                )
            refs = check.get("evidence_refs")
            if (
                not isinstance(refs, list)
                or not refs
                or any(not _valid_evidence_ref(ref) for ref in refs)
            ):
                blockers.append(
                    _blocker(
                        "CHECK_EVIDENCE_MISSING",
                        "Checks require an existing repository file or HTTP(S) evidence URL.",
                        role=role,
                        check_id=check_id,
                    )
                )

        unexpected_checks = sorted(set(check_by_id) - set(required_checks))
        if unexpected_checks:
            blockers.append(
                _blocker(
                    "REVIEW_CHECK_UNEXPECTED",
                    f"Review has unexpected checks: {', '.join(unexpected_checks)}.",
                    role=role,
                )
            )
        check_statuses = {
            check.get("status")
            for check in check_by_id.values()
            if isinstance(check, Mapping)
        }
        if verdict == "pass" and check_statuses != {"pass"}:
            blockers.append(
                _blocker(
                    "REVIEW_VERDICT_INCONSISTENT",
                    "A pass review requires every required check to pass.",
                    role=role,
                )
            )
        if verdict == "blocked" and "blocked" not in check_statuses:
            blockers.append(
                _blocker(
                    "REVIEW_VERDICT_INCONSISTENT",
                    "A blocked review requires at least one blocked check.",
                    role=role,
                )
            )

    unexpected_roles = sorted(set(by_role) - set(REQUIRED_CHECKS))
    if unexpected_roles:
        blockers.append(
            _blocker(
                "MANUAL_ROLE_UNEXPECTED",
                f"Manual evidence has unexpected roles: {', '.join(unexpected_roles)}.",
            )
        )
    return blockers, role_statuses


def build_verification_report(
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    technical_evidence: Mapping[str, Any],
    manual_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    technical_blockers = validate_technical_evidence(
        contract=contract,
        contract_sha256=contract_sha256,
        evidence=technical_evidence,
    )
    manual_blockers, role_statuses = validate_manual_evidence(
        contract=contract,
        contract_sha256=contract_sha256,
        evidence=manual_evidence,
    )
    blockers = technical_blockers + manual_blockers
    codes = {blocker["code"] for blocker in blockers}
    if technical_blockers:
        readiness = "technical-evidence-invalid"
    elif any(status == "blocked" for status in role_statuses.values()):
        readiness = "independent-evidence-blocked"
    elif blockers:
        readiness = "independent-evidence-pending"
    else:
        readiness = "ready-for-team-leader-decision"
    return {
        "verification_version": "1.0.0",
        "release": contract.get("release"),
        "gate": contract.get("gate"),
        "contract_sha256": contract_sha256,
        "dataset_baseline": contract.get("dataset_baseline"),
        "technical_verdict": technical_evidence.get("technical_verdict"),
        "role_statuses": role_statuses,
        "gate_readiness": readiness,
        "gate_verdict": "blocked",
        "decision_note": (
            "This verifier checks evidence alignment only. "
            "The Team Leader issues the Gate G4 decision in DT7F."
        ),
        "blocker_codes": sorted(codes),
        "blockers": blockers,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        contract, digest = load_contract(args.contract)
        technical = load_json_object(
            args.technical_evidence,
            label="technical evidence",
        )
        manual = load_json_object(
            args.manual_evidence,
            label="manual evidence",
        )
        report = build_verification_report(
            contract=contract,
            contract_sha256=digest,
            technical_evidence=technical,
            manual_evidence=manual,
        )
    except (AcceptanceAuditError, EvidenceVerificationError) as error:
        print(f"Release 1 evidence verification failed: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.buffer.write(rendered.encode("utf-8"))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    if report["gate_readiness"] != "ready-for-team-leader-decision":
        if (
            args.allow_incomplete
            and report["gate_readiness"] == "independent-evidence-pending"
        ):
            return 0
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
