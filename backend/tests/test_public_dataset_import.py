import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models.policy import Policy
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)
from app.repositories.policy import PolicyRepository
from app.repositories.policy_lifecycle import mark_missing_policies_inactive
from app.repositories.policy_search import PolicySearchRepository
from app.schemas.recommendation import RecommendationRequest
from app.services.policy_search_parser import parse_search_query
from app.services.public_dataset_installer import (
    PublicDatasetInstallationError,
    install_public_dataset,
    verify_public_dataset,
)
from app.services.recommendation import recommend_policies_service
from app.services.seed_importer import import_programs


SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "seeds"
    / "initial_programs.json"
)


def _write_manifest(tmp_path: Path, *, filename: str = "dataset.json") -> Path:
    artifact_bytes = b"[]"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "public-bootstrap-20260824-135a082",
                "artifact": {
                    "filename": filename,
                    "row_count": 2,
                    "bytes": len(artifact_bytes),
                    "sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


@pytest.mark.parametrize("filename", ["../dataset.json", "folder/dataset.json"])
def test_verifier_rejects_artifact_path_traversal(tmp_path, filename):
    manifest_path = _write_manifest(tmp_path, filename=filename)

    with pytest.raises(
        PublicDatasetInstallationError,
        match="filename is unsafe",
    ):
        verify_public_dataset(manifest_path)


def test_verifier_requires_positive_non_boolean_row_count(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "public-bootstrap-20260824-135a082",
                "artifact": {
                    "filename": "dataset.json",
                    "row_count": True,
                    "bytes": 2,
                    "sha256": hashlib.sha256(b"[]").hexdigest(),
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PublicDatasetInstallationError,
        match="row_count is invalid",
    ):
        verify_public_dataset(manifest_path)


def test_public_reads_fail_closed_without_an_active_dataset(db):
    assert import_programs(db, _records()[:1]).inserted == 1
    policy = db.scalar(select(Policy))
    assert policy is not None

    repository = PolicyRepository(db)
    assert repository.list(
        quality_statuses=("valid", "partial"),
        page=1,
        limit=100,
    ).total == 0
    assert repository.get_by_id(
        policy.id,
        quality_statuses=("valid", "partial"),
    ) is None


def _records() -> list[dict[str, object]]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def _write_verified_release(
    tmp_path: Path,
    records: list[dict[str, object]],
    *,
    version: str = "public-bootstrap-20260824-135a082",
    suffix: str = "",
) -> Path:
    artifact_path = tmp_path / f"dataset{suffix}.json"
    artifact_bytes = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    artifact_path.write_bytes(artifact_bytes)
    manifest_path = tmp_path / f"manifest{suffix}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": version,
                "artifact": {
                    "filename": artifact_path.name,
                    "row_count": len(records),
                    "bytes": len(artifact_bytes),
                    "sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_active_projection_hides_preserved_local_and_manual_rows(db, tmp_path):
    records = _records()
    assert import_programs(db, records).inserted == 4
    original_ids = {
        (policy.source_id, policy.external_id): policy.id
        for policy in db.scalars(select(Policy)).all()
    }
    db.commit()

    published_records = records[1:3]
    manifest_path = _write_verified_release(tmp_path, published_records)
    installed = install_public_dataset(
        db,
        verify_public_dataset(manifest_path),
    )

    repository = PolicyRepository(db)
    public_page = repository.list(
        quality_statuses=("valid", "partial"),
        page=1,
        limit=100,
    )
    assert db.scalar(select(func.count(Policy.id))) == 4
    assert public_page.total == 2
    assert {
        (policy.source_id, policy.external_id) for policy in public_page.items
    } == {
        (record["source_id"], record["external_id"])
        for record in published_records
    }
    assert db.scalar(select(func.count(PublicDatasetMembership.policy_id))) == 2
    assert db.scalar(
        select(PublicDatasetInstallation.status)
    ) == "active"
    assert installed.expected_policy_count == 2
    assert original_ids == {
        (policy.source_id, policy.external_id): policy.id
        for policy in db.scalars(select(Policy)).all()
    }
    db.commit()

    manual = dict(records[2])
    manual["external_id"] = "MANUAL-UNPROMOTED"
    manual["title"] = "미승격전용정책고유어"
    assert import_programs(db, [manual]).inserted == 1
    assert repository.list(
        quality_statuses=("valid", "partial"),
        page=1,
        limit=100,
    ).total == 2
    assert db.scalar(select(func.count(Policy.id))) == 5
    manual_policy = db.scalar(
        select(Policy).where(Policy.external_id == "MANUAL-UNPROMOTED")
    )
    assert manual_policy is not None
    assert repository.get_by_id(
        manual_policy.id,
        quality_statuses=("valid", "partial"),
    ) is None
    interpreted = parse_search_query(q="미승격전용정책고유어", db=db)
    assert PolicySearchRepository(db).search_policies(
        interpreted,
        include_partial=True,
    )[1] == 0
    recommendations = recommend_policies_service(
        db,
        RecommendationRequest(include_partial=True, limit=50),
    )
    assert manual_policy.id not in {item.id for item in recommendations.items}

    published = published_records[0]
    protected_change = dict(published)
    protected_change["title"] = "수동수집이덮어쓰면안되는제목"
    db.commit()
    protected_result = import_programs(db, [protected_change])
    stored_title = db.scalar(
        select(Policy.title).where(
            Policy.source_id == published["source_id"],
            Policy.external_id == published["external_id"],
        )
    )
    assert protected_result.unchanged == 1
    assert protected_result.updated == 0
    assert stored_title == published["title"]
    db.commit()
    mark_missing_policies_inactive(
        db,
        source_id=str(published["source_id"]),
        seen_external_ids=set(),
        inactive_at=datetime.now(timezone.utc),
    )
    db.commit()
    assert db.scalar(
        select(Policy.inactive_at).where(
            Policy.source_id == published["source_id"],
            Policy.external_id == published["external_id"],
        )
    ) is None


def test_failed_replacement_keeps_previous_active_projection(db, tmp_path):
    records = _records()[:2]
    first_manifest = _write_verified_release(tmp_path, records, suffix="-first")
    first = install_public_dataset(db, verify_public_dataset(first_manifest))

    changed = [dict(record) for record in records]
    changed[0]["title"] = "활성화되면 안 되는 변경"
    conflicting_manifest = _write_verified_release(
        tmp_path,
        changed,
        suffix="-conflict",
    )
    with pytest.raises(
        PublicDatasetInstallationError,
        match="different content",
    ):
        install_public_dataset(db, verify_public_dataset(conflicting_manifest))

    active = db.scalar(
        select(PublicDatasetInstallation).where(
            PublicDatasetInstallation.status == "active"
        )
    )
    stored_title = db.scalar(
        select(Policy.title).where(
            Policy.source_id == records[0]["source_id"],
            Policy.external_id == records[0]["external_id"],
        )
    )
    memberships = db.execute(
        select(
            PublicDatasetMembership.source_id,
            PublicDatasetMembership.external_id,
        )
    ).all()

    assert active is not None
    assert active.dataset_version == first.dataset_version
    assert stored_title == records[0]["title"]
    assert len(memberships) == 2
    db.commit()
    assert first.identity_sha256 == install_public_dataset(
        db,
        verify_public_dataset(first_manifest),
    ).identity_sha256


def test_verifier_rejects_artifact_hash_mismatch_before_database_write(
    db,
    tmp_path,
):
    manifest_path = _write_verified_release(tmp_path, _records()[:1])
    (tmp_path / "dataset.json").write_text("[]", encoding="utf-8")

    with pytest.raises(PublicDatasetInstallationError, match="byte count mismatch"):
        verify_public_dataset(manifest_path)

    assert db.scalar(select(func.count(Policy.id))) == 0
