"""Build a safe, reproducible quality profile from completed Runtime snapshots."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.services.policy_search_evaluation import (  # noqa: E402
    MatchState,
    RegionCandidate,
    RegionQueryResolution,
    RegionResolutionState,
    RegionRuleEvidence,
    evaluate_age_condition,
    evaluate_region_condition,
)
from app.services.policy_search_projection import (  # noqa: E402
    build_policy_search_document,
)
from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID  # noqa: E402
from collectors.runtime import replay_runtime_raw  # noqa: E402
from collectors.snapshot import SnapshotManifestStore  # noqa: E402
from collectors.youthcenter import (  # noqa: E402
    SOURCE_ID as YOUTHCENTER_SOURCE_ID,
)


SOURCE_IDS = (YOUTHCENTER_SOURCE_ID, BOKJIRO_SOURCE_ID)
DEFAULT_SNAPSHOT_IDS = {
    YOUTHCENTER_SOURCE_ID: "6add34f7aad9456ab0abb19175b7621c",
    BOKJIRO_SOURCE_ID: "ffa74ef47e6048109f11bf40d1ac5e15",
}
DEFAULT_VISIBLE_STATUSES = {None, "open", "scheduled"}
SEARCH_TERMS = ("월세", "주거", "주거비", "전세", "임대", "청년")
GOLDEN_QUERY = "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?"
GOLDEN_TERMS = ("청년", "단기숙소", "지원")
GOLDEN_EXPECTED_IDENTITY = (
    YOUTHCENTER_SOURCE_ID,
    "20260430005400212969",
)
APPLICATION_PERIOD_SOURCE_FIELDS = {
    YOUTHCENTER_SOURCE_ID: ("aplyYmd", "aplyPrdSeCd"),
    BOKJIRO_SOURCE_ID: (),
}
FREE_TEXT_PERIOD_FIELDS = (
    "summary",
    "eligibility_text",
    "support_content",
    "application_method",
)
_FREE_TEXT_DATE = re.compile(
    r"(?<!\d)(?:(?:19|20)\d{2}\s*[-./]\s*\d{1,2}\s*[-./]\s*"
    r"\d{1,2}|(?:['’]?\d{2}|(?:19|20)\d{2})\s*년[^\n]{0,40}?"
    r"\d{1,2}\s*(?:[./]|월\s*)\s*\d{1,2}(?:\s*일)?)(?!\d)"
)
CHEONAN_ALIAS = "천안시"
CHEONAN_CODE = "4413000000"
CHUNGNAM_ALIAS = "충청남도"
CHUNGNAM_CODE = "4400000000"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replay completed release snapshots and emit a safe JSON quality "
            "profile without network or database access."
        )
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("runtime/raw"),
        help="stored Raw root (default: runtime/raw)",
    )
    parser.add_argument(
        "--youthcenter-snapshot-id",
        default=DEFAULT_SNAPSHOT_IDS[YOUTHCENTER_SOURCE_ID],
    )
    parser.add_argument(
        "--bokjiro-snapshot-id",
        default=DEFAULT_SNAPSHOT_IDS[BOKJIRO_SOURCE_ID],
    )
    parser.add_argument(
        "--region-seed",
        type=Path,
        default=Path("data/seeds/administrative_regions.json"),
    )
    parser.add_argument(
        "--region-alias-seed",
        type=Path,
        default=Path("data/seeds/administrative_region_aliases.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional JSON output path; stdout is used when omitted",
    )
    parser.add_argument(
        "--require-period-safety",
        action="store_true",
        help=(
            "exit non-zero unless Source period mapping, status consistency, "
            "and the release golden policy pass the period safety audit"
        ),
    )
    return parser


def _counter(values: Sequence[str | None]) -> dict[str, int]:
    counts = Counter("null" if value is None else value for value in values)
    return dict(sorted(counts.items()))


def _default_visible(program: Mapping[str, Any]) -> bool:
    return program.get("application_status") in DEFAULT_VISIBLE_STATUSES


def _period_values_present(program: Mapping[str, Any]) -> bool:
    return any(
        program.get(field_name) is not None
        for field_name in (
            "application_period_text",
            "application_start",
            "application_end",
            "application_schedule",
            "application_status",
        )
    )


def _structured_period_present(program: Mapping[str, Any]) -> bool:
    return any(
        program.get(field_name) is not None
        for field_name in (
            "application_start",
            "application_end",
            "application_schedule",
            "application_status",
        )
    )


def _free_text_date_fields(program: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        field_name
        for field_name in FREE_TEXT_PERIOD_FIELDS
        if isinstance(program.get(field_name), str)
        and _FREE_TEXT_DATE.search(program[field_name]) is not None
    )


def _parse_iso_date(value: Any) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _period_status_consistent(program: Mapping[str, Any]) -> bool:
    period_text = program.get("application_period_text")
    start = _parse_iso_date(program.get("application_start"))
    end = _parse_iso_date(program.get("application_end"))
    schedule = program.get("application_schedule")
    status = program.get("application_status")

    if not _period_values_present(program):
        return True
    if period_text is None:
        return False
    if start is not None and end is not None and start > end:
        return False
    if schedule == "always":
        return start is None and end is None and status == "open"
    if schedule == "until_budget_exhausted":
        return start is None and end is None and status is None
    if schedule == "fixed_period":
        if start is None and end is None:
            return status is None
        if start is None:
            return False
        collected_at = program.get("collected_at")
        if not isinstance(collected_at, str):
            return False
        try:
            as_of = datetime.fromisoformat(collected_at).date()
        except ValueError:
            return False
        if end is None:
            expected_status = "scheduled" if as_of < start else None
        else:
            expected_status = (
                "scheduled"
                if as_of < start
                else "closed" if as_of > end else "open"
            )
        return status == expected_status
    if schedule is not None:
        return False
    if status == "closed":
        return "마감" in period_text and start is None and end is None
    return status is None and start is None and end is None


def _period_safety_cohort(
    programs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "total": len(programs),
        "source_period_text": sum(
            program.get("application_period_text") is not None
            for program in programs
        ),
        "structured_period_or_status": sum(
            _structured_period_present(program) for program in programs
        ),
        "source_period_text_unstructured": sum(
            program.get("application_period_text") is not None
            and not _structured_period_present(program)
            for program in programs
        ),
        "unknown_period_and_status": sum(
            not _period_values_present(program) for program in programs
        ),
        "free_text_date_mentions_not_promoted": sum(
            bool(_free_text_date_fields(program))
            and program.get("application_period_text") is None
            for program in programs
        ),
        "unsafe_source_promotions": sum(
            _period_values_present(program)
            and not APPLICATION_PERIOD_SOURCE_FIELDS.get(
                program.get("source_id"), ()
            )
            for program in programs
        ),
        "period_status_inconsistencies": sum(
            not _period_status_consistent(program) for program in programs
        ),
    }


def _application_period_safety(
    programs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    visible = tuple(
        program for program in programs if _default_visible(program)
    )
    golden = next(
        (
            program
            for program in programs
            if (program.get("source_id"), program.get("external_id"))
            == GOLDEN_EXPECTED_IDENTITY
        ),
        None,
    )
    mentions_by_source = {
        source_id: sum(
            bool(_free_text_date_fields(program))
            and program.get("application_period_text") is None
            for program in programs
            if program.get("source_id") == source_id
        )
        for source_id in SOURCE_IDS
    }
    golden_source_id = None if golden is None else golden.get("source_id")
    all_cohort = _period_safety_cohort(programs)
    visible_cohort = _period_safety_cohort(visible)
    golden_safe = (
        golden is not None
        and bool(APPLICATION_PERIOD_SOURCE_FIELDS.get(golden_source_id, ()))
        and golden.get("application_period_text") is not None
        and _period_status_consistent(golden)
    )
    return {
        "passed": (
            all_cohort["unsafe_source_promotions"] == 0
            and all_cohort["period_status_inconsistencies"] == 0
            and golden_safe
        ),
        "free_text_date_promotion_allowed": False,
        "unknown_representation": "null",
        "source_mappings": {
            source_id: {
                "application_period_fields": list(
                    APPLICATION_PERIOD_SOURCE_FIELDS[source_id]
                ),
                "structured_promotion_allowed": bool(
                    APPLICATION_PERIOD_SOURCE_FIELDS[source_id]
                ),
            }
            for source_id in SOURCE_IDS
        },
        "all": all_cohort,
        "default_visible": visible_cohort,
        "free_text_date_mentions_not_promoted_by_source": mentions_by_source,
        "golden_policy": {
            "found": golden is not None,
            "source_mapping_evidence_available": bool(
                APPLICATION_PERIOD_SOURCE_FIELDS.get(golden_source_id, ())
            ),
            "source_period_text_present": (
                golden is not None
                and golden.get("application_period_text") is not None
            ),
            "application_schedule": (
                None if golden is None else golden.get("application_schedule")
            ),
            "application_status": (
                None if golden is None else golden.get("application_status")
            ),
            "period_status_consistent": (
                golden is not None and _period_status_consistent(golden)
            ),
            "safety_passed": golden_safe,
            "free_text_promotion_used": (
                golden is not None
                and _structured_period_present(golden)
                and golden.get("application_period_text") is None
            ),
            "eligibility_claim_allowed": False,
        },
    }


def _contains_terms(program: Mapping[str, Any], terms: Sequence[str]) -> bool:
    search_text = build_policy_search_document(program)["search_text"].casefold()
    compact = search_text.replace(" ", "")
    return all(
        term.casefold() in search_text
        or term.casefold().replace(" ", "") in compact
        for term in terms
    )


def _source_profile(
    replay: Any,
) -> dict[str, Any]:
    programs = replay.programs
    issue_codes = Counter(
        issue.code
        for issues in replay.normalization_issues
        for issue in issues
    )
    categories = Counter(
        category
        for program in programs
        for category in program["categories"]
    )
    provenance_documents = Counter(
        len(program["provenance"]) for program in programs
    )
    return {
        "raw_documents": replay.raw_document_count,
        "extracted": replay.extracted_count,
        "accepted": replay.accepted_count,
        "quality": {
            "valid": replay.valid_count,
            "partial": replay.partial_count,
            "invalid": replay.invalid_count,
        },
        "default_visible": sum(_default_visible(program) for program in programs),
        "application_status": _counter(
            [program["application_status"] for program in programs]
        ),
        "coverage_scope": _counter(
            [program["coverage_scope"] for program in programs]
        ),
        "region_rule_resolution": _counter(
            [
                rule["resolution_status"]
                for program in programs
                for rule in program["region_rules"]
            ]
        ),
        "age_bounds": {
            "both": sum(
                program["age_min"] is not None
                and program["age_max"] is not None
                for program in programs
            ),
            "one_sided": sum(
                (program["age_min"] is None)
                != (program["age_max"] is None)
                for program in programs
            ),
            "none": sum(
                program["age_min"] is None
                and program["age_max"] is None
                for program in programs
            ),
        },
        "categories": dict(sorted(categories.items())),
        "warning_codes": dict(sorted(issue_codes.items())),
        "provenance_document_count": {
            str(count): policies
            for count, policies in sorted(provenance_documents.items())
        },
    }


def _load_region_catalog(
    region_seed: Path,
    alias_seed: Path,
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[str, tuple[RegionCandidate, ...]],
]:
    regions_value = json.loads(region_seed.read_text(encoding="utf-8"))
    aliases_value = json.loads(alias_seed.read_text(encoding="utf-8"))
    catalog = {
        (region["scheme"], region["code"]): region
        for region in regions_value["regions"]
    }
    aliases: dict[str, list[RegionCandidate]] = {}
    for alias in aliases_value["aliases"]:
        identity = (alias["scheme"], alias["region_code"])
        region = catalog[identity]
        aliases.setdefault(alias["alias"], []).append(_region_candidate(region))
    return catalog, {
        alias: tuple(
            sorted(candidates, key=lambda item: (item.scheme, item.code))
        )
        for alias, candidates in aliases.items()
    }


def _region_candidate(region: Mapping[str, Any]) -> RegionCandidate:
    return RegionCandidate(
        scheme=region["scheme"],
        code=region["code"],
        name=region["name"],
        full_name=region["full_name"],
        level=region["level"],
        status=region["status"],
    )


def _resolve_region(
    alias: str,
    aliases: Mapping[str, tuple[RegionCandidate, ...]],
) -> RegionQueryResolution:
    candidates = aliases.get(alias, ())
    if not candidates:
        status = RegionResolutionState.UNMAPPED
    elif len(candidates) == 1:
        status = RegionResolutionState.MATCHED
    else:
        status = RegionResolutionState.AMBIGUOUS
    return RegionQueryResolution(status, candidates)


def _query_path(
    query: RegionQueryResolution,
    catalog: Mapping[tuple[str, str], Mapping[str, Any]],
) -> tuple[RegionCandidate, ...]:
    if query.status is not RegionResolutionState.MATCHED:
        return ()
    current = query.candidates[0]
    path: list[RegionCandidate] = []
    seen: set[tuple[str, str]] = set()
    while True:
        identity = (current.scheme, current.code)
        if identity in seen:
            raise RuntimeError("region hierarchy contains a cycle")
        seen.add(identity)
        path.append(current)
        parent_code = catalog[identity]["parent_code"]
        if parent_code is None:
            return tuple(path)
        current = _region_candidate(catalog[(current.scheme, parent_code)])


def _region_decision(
    program: Mapping[str, Any],
    query: RegionQueryResolution,
    query_path: Sequence[RegionCandidate],
    catalog: Mapping[tuple[str, str], Mapping[str, Any]],
) -> Any:
    rules = tuple(
        RegionRuleEvidence(
            relation=rule["relation"],
            resolution_status=rule["resolution_status"],
            region_scheme=rule["region_scheme"],
            region_code=rule["region_code"],
            region_status=(
                catalog[(rule["region_scheme"], rule["region_code"])]["status"]
                if (
                    rule["region_scheme"] is not None
                    and rule["region_code"] is not None
                    and (rule["region_scheme"], rule["region_code"]) in catalog
                )
                else None
            ),
            source_code=rule["source_code"],
            source_text=rule["source_text"],
        )
        for rule in program["region_rules"]
    )
    return evaluate_region_condition(
        coverage_scope=program["coverage_scope"],
        query=query,
        query_path=query_path,
        rules=rules,
    )


def _decision_counts(decisions: Sequence[Any]) -> dict[str, Any]:
    return {
        "states": _counter([decision.state.value for decision in decisions]),
        "reasons": _counter([decision.reason.value for decision in decisions]),
    }


def _golden_confirmed(row: Mapping[str, Any]) -> bool:
    return (
        row["age"]["state"] == "match"
        and row["region"]["state"] == "match"
        and row["data_quality_status"] == "valid"
        and row["application_status"] == "open"
        and row["application_schedule"] == "always"
        and "housing" in row["categories"]
    )


def build_report(
    *,
    raw_root: Path,
    snapshot_ids: Mapping[str, str],
    region_seed: Path,
    alias_seed: Path,
) -> dict[str, Any]:
    manifest_store = SnapshotManifestStore(raw_root)
    replays = {
        source_id: replay_runtime_raw(
            raw_root=raw_root,
            source_id=source_id,
            limit=5000,
            snapshot_id=snapshot_ids[source_id],
        )
        for source_id in SOURCE_IDS
    }
    manifests = {
        source_id: manifest_store.load(source_id, snapshot_ids[source_id])
        for source_id in SOURCE_IDS
    }
    programs = tuple(
        program
        for source_id in SOURCE_IDS
        for program in replays[source_id].programs
    )
    visible = tuple(program for program in programs if _default_visible(program))
    catalog, aliases = _load_region_catalog(region_seed, alias_seed)
    cheonan_query = _resolve_region(CHEONAN_ALIAS, aliases)
    cheonan_path = _query_path(cheonan_query, catalog)
    chungnam_query = _resolve_region(CHUNGNAM_ALIAS, aliases)
    chungnam_path = _query_path(chungnam_query, catalog)

    age_decisions = tuple(
        evaluate_age_condition(
            requested_age=27,
            age_min=program["age_min"],
            age_max=program["age_max"],
            age_condition_text=program["age_condition_text"],
        )
        for program in visible
    )
    region_decisions = tuple(
        _region_decision(program, cheonan_query, cheonan_path, catalog)
        for program in visible
    )
    chungnam_decisions = tuple(
        _region_decision(program, chungnam_query, chungnam_path, catalog)
        for program in visible
    )
    golden_rows: list[dict[str, Any]] = []
    for program, age, region in zip(
        visible, age_decisions, region_decisions, strict=True
    ):
        if not _contains_terms(program, GOLDEN_TERMS):
            continue
        if age.state is MatchState.MISMATCH or region.state is MatchState.MISMATCH:
            continue
        golden_rows.append(
            {
                "source_id": program["source_id"],
                "external_id": program["external_id"],
                "title": program["title"],
                "source_url": program["source_url"],
                "data_quality_status": program["data_quality_status"],
                "application_status": program["application_status"],
                "application_schedule": program["application_schedule"],
                "categories": list(program["categories"]),
                "age": {"state": age.state.value, "reason": age.reason.value},
                "region": {
                    "state": region.state.value,
                    "reason": region.reason.value,
                },
            }
        )

    title_counts = Counter(program["title"] for program in programs)
    duplicate_groups = {
        title: count for title, count in title_counts.items() if count > 1
    }
    return {
        "profile_version": "1.2.0",
        "offline_only": True,
        "snapshots": {
            source_id: {
                "snapshot_id": manifests[source_id].snapshot_id,
                "completed_at": manifests[source_id].completed_at.isoformat(),
                "items": manifests[source_id].item_count,
                "requests": manifests[source_id].request_count,
            }
            for source_id in SOURCE_IDS
        },
        "overall": {
            "accepted": len(programs),
            "valid": sum(
                replay.valid_count for replay in replays.values()
            ),
            "partial": sum(
                replay.partial_count for replay in replays.values()
            ),
            "invalid": sum(
                replay.invalid_count for replay in replays.values()
            ),
            "default_visible": len(visible),
            "default_visible_quality": _counter(
                [program["data_quality_status"] for program in visible]
            ),
            "default_visible_status": _counter(
                [program["application_status"] for program in visible]
            ),
        },
        "sources": {
            source_id: _source_profile(replays[source_id])
            for source_id in SOURCE_IDS
        },
        "application_period_safety": _application_period_safety(programs),
        "search_terms": {
            term: {
                "all": sum(_contains_terms(program, (term,)) for program in programs),
                "default_visible": sum(
                    _contains_terms(program, (term,)) for program in visible
                ),
            }
            for term in SEARCH_TERMS
        },
        "release_1_boundaries": {
            "age_27_default_visible": _decision_counts(age_decisions),
            "cheonan_default_visible": {
                "alias": CHEONAN_ALIAS,
                "canonical_code": CHEONAN_CODE,
                **_decision_counts(region_decisions),
            },
            "chungnam_default_visible": {
                "alias": CHUNGNAM_ALIAS,
                "canonical_code": CHUNGNAM_CODE,
                **_decision_counts(chungnam_decisions),
            },
        },
        "golden_query": {
            "query": GOLDEN_QUERY,
            "terms": list(GOLDEN_TERMS),
            "expected_identity": {
                "source_id": GOLDEN_EXPECTED_IDENTITY[0],
                "external_id": GOLDEN_EXPECTED_IDENTITY[1],
            },
            "default_visible_term_matches": sum(
                _contains_terms(program, GOLDEN_TERMS) for program in visible
            ),
            "confirmed_matches": sum(_golden_confirmed(row) for row in golden_rows),
            "expected_policy_confirmed": any(
                (row["source_id"], row["external_id"])
                == GOLDEN_EXPECTED_IDENTITY
                and _golden_confirmed(row)
                for row in golden_rows
            ),
            "non_mismatch_candidates": golden_rows,
            "candidate_exposure_allowed": any(
                (row["source_id"], row["external_id"])
                == GOLDEN_EXPECTED_IDENTITY
                and _golden_confirmed(row)
                for row in golden_rows
            ),
            "eligibility_claim_allowed": False,
        },
        "identity_and_provenance": {
            "unique_source_external_identities": len(
                {
                    (program["source_id"], program["external_id"])
                    for program in programs
                }
            ),
            "duplicate_title_groups": len(duplicate_groups),
            "rows_in_duplicate_title_groups": sum(duplicate_groups.values()),
            "maximum_same_title_count": max(duplicate_groups.values(), default=1),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        raw_root=args.raw_root,
        snapshot_ids={
            YOUTHCENTER_SOURCE_ID: args.youthcenter_snapshot_id,
            BOKJIRO_SOURCE_ID: args.bokjiro_snapshot_id,
        },
        region_seed=args.region_seed,
        alias_seed=args.region_alias_seed,
    )
    rendered = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output is None:
        sys.stdout.buffer.write(rendered.encode("utf-8"))
    else:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    if (
        args.require_period_safety
        and not report["application_period_safety"]["passed"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
