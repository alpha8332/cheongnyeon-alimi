"""Audit Data 06 XLSX candidates against approved aggregator snapshots and DB."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import create_db_engine, create_session_factory  # noqa: E402
from app.services.aggregator_baseline import load_aggregator_baseline  # noqa: E402


DEFAULT_INVENTORY = (
    ROOT / "data/reference/supplemental_official_policy_inventory.json"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data/reference/supplemental_official_policy_duplicate_audit.json"
)
DIRECT_ID_KINDS = {
    "wlfareInfoId": "bokjiro-central-welfare-api",
    "plcyNo": "youthcenter-api",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--raw-root", type=Path, default=ROOT / "runtime/raw")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory_bytes = canonical_source_bytes(args.inventory.read_bytes())
    inventory = json.loads(inventory_bytes.decode("utf-8"))

    engine = create_db_engine(settings.DATABASE_URL, sql_echo=False)
    session = create_session_factory(engine)()
    try:
        baseline = load_aggregator_baseline(session, raw_root=args.raw_root)
        session.rollback()
    finally:
        session.close()
        engine.dispose()

    report = build_report(
        inventory,
        baseline,
        inventory_sha256=hashlib.sha256(inventory_bytes).hexdigest(),
    )
    _atomic_write(args.output, report)
    summary = report["summary"]
    print(
        "supplemental duplicate audit "
        f"exact={summary['exact_duplicate']} "
        f"review={summary['review_required']} "
        f"potentially_new={summary['potentially_new']} "
        f"not_assessed={summary['not_assessed']} output={args.output}"
    )
    return 0


def canonical_source_bytes(value: bytes) -> bytes:
    """Keep evidence hashes stable across LF and CRLF worktrees."""
    return value.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def build_report(
    inventory: dict[str, object],
    baseline,
    *,
    inventory_sha256: str,
) -> dict[str, object]:
    by_identity = {
        (record.identity.source_id, record.identity.external_id): record
        for record in baseline.records
    }
    by_title: dict[str, list[object]] = defaultdict(list)
    by_url: dict[str, list[object]] = defaultdict(list)
    for record in baseline.records:
        by_title[_comparison_text(record.title)].append(record)
        for url in record.canonical_urls:
            canonical = _canonical_url(url)
            if canonical is not None:
                by_url[canonical].append(record)

    decisions: list[dict[str, object]] = []
    counts: dict[str, int] = defaultdict(int)
    for candidate in inventory["policy_candidates"]:
        matched: list[object] = []
        reason_codes: list[str] = []
        identity = candidate["external_identity"]
        if (
            candidate["source_group"] == "approved-aggregator-comparison"
            and identity is not None
            and identity["kind"] in DIRECT_ID_KINDS
        ):
            key = (DIRECT_ID_KINDS[identity["kind"]], identity["value"])
            record = by_identity.get(key)
            if record is not None:
                matched = [record]
                outcome = "exact_duplicate"
                reason_codes.append("aggregator_external_id_match")
                if _comparison_text(candidate["title"]) != _comparison_text(
                    record.title
                ):
                    reason_codes.append("title_conflict")
            else:
                outcome = "review_required"
                reason_codes.append("direct_id_missing_from_baseline")
        elif candidate["inventory_status"] != "candidate":
            outcome = "not_assessed"
            reason_codes.append(candidate["inventory_status"])
        else:
            canonical = _canonical_url(candidate["canonical_url"])
            if canonical is not None:
                matched.extend(by_url.get(canonical, []))
            if matched:
                outcome = "exact_duplicate"
                reason_codes.append("canonical_url_match")
            else:
                matched.extend(by_title.get(_comparison_text(candidate["title"]), []))
                if matched:
                    outcome = "review_required"
                    reason_codes.append("normalized_title_match_only")
                else:
                    outcome = "potentially_new"
                    reason_codes.append("no_exact_id_url_or_title_match")
        counts[outcome] += 1
        decisions.append(
            {
                "candidate_id": candidate["candidate_id"],
                "input_rows": candidate["input_rows"],
                "input_disposition": candidate["inventory_status"],
                "duplicate_outcome": outcome,
                "reason_codes": reason_codes,
                "matched_policies": [
                    {
                        "source_id": record.identity.source_id,
                        "external_id": record.identity.external_id,
                        "title": record.title,
                    }
                    for record in sorted(
                        set(matched),
                        key=lambda item: (
                            item.identity.source_id,
                            item.identity.external_id,
                        ),
                    )
                ],
            }
        )
    return {
        "schema_version": "1.0.0",
        "audit_id": "supplemental-policy-duplicate-audit-20260817",
        "inventory_id": inventory["inventory_id"],
        "inventory_sha256": inventory_sha256,
        "baseline": baseline.to_dict(),
        "comparison_contract": {
            "exact": [
                "approved aggregator source_id + external_id",
                "canonical public URL",
            ],
            "review_only": ["normalized title"],
            "not_compared": [
                "XLSX collection-method text",
                "XLSX document-note text",
                "missing period/support evidence",
            ],
        },
        "summary": {
            "candidate_identity_count": len(decisions),
            "exact_duplicate": counts["exact_duplicate"],
            "review_required": counts["review_required"],
            "potentially_new": counts["potentially_new"],
            "not_assessed": counts["not_assessed"],
        },
        "decisions": decisions,
    }


def _comparison_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _canonical_url(value: str) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    path = parsed.path or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunsplit(("https", host, path, query, ""))


def _atomic_write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
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


if __name__ == "__main__":
    raise SystemExit(main())
