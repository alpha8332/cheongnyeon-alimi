import json
from pathlib import Path

import pytest

from app.cli.import_public_dataset import (
    PublicDatasetImportError,
    _load_manifest,
)


def _write_manifest(tmp_path: Path, *, filename: str = "dataset.json") -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "public-bootstrap-20260824-135a082",
                "artifact": {"filename": filename, "row_count": 2},
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_load_manifest_resolves_only_a_sibling_artifact(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text("[]", encoding="utf-8")

    version, resolved_dataset, row_count = _load_manifest(manifest_path)

    assert version == "public-bootstrap-20260824-135a082"
    assert resolved_dataset == dataset_path
    assert row_count == 2


@pytest.mark.parametrize("filename", ["../dataset.json", "folder/dataset.json"])
def test_load_manifest_rejects_artifact_path_traversal(tmp_path, filename):
    manifest_path = _write_manifest(tmp_path, filename=filename)

    with pytest.raises(PublicDatasetImportError, match="filename is unsafe"):
        _load_manifest(manifest_path)


def test_load_manifest_requires_positive_non_boolean_row_count(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "public-bootstrap-20260824-135a082",
                "artifact": {"filename": "dataset.json", "row_count": True},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PublicDatasetImportError, match="row_count is invalid"):
        _load_manifest(manifest_path)
