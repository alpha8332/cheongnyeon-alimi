import argparse
import sys
from pathlib import Path


backend_dir = Path(__file__).resolve().parent.parent.parent
project_root = backend_dir.parent
for import_root in (project_root, backend_dir):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import SessionLocal
from app.services.region_reference_importer import import_region_reference


def main() -> None:
    default_root = project_root / "data" / "seeds"
    parser = argparse.ArgumentParser(
        description="Import locked administrative-region Seed data."
    )
    parser.add_argument(
        "--regions",
        default=str(default_root / "administrative_regions.json"),
    )
    parser.add_argument(
        "--aliases",
        default=str(default_root / "administrative_region_aliases.json"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = import_region_reference(
            db,
            Path(args.regions),
            Path(args.aliases),
            dry_run=args.dry_run,
        )
        action = "dry run" if result.dry_run else "import"
        print(
            f"[SUCCESS] Region reference {action} completed. "
            f"scheme={result.scheme} "
            f"regions_inserted={result.inserted_regions} "
            f"regions_unchanged={result.unchanged_regions} "
            f"aliases_inserted={result.inserted_aliases} "
            f"aliases_unchanged={result.unchanged_aliases}"
        )
    except Exception as exc:
        print(
            "[ERROR] Region reference import failed. "
            f"error_type={type(exc).__name__}"
        )
        raise SystemExit(1) from None
    finally:
        db.close()


if __name__ == "__main__":
    main()
