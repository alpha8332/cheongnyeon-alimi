"""Build the read-only review-admission-v1 manifest from stored evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import create_db_engine, create_session_factory  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.aggregator_baseline import load_aggregator_baseline  # noqa: E402
from collectors.cross_source_duplicate import (  # noqa: E402
    evaluate_cross_source_duplicate,
)
from collectors.gyeongbuk_youth import (  # noqa: E402
    SOURCE_ID as GYEONGBUK_SOURCE_ID,
    map_gyeongbuk_duplicate_evidence,
)
from collectors.normalizer import Normalizer  # noqa: E402
from collectors.regional_expansion import (  # noqa: E402
    EXPANDED_CAPTURE_SOURCE_IDS,
    RegionalBrowserExtractor,
    RegionalCheckpointStore,
    map_expanded_duplicate_evidence,
)
from collectors.regional_pilot import (  # noqa: E402
    BUSAN_SOURCE_ID,
    SEOUL_SOURCE_ID,
    map_representative_duplicate_evidence,
)
from collectors.review_admission import (  # noqa: E402
    AUDIT_SCHEMA_VERSION,
    RULE_VERSION,
    TAXONOMY_VERSION,
    AdmissionOutcome,
    ReviewAdmissionCandidate,
    classify_review_candidate,
    manifest_hash,
    policy_fingerprint,
)
from collectors.runtime import (  # noqa: E402
    _EXTRACTOR_TYPES,
    _checkpoint_batch,
    _load_source_documents,
    replay_runtime_raw,
)


DEFAULT_CHECKPOINT_ROOT = Path("runtime/decisions/regional-checkpoints")
DEFAULT_DECISION_ROOT = Path("runtime/decisions")
DEFAULT_OUTPUT = Path("runtime/decisions/review-admission-v1.json")


def build_manifest(
    db: Session,
    *,
    as_of: date,
    raw_root: Path,
    checkpoint_root: Path,
    decision_root: Path,
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    checked_at = datetime.combine(as_of, time.min, tzinfo=timezone.utc)
    baseline = load_aggregator_baseline(
        db,
        raw_root=raw_root,
        now=lambda: checked_at,
    )
    migration_revision = db.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()
    policy_count = db.scalar(select(func.count()).select_from(Policy))
    db.rollback()

    checkpoint_store = RegionalCheckpointStore(checkpoint_root)
    decisions = []
    promoted_programs: dict[tuple[str, str], dict[str, Any]] = {}
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    replay_counts = Counter()

    for path in sorted(checkpoint_root.glob("*.json")):
        checkpoint = checkpoint_store.load(path.stem)
        if checkpoint is None:
            continue
        replay = replay_runtime_raw(
            raw_root=raw_root,
            source_id=checkpoint.source_id,
            limit=len(checkpoint.captured_ids),
            checkpoint_root=checkpoint_root,
        )
        extracted = _checkpoint_extracted_policies(
            raw_root=raw_root,
            checkpoint=checkpoint,
        )
        policies = {str(policy.external_id): policy for policy in extracted}
        regional_by_id = {
            str(value["external_id"]): value
            for value in replay.regional_decisions
        }
        outcomes = {
            external_id: outcome.value
            for external_id, outcome in checkpoint.decisions
        }
        if set(regional_by_id) != {
            external_id
            for external_id, outcome in outcomes.items()
            if outcome != "failed"
        }:
            raise ValueError(
                f"checkpoint/replay identity drift: {checkpoint.source_id}"
            )

        for external_id, checkpoint_outcome in sorted(outcomes.items()):
            replay_counts[checkpoint_outcome] += 1
            if checkpoint_outcome != "review":
                continue
            policy = policies.get(external_id)
            regional = regional_by_id.get(external_id)
            if policy is None or regional is None:
                raise ValueError(
                    f"review evidence missing: {checkpoint.source_id}/{external_id}"
                )
            candidate = ReviewAdmissionCandidate(
                source_id=policy.source_id,
                external_id=policy.external_id,
                source_url=policy.source_url,
                provenance_ids=tuple(
                    item.raw_document_id for item in policy.provenance
                ),
                checkpoint_outcome=checkpoint_outcome,
                regionality=str(regional["regionality"]),
                application=str(regional["application"]),
                original_reason_codes=tuple(regional["reason_codes"]),
                item_texts=tuple(
                    value
                    for value in (
                        policy.title,
                        policy.eligibility_text,
                        policy.age_text,
                        policy.category_text,
                    )
                    if value is not None
                ),
                normalization_status="partial",
                policy_fingerprint="sha256:" + "0" * 64,
                duplicate_outcome="accepted_regional",
                duplicate_reason_codes=("duplicate_check_deferred",),
            )
            decision = classify_review_candidate(candidate)
            program = None
            if decision.outcome is AdmissionOutcome.PROMOTE_PARTIAL:
                try:
                    normalized = Normalizer().normalize(policy)
                except Exception as exc:  # normalization is an audited boundary
                    candidate = replace(
                        candidate,
                        normalization_status="invalid",
                        residual_unknown_codes=(
                            f"normalization_exception_{type(exc).__name__}",
                        ),
                        policy_fingerprint=None,
                        duplicate_outcome=None,
                        duplicate_reason_codes=(),
                    )
                    decision = classify_review_candidate(candidate)
                else:
                    program = (
                        normalized.program.to_dict()
                        if normalized.program is not None
                        else None
                    )
                    candidate = replace(
                        candidate,
                        normalization_status=normalized.status.value,
                        residual_unknown_codes=tuple(
                            issue.code for issue in normalized.issues
                        ),
                        policy_fingerprint=(
                            policy_fingerprint(program)
                            if program is not None
                            else None
                        ),
                        duplicate_outcome=(
                            "accepted_regional" if program is not None else None
                        ),
                    )
                    decision = classify_review_candidate(candidate)
            else:
                candidate = replace(
                    candidate,
                    normalization_status=None,
                    policy_fingerprint=None,
                    duplicate_outcome=None,
                    duplicate_reason_codes=(),
                )
                decision = classify_review_candidate(candidate)
            if (
                decision.outcome is AdmissionOutcome.PROMOTE_PARTIAL
                and program is not None
            ):
                duplicate = _duplicate_decision(policy, normalized.program, baseline)
                candidate = replace(
                    candidate,
                    duplicate_outcome=duplicate.outcome.value,
                    duplicate_reason_codes=duplicate.reason_codes,
                )
                decision = classify_review_candidate(candidate)
            decisions.append(decision.to_dict())
            source_counts[policy.source_id][decision.outcome.value] += 1
            if decision.outcome is AdmissionOutcome.PROMOTE_PARTIAL:
                if program is None:
                    raise ValueError("promoted admission has no normalized program")
                promoted_programs[(policy.source_id, policy.external_id)] = program

    external_holds, external_manifest_hash = _external_duplicate_holds(
        decision_root,
        excluded_sources=frozenset(source_counts),
    )
    decisions.sort(key=lambda value: (value["source_id"], value["external_id"]))
    outcome_counts = Counter(value["outcome"] for value in decisions)
    promoted = [
        value
        for value in decisions
        if value["outcome"] == AdmissionOutcome.PROMOTE_PARTIAL.value
    ]
    source_summary = [
        {
            "source_id": source_id,
            "review": sum(counts.values()),
            **{
                outcome.value: counts[outcome.value]
                for outcome in AdmissionOutcome
            },
        }
        for source_id, counts in sorted(source_counts.items())
    ]
    manifest: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "as_of": as_of.isoformat(),
        "git_sha": _git_sha(),
        "database": {
            "migration_revision": str(migration_revision),
            "policy_count": int(policy_count or 0),
            "aggregator_baseline_id": baseline.baseline_id,
        },
        "inputs": {
            "checkpoint_sha256": _tree_hash(checkpoint_root),
            "external_decision_sha256": external_manifest_hash,
        },
        "checkpoint_counts": dict(sorted(replay_counts.items())),
        "summary": {
            "regional_review": len(decisions),
            **{
                outcome.value: outcome_counts[outcome.value]
                for outcome in AdmissionOutcome
            },
            "external_duplicate_hold": len(external_holds),
            "promoted_hard_exclusion_count": sum(
                bool(value["duplicate_outcome"] != "accepted_regional")
                for value in promoted
            ),
        },
        "sources": source_summary,
        "decisions": decisions,
        "external_duplicate_holds": external_holds,
        "blockers": [],
    }
    manifest["manifest_sha256"] = manifest_hash(manifest)
    return manifest, promoted_programs


def _checkpoint_extracted_policies(*, raw_root: Path, checkpoint):
    documents = _load_source_documents(raw_root, checkpoint.source_id)
    selected = _checkpoint_batch(
        documents,
        checkpoint,
        len(checkpoint.captured_ids),
    )
    extractor = (
        RegionalBrowserExtractor(checkpoint.source_id)
        if checkpoint.source_id == SEOUL_SOURCE_ID
        else _EXTRACTOR_TYPES[checkpoint.source_id]()
    )
    return extractor.extract(selected)


def _duplicate_decision(policy, program, baseline):
    if policy.source_id == GYEONGBUK_SOURCE_ID:
        mapper = map_gyeongbuk_duplicate_evidence
    elif policy.source_id in {BUSAN_SOURCE_ID, SEOUL_SOURCE_ID}:
        mapper = map_representative_duplicate_evidence
    elif policy.source_id in EXPANDED_CAPTURE_SOURCE_IDS:
        mapper = map_expanded_duplicate_evidence
    else:
        raise ValueError(f"no duplicate mapper for {policy.source_id}")
    return evaluate_cross_source_duplicate(program, mapper(policy), baseline)


def _external_duplicate_holds(
    decision_root: Path,
    *,
    excluded_sources: frozenset[str],
) -> tuple[list[dict[str, Any]], str]:
    selected_payloads: list[bytes] = []
    holds: list[dict[str, Any]] = []
    for source_root in sorted(decision_root.iterdir()):
        if (
            not source_root.is_dir()
            or source_root.name == "regional-checkpoints"
            or source_root.name in excluded_sources
        ):
            continue
        manifests = []
        for path in sorted(source_root.glob("*.json")):
            try:
                payload = path.read_bytes()
                value = json.loads(payload.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            manifest_id = value.get("manifest_id")
            decisions = value.get("decisions")
            if not isinstance(manifest_id, str) or not isinstance(decisions, list):
                continue
            timestamps = [
                str(item.get("candidate_collected_at", ""))
                for item in decisions
                if isinstance(item, dict)
            ]
            manifests.append(
                (max(timestamps, default=""), manifest_id, payload, value)
            )
        if not manifests:
            continue
        _, manifest_id, payload, value = max(
            manifests,
            key=lambda item: (item[0], item[1]),
        )
        selected_payloads.append(payload)
        for decision in value["decisions"]:
            if decision.get("outcome") != "duplicate_review_required":
                continue
            candidate = decision.get("candidate", {})
            holds.append(
                {
                    "source_id": candidate.get("source_id"),
                    "external_id": candidate.get("external_id"),
                    "outcome": "hold_review",
                    "admission_reason_codes": ["duplicate_review_required"],
                    "duplicate_reason_codes": sorted(decision.get("reason_codes", [])),
                    "decision_manifest_id": manifest_id,
                }
            )
    digest = hashlib.sha256()
    for payload in selected_payloads:
        digest.update(payload)
    holds.sort(key=lambda value: (str(value["source_id"]), str(value["external_id"])))
    return holds, digest.hexdigest()


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=DEFAULT_CHECKPOINT_ROOT,
    )
    parser.add_argument(
        "--decision-root",
        type=Path,
        default=DEFAULT_DECISION_ROOT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    engine = create_db_engine(settings.DATABASE_URL, sql_echo=False)
    session = create_session_factory(engine)()
    try:
        manifest, _ = build_manifest(
            session,
            as_of=date.fromisoformat(args.as_of),
            raw_root=args.raw_root,
            checkpoint_root=args.checkpoint_root,
            decision_root=args.decision_root,
        )
        _atomic_write(args.output, manifest)
    except Exception as exc:  # noqa: BLE001 - stable CLI boundary
        session.rollback()
        print(
            f"review admission audit failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        session.close()
        engine.dispose()
    summary = manifest["summary"]
    print(
        "review admission audit "
        f"review={summary['regional_review']} "
        f"promote_partial={summary['promote_partial']} "
        f"hold_review={summary['hold_review']} "
        f"exclude_duplicate={summary['exclude_duplicate']} "
        f"external_duplicate_hold={summary['external_duplicate_hold']} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
