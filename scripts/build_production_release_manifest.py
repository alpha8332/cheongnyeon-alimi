"""Bind image digests, Git, migration, schema and dataset into one release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT, ROOT / "scripts"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from collectors.normalized import NormalizedProgram  # noqa: E402
from collectors.validation import JsonSchemaValidator  # noqa: E402
from build_public_dataset_pointer import sha256_file, validate_pointer  # noqa: E402


SCHEMA = ROOT / "data/schema/production_release_manifest.schema.json"
NORMALIZED_SCHEMA = ROOT / "data/schema/normalized_program.schema.json"
VERSIONS_DIR = ROOT / "backend/alembic/versions"


class ProductionManifestError(ValueError):
    """Raised when immutable release identities cannot be linked safely."""


def alembic_head(versions_dir: Path = VERSIONS_DIR) -> str:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        revision = re.search(r'^revision:\s*str\s*=\s*"([^"]+)"', text, re.MULTILINE)
        parent = re.search(
            r'^down_revision:[^=]*=\s*(?:"([^"]+)"|None)', text, re.MULTILINE
        )
        if revision:
            revisions.add(revision.group(1))
        if parent and parent.group(1):
            parents.add(parent.group(1))
    heads = revisions - parents
    if len(heads) != 1:
        raise ProductionManifestError(f"expected one Alembic head, found {sorted(heads)}")
    return next(iter(heads))


def build_manifest(
    *, release_version: str, git_sha: str, backend_name: str,
    backend_digest: str, frontend_name: str, frontend_digest: str,
    dataset_pointer_path: Path, generated_at: str | None = None,
) -> dict[str, Any]:
    pointer = json.loads(dataset_pointer_path.read_text(encoding="utf-8"))
    validate_pointer(pointer)
    manifest = {
        "manifest_version": "1.0.0",
        "release_version": release_version,
        "generated_at": generated_at
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "git_sha": git_sha,
        "alembic_revision": alembic_head(),
        "normalized_schema": {
            "version": NormalizedProgram.SCHEMA_VERSION,
            "sha256": sha256_file(NORMALIZED_SCHEMA),
        },
        "dataset": {
            "version": pointer["dataset_version"],
            "pointer_sha256": sha256_file(dataset_pointer_path),
            "manifest_sha256": pointer["manifest_sha256"],
            "manifest_url": pointer["manifest_url"],
        },
        "images": {
            "backend": {"name": backend_name, "digest": backend_digest},
            "frontend": {"name": frontend_name, "digest": frontend_digest},
        },
    }
    issues = JsonSchemaValidator(SCHEMA).schema_issues(manifest)
    if issues:
        detail = ", ".join(f"{issue.path}:{issue.code}" for issue in issues)
        raise ProductionManifestError(f"release manifest validation failed: {detail}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--backend-name", required=True)
    parser.add_argument("--backend-digest", required=True)
    parser.add_argument("--frontend-name", required=True)
    parser.add_argument("--frontend-digest", required=True)
    parser.add_argument("--dataset-pointer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generated-at")
    try:
        args = parser.parse_args()
        manifest = build_manifest(
            release_version=args.release_version,
            git_sha=args.git_sha,
            backend_name=args.backend_name,
            backend_digest=args.backend_digest,
            frontend_name=args.frontend_name,
            frontend_digest=args.frontend_digest,
            dataset_pointer_path=args.dataset_pointer,
            generated_at=args.generated_at,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("W6_P4_PRODUCTION_RELEASE_MANIFEST_CREATED")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"W6_P4_PRODUCTION_RELEASE_MANIFEST_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
