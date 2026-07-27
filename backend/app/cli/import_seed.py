import sys
import os
import argparse
from pathlib import Path

# Add backend directory to sys.path if needed
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, Base, engine
from app.services.seed_importer import import_seed_data
from app.core.logging import logger

def main():
    parser = argparse.ArgumentParser(description="Import canonical JSON Seed data into the database.")
    default_seed = backend_dir.parent / "data" / "seeds" / "initial_programs.json"
    parser.add_argument(
        "--file",
        type=str,
        default=str(default_seed),
        help="Path to initial_programs.json seed file"
    )
    args = parser.parse_args()

    seed_path = Path(args.file)
    logger.info(f"Starting seed ingestion from: {seed_path}")

    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        total, inserted, updated = import_seed_data(db, seed_path)
        logger.info(f"Seed Ingestion Completed Successfully. Total: {total}, Inserted: {inserted}, Updated: {updated}")
        print(f"[SUCCESS] Seed Ingestion Completed. Total: {total}, Inserted: {inserted}, Updated: {updated}")
    except Exception as e:
        logger.error(f"Seed Ingestion Failed: {str(e)}", exc_info=True)
        print(f"[ERROR] Seed Ingestion Failed: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
