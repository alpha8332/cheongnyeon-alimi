"""Audit whether every user-visible DB policy can reach the public dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import create_db_engine  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.models.policy_search import PolicyRegionRule  # noqa: E402
from app.repositories.policy_lifecycle import public_policy_predicates  # noqa: E402
from scripts.build_public_bootstrap_dataset import (  # noqa: E402
    DEFAULT_CONTRACT,
    content_safety_counts,
    load_source_contract,
    policy_to_normalized_program,
)


DEFAULT_OUTPUT = ROOT / "runtime/public_dataset/parity-report.json"
KST = timezone(timedelta(hours=9))


class PublicDatasetParityError(ValueError):
    """Raised when parity inputs cannot produce deterministic evidence."""


def _comparison_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _exclusion_reason(
    source_id: str, contract: Mapping[str, Any]
) -> str:
    exclusions = contract["known_exclusions"]
    for selector in ("source_id", "source_prefix"):
        for item in exclusions:
            if item["selector"] != selector:
                continue
            value = item["value"]
            if selector == "source_id" and source_id == value:
                return str(item["reason_code"])
            if selector == "source_prefix" and source_id.startswith(value):
                return str(item["reason_code"])
    return "default_exclude"


def _unsafe_reasons(
    record: Mapping[str, Any], contract: Mapping[str, Any]
) -> tuple[str, ...]:
    counts = content_safety_counts([record], contract)
    reason_by_count = {
        "institutional_contact_count": "institutional_contact",
        "email_match_count": "email",
        "personal_mobile_match_count": "personal_mobile",
        "forbidden_query_key_match_count": "forbidden_query_key",
    }
    return tuple(
        reason_by_count[key]
        for key, value in counts.items()
        if key in reason_by_count and value not in {0, False}
    )


def build_report(
    policies: Sequence[Policy],
    *,
    rules_by_policy: Mapping[int, Sequence[PolicyRegionRule]],
    contract: Mapping[str, Any],
    as_of: date,
) -> dict[str, Any]:
    allowed_source_ids = {
        str(item["source_id"]) for item in contract["included_sources"]
    }
    public_titles = {
        _comparison_text(policy.title)
        for policy in policies
        if policy.source_id in allowed_source_ids
    }
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    source_safety_reasons: dict[str, Counter[str]] = defaultdict(Counter)
    safety_reason_row_counts: Counter[str] = Counter()
    publishable_row_count = 0
    public_candidate_row_count = 0
    excluded_source_row_count = 0
    content_safety_excluded_row_count = 0
    exact_title_review_count = 0
    unique_title_gap_count = 0

    for policy in policies:
        counts = source_counts[policy.source_id]
        counts["user_visible"] += 1
        if policy.source_id not in allowed_source_ids:
            excluded_source_row_count += 1
            counts["excluded_source"] += 1
            if _comparison_text(policy.title) in public_titles:
                exact_title_review_count += 1
                counts["exact_title_review"] += 1
            else:
                unique_title_gap_count += 1
                counts["unique_title_gap"] += 1
            continue

        public_candidate_row_count += 1
        counts["public_candidate"] += 1
        record = policy_to_normalized_program(
            policy, rules_by_policy.get(int(policy.id), ())
        )
        unsafe_reasons = _unsafe_reasons(record, contract)
        if unsafe_reasons:
            content_safety_excluded_row_count += 1
            counts["content_safety_excluded"] += 1
            safety_reason_row_counts.update(unsafe_reasons)
            source_safety_reasons[policy.source_id].update(unsafe_reasons)
        else:
            publishable_row_count += 1
            counts["publishable"] += 1

    all_source_ids = sorted(set(source_counts) | allowed_source_ids)
    sources = []
    for source_id in all_source_ids:
        counts = source_counts[source_id]
        included = source_id in allowed_source_ids
        sources.append(
            {
                "source_id": source_id,
                "decision": "include" if included else "exclude",
                "reason_code": (
                    "included_source"
                    if included
                    else _exclusion_reason(source_id, contract)
                ),
                "user_visible_row_count": counts["user_visible"],
                "public_candidate_row_count": counts["public_candidate"],
                "publishable_row_count": counts["publishable"],
                "excluded_source_row_count": counts["excluded_source"],
                "content_safety_excluded_row_count": counts[
                    "content_safety_excluded"
                ],
                "content_safety_reason_row_counts": dict(
                    sorted(source_safety_reasons[source_id].items())
                ),
                "exact_title_review_count": counts["exact_title_review"],
                "unique_title_gap_count": counts["unique_title_gap"],
            }
        )

    user_visible_row_count = len(policies)
    parity_gap_row_count = user_visible_row_count - publishable_row_count
    return {
        "schema_version": "1.0.0",
        "as_of": as_of.isoformat(),
        "source_contract_version": contract["contract_version"],
        "comparison_contract": {
            "user_visible_quality_statuses": ["valid", "partial"],
            "lifecycle": "active and application_end >= as_of or absent",
            "exact_title_is_review_only": True,
            "raw_payload_compared": False,
        },
        "summary": {
            "parity_status": "pass" if parity_gap_row_count == 0 else "blocked",
            "user_visible_row_count": user_visible_row_count,
            "public_source_candidate_row_count": public_candidate_row_count,
            "publishable_row_count": publishable_row_count,
            "excluded_source_row_count": excluded_source_row_count,
            "content_safety_excluded_row_count": content_safety_excluded_row_count,
            "content_safety_reason_row_counts": dict(
                sorted(safety_reason_row_counts.items())
            ),
            "exact_title_review_count": exact_title_review_count,
            "unique_title_gap_count": unique_title_gap_count,
            "parity_gap_row_count": parity_gap_row_count,
        },
        "sources": sources,
    }


def audit_database(
    database_url: str,
    *,
    contract: Mapping[str, Any],
    as_of: date,
) -> dict[str, Any]:
    engine = create_db_engine(database_url, sql_echo=False)
    try:
        with Session(engine) as session:
            policies = list(
                session.scalars(
                    select(Policy)
                    .where(
                        Policy.data_quality_status.in_(("valid", "partial")),
                        *public_policy_predicates(as_of=as_of),
                    )
                    .order_by(Policy.source_id, Policy.external_id, Policy.id)
                )
            )
            if not policies:
                raise PublicDatasetParityError(
                    "no user-visible policy was found"
                )
            policy_ids = [int(policy.id) for policy in policies]
            rules_by_policy: dict[int, list[PolicyRegionRule]] = defaultdict(list)
            rules = session.scalars(
                select(PolicyRegionRule)
                .where(PolicyRegionRule.policy_id.in_(policy_ids))
                .order_by(PolicyRegionRule.policy_id, PolicyRegionRule.id)
            )
            for rule in rules:
                rules_by_policy[int(rule.policy_id)].append(rule)
            return build_report(
                policies,
                rules_by_policy=rules_by_policy,
                contract=contract,
                as_of=as_of,
            )
    finally:
        engine.dispose()


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--source-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--as-of", type=date.fromisoformat)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-parity", action="store_true")
    args = parser.parse_args()
    try:
        selected_date = args.as_of or datetime.now(KST).date()
        contract = load_source_contract(args.source_contract)
        report = audit_database(
            args.database_url, contract=contract, as_of=selected_date
        )
        _atomic_write(args.output, report)
        summary = report["summary"]
        print(
            json.dumps(
                {
                    "status": "PUBLIC_DATASET_PARITY_"
                    + str(summary["parity_status"]).upper(),
                    "as_of": report["as_of"],
                    **summary,
                    "output": str(args.output),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        if args.require_parity and summary["parity_status"] != "pass":
            return 2
        return 0
    except Exception as exc:
        print(
            "PUBLIC_DATASET_PARITY_AUDIT_FAILED: " + type(exc).__name__,
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
