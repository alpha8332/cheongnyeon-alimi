from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ALLOWLIST_TABLES = (
    "administrative_region_aliases",
    "administrative_regions",
    "alembic_version",
    "collection_runs",
    "policies",
    "policy_region_rules",
    "policy_search_documents",
)
BLOCKING_SCAN_KEYS = (
    "forbidden_column_count",
    "known_secret_match_count",
    "disallowed_contact_kind_count",
    "email_contact_count",
    "local_path_provenance_count",
    "collection_error_sensitive_count",
    "source_url_high_risk_query_count",
    "source_url_unsafe_token_count",
)
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_manifest_hash(value: dict[str, Any]) -> str:
    selected = dict(value)
    selected.pop("manifest_sha256", None)
    payload = json.dumps(
        selected,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationError(f"{name} must be an object")
    return value


def ensure_external_path(path: Path, repository_root: Path) -> None:
    try:
        path.relative_to(repository_root)
    except ValueError:
        return
    raise VerificationError("snapshot directory must be outside the workspace")


def verify_repository_lineage(repository_root: Path, snapshot_sha: str) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", snapshot_sha, head],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if ancestor.returncode != 0:
        raise VerificationError(
            "snapshot Git SHA is not an ancestor of the current checkout"
        )
    return head


def verify_snapshot(
    snapshot_dir: Path,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    snapshot_dir = snapshot_dir.resolve()
    repository_root = repository_root.resolve()
    ensure_external_path(snapshot_dir, repository_root)
    if not snapshot_dir.is_dir():
        raise VerificationError("snapshot directory does not exist")

    manifest_path = snapshot_dir / "acceptance-snapshot.manifest.json"
    if not manifest_path.is_file():
        raise VerificationError("snapshot manifest does not exist")
    manifest = require_mapping(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        "manifest",
    )

    if manifest.get("schema_version") != "1.0.0":
        raise VerificationError("unsupported snapshot manifest schema")
    embedded_manifest_hash = manifest.get("manifest_sha256")
    if not isinstance(embedded_manifest_hash, str) or not SHA256_PATTERN.fullmatch(
        embedded_manifest_hash
    ):
        raise VerificationError("manifest SHA-256 is malformed")
    actual_manifest_hash = canonical_manifest_hash(manifest)
    if actual_manifest_hash != embedded_manifest_hash:
        raise VerificationError("manifest canonical SHA-256 mismatch")

    repository = require_mapping(manifest.get("repository"), "repository")
    snapshot_git_sha = repository.get("git_sha")
    if not isinstance(snapshot_git_sha, str) or not GIT_SHA_PATTERN.fullmatch(
        snapshot_git_sha
    ):
        raise VerificationError("snapshot Git SHA is malformed")
    current_git_sha = verify_repository_lineage(repository_root, snapshot_git_sha)

    database = require_mapping(manifest.get("database"), "database")
    if tuple(database.get("tables", ())) != ALLOWLIST_TABLES:
        raise VerificationError("snapshot table allowlist mismatch")
    if database.get("alembic_revision") != "20260810_0006":
        raise VerificationError("snapshot Alembic revision mismatch")
    row_counts = require_mapping(database.get("row_counts"), "database.row_counts")
    if row_counts.get("policies") != 3273:
        raise VerificationError("snapshot Policy count mismatch")
    if row_counts.get("collection_runs") != 61:
        raise VerificationError("snapshot CollectionRun count mismatch")
    stable_counts = require_mapping(
        database.get("stable_identity_counts"),
        "database.stable_identity_counts",
    )
    if len(stable_counts) != 3 or any(value != 1 for value in stable_counts.values()):
        raise VerificationError("snapshot stable identity counts mismatch")
    scan = require_mapping(
        database.get("sensitive_data_scan"),
        "database.sensitive_data_scan",
    )
    blockers = {
        key: scan.get(key)
        for key in BLOCKING_SCAN_KEYS
        if scan.get(key) != 0
    }
    if blockers:
        raise VerificationError(f"snapshot sensitive data scan failed: {blockers}")

    dump = require_mapping(manifest.get("dump"), "dump")
    dump_filename = dump.get("filename")
    if (
        not isinstance(dump_filename, str)
        or not dump_filename
        or Path(dump_filename).name != dump_filename
    ):
        raise VerificationError("dump filename must be a basename")
    expected_dump_hash = dump.get("sha256")
    if not isinstance(expected_dump_hash, str) or not SHA256_PATTERN.fullmatch(
        expected_dump_hash
    ):
        raise VerificationError("dump SHA-256 is malformed")
    dump_path = snapshot_dir / dump_filename
    if not dump_path.is_file():
        raise VerificationError("snapshot dump does not exist")
    if dump_path.stat().st_size != dump.get("bytes"):
        raise VerificationError("snapshot dump size mismatch")
    actual_dump_hash = sha256_file(dump_path)
    if actual_dump_hash != expected_dump_hash:
        raise VerificationError("snapshot dump SHA-256 mismatch")
    if dump.get("format") != "custom":
        raise VerificationError("snapshot dump format is not custom")
    if dump.get("toc_acl_entry_count") != 0:
        raise VerificationError("snapshot dump contains ACL entries")
    if dump.get("schema_owner_acl_statement_count") != 0:
        raise VerificationError("snapshot schema contains owner or ACL statements")

    return {
        "status": "DEP2_SNAPSHOT_VERIFIED",
        "snapshot_version": manifest.get("snapshot_version"),
        "snapshot_git_sha": snapshot_git_sha,
        "current_git_sha": current_git_sha,
        "manifest_path": str(manifest_path),
        "manifest_sha256": actual_manifest_hash,
        "manifest_file_sha256": sha256_file(manifest_path),
        "dump_path": str(dump_path),
        "dump_filename": dump_filename,
        "dump_bytes": dump_path.stat().st_size,
        "dump_sha256": actual_dump_hash,
        "policy_count": row_counts["policies"],
        "collection_run_count": row_counts["collection_runs"],
        "alembic_revision": database["alembic_revision"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail-closed verification for an external Acceptance snapshot."
    )
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = verify_snapshot(
            args.snapshot_dir,
            repository_root=args.repository_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (
        VerificationError,
        OSError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"DEP2_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
