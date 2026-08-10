import argparse
import sys
from pathlib import Path

# Add the repository and backend roots for direct module execution.
backend_dir = Path(__file__).resolve().parent.parent.parent
project_root = backend_dir.parent
for import_root in (project_root, backend_dir):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.logging import logger
from app.core.database import SessionLocal
from app.services.collection_runs import (
    CollectionRunCounts,
    CollectionRunWriter,
)
from app.services.seed_importer import import_seed_data


def main():
    parser = argparse.ArgumentParser(
        description="Import canonical JSON Seed data into the database."
    )
    default_seed = backend_dir.parent / "data" / "seeds" / "initial_programs.json"
    parser.add_argument(
        "--file",
        type=str,
        default=str(default_seed),
        help="Path to initial_programs.json seed file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and project database changes, then roll them back",
    )
    args = parser.parse_args()

    seed_path = Path(args.file)
    logger.info(f"Starting seed ingestion from: {seed_path}")

    run_writer = None
    run_id = None
    if not args.dry_run:
        run_writer = CollectionRunWriter(SessionLocal)
        try:
            run_id = run_writer.start(
                source_id=None,
                run_type="seed_import",
                trigger_type="cli",
            )
        except Exception as exc:
            error_type = type(exc).__name__
            logger.error(
                "Seed ingestion history start failed. error_type=%s",
                error_type,
            )
            print(
                "[ERROR] Seed ingestion failed. "
                f"error_type={error_type}"
            )
            sys.exit(1)

    db = SessionLocal()
    try:
        result = import_seed_data(db, seed_path, dry_run=args.dry_run)
        summary = (
            f"Total: {result.total}, Validated: {result.validated}, "
            f"Inserted: {result.inserted}, "
            f"Updated: {result.updated}, Unchanged: {result.unchanged}, "
            f"Duplicate: {result.duplicate}, "
            f"Skipped: {result.skipped}, Rejected: {result.rejected}, "
            f"Failed: {result.failed}, Run ID: {run_id}"
        )
        has_errors = bool(
            result.skipped or result.rejected or result.failed
        )
        status = "failed" if has_errors else "completed"
        if run_writer is not None and run_id is not None:
            run_writer.finish(
                run_id,
                status="failed" if has_errors else "succeeded",
                counts=_seed_run_counts(result),
            )
        logger.info("Seed ingestion %s. %s", status, summary)
        label = "ERROR" if has_errors else "SUCCESS"
        action = "dry run" if result.dry_run else "ingestion"
        print(f"[{label}] Seed {action} {status}. {summary}")
        for issue in result.issues:
            print(
                "[ISSUE] "
                f"index={issue.index} source_id={issue.source_id} "
                f"external_id={issue.external_id} code={issue.code} "
                f"stage={issue.stage} "
                f"path={issue.path} "
                f"error_type={issue.error_type}"
            )
        if has_errors:
            sys.exit(1)
    except Exception as exc:
        error_type = type(exc).__name__
        _finish_failed_run(run_writer, run_id, error_type)
        logger.error("Seed ingestion failed. error_type=%s", error_type)
        print(f"[ERROR] Seed ingestion failed. error_type={error_type}")
        sys.exit(1)
    finally:
        db.close()


def _seed_run_counts(result):
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


def _finish_failed_run(run_writer, run_id, error_type):
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
    main()
