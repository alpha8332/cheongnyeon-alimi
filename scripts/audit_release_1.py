"""Run the executable Release 1 search acceptance contract over HTTP."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data" / "release_1_acceptance.json"
SEARCH_PATH = "/api/v1/policies/search"


class AcceptanceAuditError(RuntimeError):
    """Raised when the audit cannot execute safely or parse its contract."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Release 1 search acceptance contract against a live "
            "Backend and emit sanitized JSON evidence."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend origin without credentials",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Release 1 acceptance contract JSON",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="per-request timeout in seconds",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional JSON evidence path; stdout is used when omitted",
    )
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="return zero even when the technical verdict is blocked",
    )
    return parser


def load_contract(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceAuditError(
            f"could not load acceptance contract: {path}"
        ) from error
    if not isinstance(value, dict) or not isinstance(value.get("scenarios"), list):
        raise AcceptanceAuditError("acceptance contract must contain scenarios")
    if not value.get("release") or not value.get("gate") or not value["scenarios"]:
        raise AcceptanceAuditError("acceptance contract metadata is incomplete")
    required_scenario_keys = {
        "id",
        "params",
        "expected_policy",
        "maximum_unknown_count",
        "maximum_rank",
        "maximum_elapsed_ms",
    }
    scenario_ids: set[str] = set()
    for scenario in value["scenarios"]:
        if not isinstance(scenario, dict):
            raise AcceptanceAuditError("each acceptance scenario must be an object")
        if not required_scenario_keys.issubset(scenario):
            raise AcceptanceAuditError(
                f"acceptance scenario is incomplete: {scenario.get('id', '<unknown>')}"
            )
        scenario_id = scenario["id"]
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise AcceptanceAuditError("acceptance scenario id must be non-empty")
        if scenario_id in scenario_ids:
            raise AcceptanceAuditError(
                f"acceptance scenario id is duplicated: {scenario_id}"
            )
        scenario_ids.add(scenario_id)
        params = scenario["params"]
        expected_policy = scenario["expected_policy"]
        if not isinstance(params, dict) or not isinstance(params.get("q"), str):
            raise AcceptanceAuditError(
                f"acceptance scenario params are invalid: {scenario_id}"
            )
        if not params["q"].strip() or not isinstance(expected_policy, dict):
            raise AcceptanceAuditError(
                f"acceptance scenario policy contract is invalid: {scenario_id}"
            )
        for identity_field in ("source_id", "external_id", "title"):
            if not isinstance(expected_policy.get(identity_field), str):
                raise AcceptanceAuditError(
                    f"expected policy identity is invalid: {scenario_id}"
                )
        numeric_limits = (
            ("maximum_unknown_count", 0),
            ("maximum_rank", 1),
            ("maximum_elapsed_ms", 1),
        )
        for field, minimum in numeric_limits:
            limit = scenario[field]
            if isinstance(limit, bool) or not isinstance(limit, (int, float)):
                raise AcceptanceAuditError(
                    f"acceptance scenario limit is invalid: {scenario_id}.{field}"
                )
            if limit < minimum:
                raise AcceptanceAuditError(
                    f"acceptance scenario limit is too small: {scenario_id}.{field}"
                )
    return value, hashlib.sha256(raw).hexdigest()


def normalize_base_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AcceptanceAuditError("base URL must be an HTTP(S) origin")
    if parsed.username is not None or parsed.password is not None:
        raise AcceptanceAuditError("base URL must not contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise AcceptanceAuditError(
            "base URL must be an origin without path, query, or fragment"
        )
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def fetch_search(
    *,
    base_url: str,
    params: Mapping[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], float]:
    query = urlencode(
        {
            key: str(value).lower() if isinstance(value, bool) else value
            for key, value in params.items()
        }
    )
    request = Request(
        f"{base_url}{SEARCH_PATH}?{query}",
        headers={"Accept": "application/json"},
    )
    started = perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            status = response.status
            body = response.read()
    except HTTPError as error:
        raise AcceptanceAuditError(
            f"search endpoint returned HTTP {error.code}"
        ) from error
    except (URLError, TimeoutError) as error:
        raise AcceptanceAuditError("search endpoint is unavailable") from error
    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    if status != 200:
        raise AcceptanceAuditError(f"search endpoint returned HTTP {status}")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceAuditError("search endpoint returned invalid JSON") from error
    if not isinstance(payload, dict):
        raise AcceptanceAuditError("search response must be a JSON object")
    return payload, elapsed_ms


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _condition_matches(
    conditions: Sequence[Mapping[str, Any]],
    dimension: str,
    expected: Any,
) -> bool:
    for condition in conditions:
        if condition.get("dimension") != dimension:
            continue
        if condition.get("resolution") != "resolved":
            continue
        if condition.get("value") == expected:
            return True
        if expected in (condition.get("candidates") or []):
            return True
    return False


def _safe_item(item: Mapping[str, Any], rank: int) -> dict[str, Any]:
    policy = item.get("policy", {})
    return {
        "rank": rank,
        "source_id": policy.get("source_id"),
        "external_id": policy.get("external_id"),
        "title": policy.get("title"),
        "data_quality_status": policy.get("data_quality_status"),
        "application_status": policy.get("application_status"),
        "application_schedule": policy.get("application_schedule"),
        "categories": policy.get("categories", []),
        "unknown_count": item.get("unknown_count"),
        "verdicts": item.get("verdicts", {}),
        "score": item.get("score"),
    }


def evaluate_scenario(
    scenario: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    elapsed_ms: float,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    params = scenario["params"]
    interpreted = payload.get("interpreted_conditions", {})
    if interpreted.get("q_raw") != params.get("q"):
        blockers.append(
            _blocker(
                "QUERY_RAW_MISMATCH",
                "Backend did not preserve the original natural-language query.",
            )
        )

    conditions = interpreted.get("conditions", [])
    for dimension, expected in scenario.get("required_conditions", {}).items():
        if not _condition_matches(conditions, dimension, expected):
            blockers.append(
                _blocker(
                    "REQUIRED_CONDITION_MISSING",
                    f"Required {dimension} condition was not resolved as expected.",
                )
            )

    maximum_elapsed_ms = scenario["maximum_elapsed_ms"]
    if elapsed_ms > maximum_elapsed_ms:
        blockers.append(
            _blocker(
                "RESPONSE_TIME_BUDGET_EXCEEDED",
                f"Response time must be at most {maximum_elapsed_ms} ms.",
            )
        )

    items = payload.get("items", [])
    expected_policy = scenario["expected_policy"]
    target_rank: int | None = None
    target_item: Mapping[str, Any] | None = None
    for rank, item in enumerate(items, start=1):
        policy = item.get("policy", {})
        if (
            policy.get("source_id") == expected_policy["source_id"]
            and policy.get("external_id") == expected_policy["external_id"]
        ):
            target_rank = rank
            target_item = item
            break

    if target_item is None:
        blockers.append(
            _blocker(
                "EXPECTED_POLICY_NOT_RETURNED",
                "The approved expected policy was not returned in the audit window.",
            )
        )
    else:
        maximum_rank = scenario["maximum_rank"]
        if target_rank is None or target_rank > maximum_rank:
            blockers.append(
                _blocker(
                    "EXPECTED_POLICY_RANK_TOO_LOW",
                    f"Expected policy rank must be at most {maximum_rank}.",
                )
            )
        policy = target_item.get("policy", {})
        if policy.get("title") != expected_policy["title"]:
            blockers.append(
                _blocker(
                    "EXPECTED_POLICY_TITLE_MISMATCH",
                    "Expected policy identity has an unexpected title.",
                )
            )
        for field, expected in expected_policy.get("required_fields", {}).items():
            if policy.get(field) != expected:
                blockers.append(
                    _blocker(
                        "EXPECTED_POLICY_FIELD_MISMATCH",
                        f"Expected policy field {field} did not match the contract.",
                    )
                )
        categories = policy.get("categories", [])
        for category in expected_policy.get("required_categories", []):
            if category not in categories:
                blockers.append(
                    _blocker(
                        "EXPECTED_POLICY_CATEGORY_MISSING",
                        f"Expected policy category {category} is missing.",
                    )
                )
        unknown_count = target_item.get("unknown_count")
        if (
            not isinstance(unknown_count, int)
            or unknown_count > scenario["maximum_unknown_count"]
        ):
            blockers.append(
                _blocker(
                    "EXPECTED_POLICY_UNKNOWN_CONDITIONS",
                    "Expected policy contains unconfirmed required conditions.",
                )
            )
        verdicts = target_item.get("verdicts", {})
        for dimension, expected in scenario.get("required_verdicts", {}).items():
            if verdicts.get(dimension) != expected:
                blockers.append(
                    _blocker(
                        "EXPECTED_POLICY_VERDICT_MISMATCH",
                        f"Expected policy {dimension} verdict did not match.",
                    )
                )

    safe_items = [
        _safe_item(item, rank)
        for rank, item in enumerate(items[:5], start=1)
    ]
    return {
        "id": scenario["id"],
        "status": "pass" if not blockers else "blocked",
        "elapsed_ms": elapsed_ms,
        "total": payload.get("total"),
        "query": params.get("q"),
        "target": (
            _safe_item(target_item, target_rank)
            if target_item is not None and target_rank is not None
            else None
        ),
        "top_results": safe_items,
        "blockers": blockers,
    }


def build_report(
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    base_url: str,
    results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    technical_verdict = (
        "pass"
        if all(result.get("status") == "pass" for result in results)
        else "blocked"
    )
    return {
        "evidence_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": contract["release"],
        "gate": contract["gate"],
        "contract_sha256": contract_sha256,
        "base_url": base_url,
        "dataset_baseline": contract.get("dataset_baseline"),
        "technical_verdict": technical_verdict,
        "gate_verdict": "blocked",
        "gate_readiness": (
            "technical-blocked"
            if technical_verdict == "blocked"
            else "technical-pass-evidence-pending"
        ),
        "required_manual_evidence": contract.get(
            "required_manual_evidence", []
        ),
        "manual_review_policy": contract.get("manual_review_policy", {}),
        "scenarios": list(results),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        contract, digest = load_contract(args.contract)
        base_url = normalize_base_url(args.base_url)
        results = []
        for scenario in contract["scenarios"]:
            payload, elapsed_ms = fetch_search(
                base_url=base_url,
                params=scenario["params"],
                timeout=args.timeout,
            )
            results.append(
                evaluate_scenario(scenario, payload, elapsed_ms=elapsed_ms)
            )
        report = build_report(
            contract=contract,
            contract_sha256=digest,
            base_url=base_url,
            results=results,
        )
    except AcceptanceAuditError as error:
        print(f"Release 1 acceptance audit failed: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.buffer.write(rendered.encode("utf-8"))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    if report["technical_verdict"] == "blocked" and not args.allow_blocked:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
