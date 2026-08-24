"""Create and verify the mutable pointer to an immutable public dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from collectors.validation import JsonSchemaValidator  # noqa: E402


POINTER_SCHEMA = ROOT / "data/schema/public_policy_dataset_pointer.schema.json"


class DatasetPointerError(ValueError):
    """Raised when a dataset pointer is unsafe or invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pointer(pointer: dict[str, Any]) -> None:
    issues = JsonSchemaValidator(POINTER_SCHEMA).schema_issues(pointer)
    if issues:
        detail = ", ".join(f"{issue.path}:{issue.code}" for issue in issues)
        raise DatasetPointerError(f"pointer schema validation failed: {detail}")
    parsed = urlsplit(pointer["manifest_url"])
    if parsed.scheme != "https" or not parsed.netloc:
        raise DatasetPointerError("manifest URL must be an absolute HTTPS URL")
    immutable_tag = f"/download/dataset-{pointer['dataset_version']}/"
    if immutable_tag not in parsed.path:
        raise DatasetPointerError("manifest URL must reference its immutable dataset tag")


def build_pointer(
    *, manifest_path: Path, manifest_url: str, updated_at: str | None = None
) -> dict[str, Any]:
    from scripts.build_public_bootstrap_dataset import verify_release

    manifest = verify_release(manifest_path)
    dataset_version = manifest.get("dataset_version")
    if not isinstance(dataset_version, str):
        raise DatasetPointerError("manifest dataset_version is missing")
    pointer = {
        "pointer_version": "1.0.0",
        "dataset_version": dataset_version,
        "manifest_url": manifest_url,
        "manifest_sha256": sha256_file(manifest_path),
        "updated_at": updated_at
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    validate_pointer(pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manifest-url")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--updated-at")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            validate_pointer(json.loads(args.verify.read_text(encoding="utf-8")))
            print("W6_P4_DATASET_POINTER_VERIFIED")
            return 0
        if not all((args.manifest, args.manifest_url, args.output)):
            raise DatasetPointerError(
                "build mode requires --manifest, --manifest-url and --output"
            )
        pointer = build_pointer(
            manifest_path=args.manifest,
            manifest_url=args.manifest_url,
            updated_at=args.updated_at,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(pointer, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("W6_P4_DATASET_POINTER_CREATED")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"W6_P4_DATASET_POINTER_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
