import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment"
    / "postgres"
    / "verify_snapshot.py"
)
SPEC = importlib.util.spec_from_file_location(
    "verify_acceptance_snapshot", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_snapshot(snapshot_dir: Path, *, blocker: int = 0) -> dict:
    snapshot_dir.mkdir()
    dump_path = snapshot_dir / "acceptance-post-admission.dump"
    dump_path.write_bytes(b"synthetic custom dump")
    dump_hash = MODULE.sha256_file(dump_path)
    scan = {key: 0 for key in MODULE.BLOCKING_SCAN_KEYS}
    scan["source_url_public_navigation_token_count"] = 2
    scan["known_secret_match_count"] = blocker
    manifest = {
        "schema_version": "1.0.0",
        "snapshot_version": "acceptance-20260819-abcdef0",
        "repository": {"git_sha": "a" * 40},
        "database": {
            "alembic_revision": "20260810_0006",
            "tables": list(MODULE.ALLOWLIST_TABLES),
            "row_counts": {"policies": 3273, "collection_runs": 61},
            "stable_identity_counts": {
                "source-a/1": 1,
                "source-b/2": 1,
                "source-c/3": 1,
            },
            "sensitive_data_scan": scan,
        },
        "dump": {
            "filename": dump_path.name,
            "bytes": dump_path.stat().st_size,
            "sha256": dump_hash,
            "format": "custom",
            "toc_acl_entry_count": 0,
            "schema_owner_acl_statement_count": 0,
        },
    }
    manifest["manifest_sha256"] = MODULE.canonical_manifest_hash(manifest)
    (snapshot_dir / "acceptance-snapshot.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def test_verify_snapshot_accepts_complete_external_contract(tmp_path, monkeypatch):
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    snapshot_dir = tmp_path / "snapshot"
    manifest = write_snapshot(snapshot_dir)
    monkeypatch.setattr(
        MODULE,
        "verify_repository_lineage",
        lambda _root, _sha: "b" * 40,
    )

    result = MODULE.verify_snapshot(
        snapshot_dir,
        repository_root=repository_root,
    )

    assert result["status"] == "DEP2_SNAPSHOT_VERIFIED"
    assert result["dump_sha256"] == manifest["dump"]["sha256"]
    assert result["policy_count"] == 3273


def test_verify_snapshot_rejects_dump_hash_mismatch(tmp_path, monkeypatch):
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    snapshot_dir = tmp_path / "snapshot"
    write_snapshot(snapshot_dir)
    (snapshot_dir / "acceptance-post-admission.dump").write_bytes(b"changed")
    monkeypatch.setattr(
        MODULE,
        "verify_repository_lineage",
        lambda _root, _sha: "b" * 40,
    )

    with pytest.raises(MODULE.VerificationError, match="size mismatch"):
        MODULE.verify_snapshot(snapshot_dir, repository_root=repository_root)


def test_verify_snapshot_rejects_sensitive_scan_blocker(tmp_path, monkeypatch):
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    snapshot_dir = tmp_path / "snapshot"
    write_snapshot(snapshot_dir, blocker=1)
    monkeypatch.setattr(
        MODULE,
        "verify_repository_lineage",
        lambda _root, _sha: "b" * 40,
    )

    with pytest.raises(MODULE.VerificationError, match="sensitive data scan"):
        MODULE.verify_snapshot(snapshot_dir, repository_root=repository_root)


def test_verify_snapshot_rejects_workspace_child(tmp_path):
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    snapshot_dir = repository_root / "snapshot"
    snapshot_dir.mkdir()

    with pytest.raises(MODULE.VerificationError, match="outside the workspace"):
        MODULE.verify_snapshot(snapshot_dir, repository_root=repository_root)


def test_verify_snapshot_rejects_manifest_tampering(tmp_path, monkeypatch):
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    snapshot_dir = tmp_path / "snapshot"
    write_snapshot(snapshot_dir)
    manifest_path = snapshot_dir / "acceptance-snapshot.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["database"]["row_counts"]["policies"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(
        MODULE,
        "verify_repository_lineage",
        lambda _root, _sha: "b" * 40,
    )

    with pytest.raises(MODULE.VerificationError, match="canonical SHA-256"):
        MODULE.verify_snapshot(snapshot_dir, repository_root=repository_root)


def test_repository_lineage_rejects_unrelated_snapshot(tmp_path, monkeypatch):
    class Result:
        def __init__(self, returncode, stdout=""):
            self.returncode = returncode
            self.stdout = stdout

    responses = iter((Result(0, "b" * 40 + "\n"), Result(1)))
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *args, **kwargs: next(responses))

    with pytest.raises(MODULE.VerificationError, match="not an ancestor"):
        MODULE.verify_repository_lineage(tmp_path, "a" * 40)

