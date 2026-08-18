"""Verify and apply a review-admission manifest through the existing importer."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import create_db_engine, create_session_factory  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.seed_importer import import_programs  # noqa: E402
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
    args = parser.parse_args(argv)

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

        engine = create_db_engine(args.database_url, sql_echo=False)
        session = create_session_factory(engine)()
        try:
            before_count = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
            session.rollback()
            rebuilt, programs = build_manifest(
                session,
                as_of=date.fromisoformat(manifest["as_of"]),
                raw_root=args.raw_root,
                checkpoint_root=args.checkpoint_root,
                decision_root=args.decision_root,
            )
            if rebuilt != manifest:
                raise ValueError("manifest inputs or database baseline drifted")

            expected = {
                (value["source_id"], value["external_id"])
                for value in manifest["decisions"]
                if value["outcome"] == "promote_partial"
            }
            if set(programs) != expected:
                raise ValueError("promoted program identities do not match manifest")
            for decision in manifest["decisions"]:
                identity = (decision["source_id"], decision["external_id"])
                if identity in programs and decision["policy_fingerprint"] is None:
                    raise ValueError("promoted program fingerprint is missing")

            result = import_programs(
                session,
                [programs[identity] for identity in sorted(programs)],
                dry_run=args.dry_run,
            )
            if result.failed or result.invalid or result.rejected or result.skipped:
                raise RuntimeError("review admission importer rejected the manifest")
            after_count = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
            if args.dry_run and after_count != before_count:
                raise RuntimeError("dry-run changed the scratch database")
            migration_revision = session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            session.rollback()
        finally:
            session.close()
            engine.dispose()
    except Exception as exc:  # noqa: BLE001 - stable CLI boundary
        print(
            f"review admission apply failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        "review admission apply "
        f"mode={'dry-run' if args.dry_run else 'apply'} "
        f"database={database_name} migration={migration_revision} "
        f"total={result.total} inserted={result.inserted} "
        f"updated={result.updated} unchanged={result.unchanged} "
        f"before={before_count} after={after_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

