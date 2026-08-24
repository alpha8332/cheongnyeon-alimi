"""Verify and apply a review-admission manifest through the existing importer."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import create_db_engine, create_session_factory  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.collection_runs import (  # noqa: E402
    CollectionRunCounts,
    CollectionRunWriter,
)
from app.services.seed_importer import ImportResult, import_programs  # noqa: E402
from collectors.review_admission import (  # noqa: E402
    RULE_VERSION,
    manifest_hash,
)
from collectors.validation import JsonSchemaValidator  # noqa: E402
from scripts.audit_review_admission import build_manifest  # noqa: E402


DEFAULT_SCHEMA = ROOT / "data/schema/review_admission_audit.schema.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("runtime/decisions/regional-checkpoints"),
    )
    parser.add_argument(
        "--decision-root",
        type=Path,
        default=Path("runtime/decisions"),
    )
    parser.add_argument("--database-url", default=settings.DATABASE_URL)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--test-apply", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    engine = None
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        issues = JsonSchemaValidator(DEFAULT_SCHEMA).schema_issues(manifest)
        if issues:
            raise ValueError("manifest schema validation failed")
        if manifest.get("rule_version") != RULE_VERSION:
            raise ValueError("manifest rule version is not supported")
        if manifest.get("manifest_sha256") != manifest_hash(manifest):
            raise ValueError("manifest hash does not match its content")

        database_name = make_url(args.database_url).database or ""
        if args.dry_run and not database_name.endswith("_test"):
            raise ValueError("dry-run requires a database whose name ends in _test")
        if args.apply and database_name.endswith("_test"):
            raise ValueError("apply mode refuses a scratch _test database")
        if args.test_apply and not database_name.endswith("_test"):
            raise ValueError("test-apply requires a scratch _test database")

        engine = create_db_engine(args.database_url, sql_echo=False)
        session_factory = create_session_factory(engine)
        session = session_factory()
        try:
            before_count = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
            expected = _promoted_identities(manifest)
            existing_expected_count = _existing_identity_count(session, expected)
            baseline_count = int(manifest["database"]["policy_count"])
            if before_count - existing_expected_count != baseline_count:
                raise ValueError("database policy baseline drifted")
            rebuilt, programs = build_manifest(
                session,
                as_of=date.fromisoformat(manifest["as_of"]),
                raw_root=args.raw_root,
                checkpoint_root=args.checkpoint_root,
                decision_root=args.decision_root,
            )
            rebuilt["database"]["policy_count"] = baseline_count
            rebuilt["manifest_sha256"] = manifest_hash(rebuilt)
            if rebuilt != manifest:
                raise ValueError("manifest inputs or database baseline drifted")

            if set(programs) != expected:
                raise ValueError("promoted program identities do not match manifest")
            for decision in manifest["decisions"]:
                identity = (decision["source_id"], decision["external_id"])
                if identity in programs and decision["policy_fingerprint"] is None:
                    raise ValueError("promoted program fingerprint is missing")
            session.rollback()
        finally:
            session.close()

        result = _import_by_source(
            session_factory,
            programs,
            dry_run=args.dry_run,
            record_runs=not args.dry_run,
        )
        verification = session_factory()
        try:
            after_count = int(
                verification.scalar(
                    select(func.count()).select_from(Policy)
                )
                or 0
            )
            migration_revision = verification.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            verification.rollback()
        finally:
            verification.close()
        if args.dry_run and after_count != before_count:
            raise RuntimeError("dry-run changed the scratch database")
        if not args.dry_run and after_count != before_count + result.inserted:
            raise RuntimeError("applied policy count does not match inserts")
    except Exception as exc:  # noqa: BLE001 - stable CLI boundary
        print(
            f"review admission apply failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()

    print(
        "review admission apply "
        f"mode={_mode_name(args)} "
        f"database={database_name} migration={migration_revision} "
        f"total={result.total} inserted={result.inserted} "
        f"updated={result.updated} unchanged={result.unchanged} "
        f"before={before_count} after={after_count}"
    )
    return 0


def _mode_name(args: argparse.Namespace) -> str:
    if args.dry_run:
        return "dry-run"
    if args.test_apply:
        return "test-apply"
    return "apply"


def _promoted_identities(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (value["source_id"], value["external_id"])
        for value in manifest["decisions"]
        if value["outcome"] == "promote_partial"
    }


def _existing_identity_count(session, identities: set[tuple[str, str]]) -> int:
    if not identities:
        return 0
    conditions = [
        and_(Policy.source_id == source_id, Policy.external_id == external_id)
        for source_id, external_id in sorted(identities)
    ]
    return int(
        session.scalar(
            select(func.count()).select_from(Policy).where(or_(*conditions))
        )
        or 0
    )


def _import_by_source(
    session_factory,
    programs: dict[tuple[str, str], dict[str, Any]],
    *,
    dry_run: bool,
    record_runs: bool,
) -> ImportResult:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for identity in sorted(programs):
        grouped[identity[0]].append(programs[identity])

    counts: Counter[str] = Counter()
    run_writer = CollectionRunWriter(session_factory) if record_runs else None
    for source_id in sorted(grouped):
        selected = grouped[source_id]
        run_id = None
        if run_writer is not None:
            run_id = run_writer.start(
                source_id=source_id,
                run_type="runtime_import",
                trigger_type="cli",
                requested_count=len(selected),
            )
        source_session = session_factory()
        try:
            source_result = import_programs(
                source_session,
                selected,
                dry_run=dry_run,
            )
        except Exception as exc:
            _finish_failed_run(run_writer, run_id, type(exc).__name__)
            raise
        finally:
            source_session.close()

        has_errors = bool(
            source_result.failed
            or source_result.invalid
            or source_result.rejected
            or source_result.skipped
        )
        if run_writer is not None and run_id is not None:
            run_writer.finish(
                run_id,
                status="failed" if has_errors else "succeeded",
                counts=_collection_run_counts(source_result),
            )
        if has_errors:
            raise RuntimeError(
                f"review admission importer rejected source {source_id}"
            )
        for field in (
            "total",
            "validated",
            "accepted",
            "partial",
            "invalid",
            "inserted",
            "updated",
            "unchanged",
            "duplicate",
            "skipped",
            "rejected",
            "failed",
        ):
            counts[field] += int(getattr(source_result, field))

    return ImportResult(
        total=counts["total"],
        validated=counts["validated"],
        accepted=counts["accepted"],
        partial=counts["partial"],
        invalid=counts["invalid"],
        inserted=counts["inserted"],
        updated=counts["updated"],
        unchanged=counts["unchanged"],
        duplicate=counts["duplicate"],
        skipped=counts["skipped"],
        rejected=counts["rejected"],
        failed=counts["failed"],
        committed=not dry_run,
        dry_run=dry_run,
    )


def _collection_run_counts(result: ImportResult) -> CollectionRunCounts:
    return CollectionRunCounts(
        requested_count=result.total,
        extracted_count=result.total,
        accepted_count=result.accepted,
        partial_count=result.partial,
        invalid_count=result.invalid,
        duplicate_count=result.duplicate,
        rejected_count=result.rejected,
        inserted_count=result.inserted,
        updated_count=result.updated,
        unchanged_count=result.unchanged,
        skipped_count=result.skipped,
        failed_count=result.failed,
    )


def _finish_failed_run(run_writer, run_id, error_type: str) -> None:
    if run_writer is None or run_id is None:
        return
    try:
        run_writer.finish(
            run_id,
            status="failed",
            counts=CollectionRunCounts(failed_count=1),
            error_type=error_type,
        )
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
