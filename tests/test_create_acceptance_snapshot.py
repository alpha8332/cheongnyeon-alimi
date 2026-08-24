import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment"
    / "postgres"
    / "create_snapshot.py"
)
SPEC = importlib.util.spec_from_file_location(
    "create_acceptance_snapshot", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_split_pgpass_line_supports_escaped_delimiters():
    assert MODULE.split_pgpass_line(
        r"127.0.0.1:5432:database:role:pass\:word"
    ) == ["127.0.0.1", "5432", "database", "role", "pass:word"]


def test_resolve_pgpass_entry_never_returns_password(tmp_path):
    pgpass = tmp_path / "pgpass.conf"
    pgpass.write_text(
        "127.0.0.1:5432:database:acceptance_role:private-value\n",
        encoding="utf-8",
    )

    entry = MODULE.resolve_pgpass_entry(
        pgpass,
        host="127.0.0.1",
        port=5432,
        database="database",
    )

    assert entry.user == "acceptance_role"
    assert "private-value" not in repr(entry)


def test_classify_source_urls_separates_public_navigation_token():
    result = MODULE.classify_source_urls(
        [
            (
                "source",
                "external",
                "https://example.go.kr/board/list.do?token=1234567890123",
            )
        ],
        secret_candidates=("known-secret-value",),
    )

    assert result == {
        "source_url_high_risk_query_count": 0,
        "source_url_public_navigation_token_count": 1,
        "source_url_unsafe_token_count": 0,
    }


@pytest.mark.parametrize(
    "url",
    [
        "https://example.go.kr/open?serviceKey=secret",
        "https://example.go.kr/open?api_key=secret",
        "https://example.go.kr/open?password=secret",
    ],
)
def test_classify_source_urls_blocks_high_risk_query_keys(url):
    result = MODULE.classify_source_urls(
        [("source", "external", url)], secret_candidates=()
    )

    assert result["source_url_high_risk_query_count"] == 1


def test_classify_source_urls_blocks_non_government_token():
    result = MODULE.classify_source_urls(
        [
            (
                "source",
                "external",
                "https://example.com/open?token=1234567890123",
            )
        ],
        secret_candidates=(),
    )

    assert result["source_url_unsafe_token_count"] == 1


def test_classify_source_urls_blocks_token_matching_known_secret():
    secret = "1234567890123"
    result = MODULE.classify_source_urls(
        [
            (
                "source",
                "external",
                f"https://example.go.kr/open?token={secret}",
            )
        ],
        secret_candidates=(secret,),
    )

    assert result["source_url_public_navigation_token_count"] == 0
    assert result["source_url_unsafe_token_count"] == 1


def test_canonical_manifest_hash_ignores_embedded_hash():
    original = {"schema_version": "1.0.0", "value": 1}
    with_hash = {
        **original,
        "manifest_sha256": "this-field-is-excluded",
    }

    assert MODULE.canonical_manifest_hash(original) == (
        MODULE.canonical_manifest_hash(with_hash)
    )


def test_ensure_outside_workspace_rejects_child_path(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(MODULE.SnapshotError):
        MODULE.ensure_outside_workspace(
            workspace / "snapshot",
            workspace,
        )


def test_write_manifest_refuses_overwrite(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("existing", encoding="utf-8")

    with pytest.raises(MODULE.SnapshotError):
        MODULE.write_manifest(
            manifest_path,
            {"schema_version": "1.0.0"},
        )
