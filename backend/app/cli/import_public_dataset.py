"""Import a previously verified public bootstrap dataset into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

from app.core.database import SessionLocal
from app.services.collection_runs import CollectionRunCounts, CollectionRunWriter
from app.services.seed_importer import import_seed_data


class PublicDatasetImportError(ValueError):
    """Raised when the verified manifest cannot identify a safe artifact."""


def _load_manifest(path: Path) -> tuple[str, Path, int]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise PublicDatasetImportError("manifest must be an object")

    dataset_version = value.get("dataset_version")
    artifact = value.get("artifact")
    if not isinstance(dataset_version, str) or not dataset_version:
        raise PublicDatasetImportError("manifest dataset_version is missing")
    if not isinstance(artifact, Mapping):
        raise PublicDatasetImportError("manifest artifact is missing")

    filename = artifact.get("filename")
    row_count = artifact.get("row_count")
    if (
        not isinstance(filename, str)
        or not filename
        or Path(filename).name != filename
    ):
        raise PublicDatasetImportError("manifest artifact filename is unsafe")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 1:
        raise PublicDatasetImportError("manifest artifact row_count is invalid")

    dataset_path = path.parent / filename
    if not dataset_path.is_file():
        raise PublicDatasetImportError("verified dataset artifact is missing")
    return dataset_version, dataset_path, row_count


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
    dataset_version, dataset_path, expected_rows = _load_manifest(manifest_path)
    writer = CollectionRunWriter(SessionLocal)
    run_id = writer.start(
        source_id=f"public-dataset:{dataset_version}",
        run_type="seed_import",
        trigger_type="cli",
    )

    db = SessionLocal()
    try:
        result = import_seed_data(db, dataset_path)
        has_errors = bool(result.skipped or result.rejected or result.failed)
        if result.total != expected_rows:
            has_errors = True
        writer.finish(
            run_id,
            status="failed" if has_errors else "succeeded",
            counts=_counts(result),
            error_type=("PublicDatasetImportMismatch" if has_errors else None),
        )
        if has_errors:
            raise PublicDatasetImportError(
                "dataset import counts did not match the verified manifest"
            )
        return {
            "status": "W6_P3_PUBLIC_DATASET_IMPORTED",
            "dataset_version": dataset_version,
            "row_count": result.total,
            "inserted": result.inserted,
            "updated": result.updated,
            "unchanged": result.unchanged,
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
