"""Import a previously verified public bootstrap dataset into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.services.collection_runs import CollectionRunCounts, CollectionRunWriter
from app.services.public_dataset_installer import (
    install_public_dataset,
    verify_public_dataset,
)

def _counts(result) -> CollectionRunCounts:
    return CollectionRunCounts(
        requested_count=result.total,
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


def import_verified_public_dataset(manifest_path: Path) -> dict[str, object]:
    verified = verify_public_dataset(manifest_path)
    dataset_version = verified.dataset_version
    writer = CollectionRunWriter(SessionLocal)
    run_id = writer.start(
        source_id=f"public-dataset:{dataset_version}",
        run_type="seed_import",
        trigger_type="cli",
    )

    db = SessionLocal()
    try:
        installation = install_public_dataset(db, verified)
        result = installation.import_result
        writer.finish(
            run_id,
            status="succeeded",
            counts=_counts(result),
            error_type=None,
        )
        return {
            "status": "W6_P3_PUBLIC_DATASET_IMPORTED",
            "dataset_version": dataset_version,
            "row_count": result.total,
            "inserted": result.inserted,
            "updated": result.updated,
            "unchanged": result.unchanged,
            "identity_sha256": installation.identity_sha256,
            "run_id": str(run_id),
        }
    except Exception as exc:
        try:
            writer.finish(
                run_id,
                status="failed",
                counts=CollectionRunCounts(failed_count=1),
                error_type=type(exc).__name__,
            )
        except Exception:
            pass
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = import_verified_public_dataset(args.manifest.resolve())
    except (OSError, ValueError) as exc:
        print(
            f"W6_P3_PUBLIC_DATASET_IMPORT_FAILED: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
