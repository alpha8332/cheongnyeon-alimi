import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path if needed
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.logging import logger
from app.core.database import SessionLocal
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

    db = SessionLocal()
    try:
        result = import_seed_data(db, seed_path, dry_run=args.dry_run)
        summary = (
            f"Total: {result.total}, Validated: {result.validated}, "
            f"Inserted: {result.inserted}, "
            f"Updated: {result.updated}, Unchanged: {result.unchanged}, "
            f"Skipped: {result.skipped}, Rejected: {result.rejected}, "
            f"Failed: {result.failed}"
        )
        has_errors = bool(
            result.skipped or result.rejected or result.failed
        )
        status = "failed" if has_errors else "completed"
        logger.info("Seed ingestion %s. %s", status, summary)
        label = "ERROR" if has_errors else "SUCCESS"
        action = "dry run" if result.dry_run else "ingestion"
        print(f"[{label}] Seed {action} {status}. {summary}")
        for issue in result.issues:
            print(
                "[ISSUE] "
                f"index={issue.index} source_id={issue.source_id} "
                f"external_id={issue.external_id} code={issue.code} "
                f"path={issue.path} "
                f"error_type={issue.error_type}"
            )
        if has_errors:
            sys.exit(1)
    except Exception as exc:
        error_type = type(exc).__name__
        logger.error("Seed ingestion failed. error_type=%s", error_type)
        print(f"[ERROR] Seed ingestion failed. error_type={error_type}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
