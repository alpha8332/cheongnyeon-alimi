"""Promote a public dataset only from the latest successful collection runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT, ROOT / "scripts"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import create_db_engine  # noqa: E402
from app.models.collection_run import CollectionRun  # noqa: E402
from build_public_bootstrap_dataset import (  # noqa: E402
    DEFAULT_CONTRACT,
    PublicDatasetError,
    load_records,
    load_source_contract,
    verify_release,
    write_release,
)
from build_public_dataset_pointer import build_pointer  # noqa: E402


class DatasetPromotionError(ValueError):
    """Raised when collection evidence cannot authorize a release."""


def assert_promotable_runs(
    session: Session, *, source_ids: set[str], run_ids: list[UUID]
) -> dict[str, str]:
    if len(run_ids) != len(set(run_ids)):
        raise DatasetPromotionError("collection run IDs must be unique")
    selected = list(
        session.scalars(select(CollectionRun).where(CollectionRun.run_id.in_(run_ids)))
    )
    if len(selected) != len(run_ids):
        raise DatasetPromotionError("one or more collection runs were not found")
    by_source = {run.source_id: run for run in selected}
    if set(by_source) != source_ids or len(by_source) != len(selected):
        raise DatasetPromotionError(
            "exactly one collection run is required for every included source"
        )
    evidence: dict[str, str] = {}
    for source_id in sorted(source_ids):
        run = by_source[source_id]
        latest = session.scalar(
            select(CollectionRun)
            .where(
                CollectionRun.source_id == source_id,
                CollectionRun.run_type == "collection",
            )
            .order_by(CollectionRun.started_at.desc(), CollectionRun.run_id.desc())
            .limit(1)
        )
        if latest is None or latest.run_id != run.run_id:
            raise DatasetPromotionError(
                f"{source_id}: supplied run is not the latest collection run"
            )
        if run.run_type != "collection" or run.status != "succeeded":
            raise DatasetPromotionError(
                f"{source_id}: latest collection status is {run.status}"
            )
        if not run.is_complete_snapshot:
            raise DatasetPromotionError(
                f"{source_id}: latest collection is not a complete source snapshot"
            )
        if run.finished_at is None or any(
            getattr(run, field) != 0
            for field in ("invalid_count", "rejected_count", "failed_count")
        ):
            raise DatasetPromotionError(
                f"{source_id}: latest collection contains validation failures"
            )
        evidence[source_id] = str(run.run_id)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--collection-run-id", action="append", required=True)
    parser.add_argument("--source-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--previous-dataset-version")
    parser.add_argument("--manifest-url", required=True)
    try:
        args = parser.parse_args()
        run_ids = [UUID(value) for value in args.collection_run_id]
        contract = load_source_contract(args.source_contract)
        source_ids = {item["source_id"] for item in contract["included_sources"]}
        engine = create_db_engine(args.database_url, sql_echo=False)
        try:
            with Session(engine) as session:
                evidence = assert_promotable_runs(
                    session, source_ids=source_ids, run_ids=run_ids
                )
            records = load_records(args.database_url, contract, limit=None)
        finally:
            engine.dispose()
        dataset_path, manifest_path, manifest = write_release(
            records=records,
            contract=contract,
            contract_path=args.source_contract,
            output_dir=args.output_dir,
            dataset_version=args.dataset_version,
            generated_at=args.generated_at,
            git_sha=args.git_sha,
            previous_dataset_version=args.previous_dataset_version,
        )
        verify_release(manifest_path, contract_path=args.source_contract)
        pointer = build_pointer(
            manifest_path=manifest_path, manifest_url=args.manifest_url
        )
        pointer_path = args.output_dir / "public-dataset-pointer.json"
        pointer_path.write_text(
            json.dumps(pointer, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "W6_P4_DATASET_PROMOTION_READY",
                    "dataset_path": str(dataset_path),
                    "manifest_path": str(manifest_path),
                    "pointer_path": str(pointer_path),
                    "row_count": manifest["artifact"]["row_count"],
                    "collection_runs": evidence,
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError, PublicDatasetError) as exc:
        print(f"W6_P4_DATASET_PROMOTION_BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
