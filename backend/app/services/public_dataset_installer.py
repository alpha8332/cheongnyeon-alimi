from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)
from app.services.seed_importer import ImportResult, import_seed_data


class PublicDatasetInstallationError(ValueError):
    """Raised when a release cannot be verified and atomically activated."""


@dataclass(frozen=True)
class VerifiedPublicDataset:
    dataset_version: str
    manifest_path: Path
    dataset_path: Path
    manifest_sha256: str
    artifact_sha256: str
    expected_policy_count: int
    identities: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PublicDatasetInstallationResult:
    dataset_version: str
    expected_policy_count: int
    identity_sha256: str
    import_result: ImportResult


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PublicDatasetInstallationError(f"manifest {field} is invalid")
    return value


def verify_public_dataset(manifest_path: Path) -> VerifiedPublicDataset:
    """Verify release bytes, row count, and complete identity set before writes."""

    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as exc:
        raise PublicDatasetInstallationError("manifest is not valid JSON") from exc
    if not isinstance(manifest, Mapping):
        raise PublicDatasetInstallationError("manifest must be an object")

    dataset_version = manifest.get("dataset_version")
    artifact = manifest.get("artifact")
    if not isinstance(dataset_version, str) or re.fullmatch(
        r"public-bootstrap-[0-9]{8}-[0-9a-f]{7,40}",
        dataset_version,
    ) is None:
        raise PublicDatasetInstallationError("manifest dataset_version is invalid")
    if not isinstance(artifact, Mapping):
        raise PublicDatasetInstallationError("manifest artifact is missing")

    filename = artifact.get("filename")
    row_count = artifact.get("row_count")
    byte_count = artifact.get("bytes")
    artifact_sha256 = _require_sha256(
        artifact.get("sha256"),
        field="artifact sha256",
    )
    if (
        not isinstance(filename, str)
        or not filename
        or Path(filename).name != filename
    ):
        raise PublicDatasetInstallationError(
            "manifest artifact filename is unsafe"
        )
    if (
        not isinstance(row_count, int)
        or isinstance(row_count, bool)
        or row_count < 1
    ):
        raise PublicDatasetInstallationError(
            "manifest artifact row_count is invalid"
        )
    if (
        not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 1
    ):
        raise PublicDatasetInstallationError(
            "manifest artifact bytes is invalid"
        )

    dataset_path = manifest_path.parent / filename
    if not dataset_path.is_file():
        raise PublicDatasetInstallationError("dataset artifact is missing")
    dataset_bytes = dataset_path.read_bytes()
    if len(dataset_bytes) != byte_count:
        raise PublicDatasetInstallationError("dataset byte count mismatch")
    if _sha256_bytes(dataset_bytes) != artifact_sha256:
        raise PublicDatasetInstallationError("dataset sha256 mismatch")

    try:
        records = json.loads(dataset_bytes)
    except json.JSONDecodeError as exc:
        raise PublicDatasetInstallationError(
            "dataset artifact is not valid JSON"
        ) from exc
    if not isinstance(records, list):
        raise PublicDatasetInstallationError("dataset must be a JSON array")
    if len(records) != row_count:
        raise PublicDatasetInstallationError("dataset row count mismatch")

    identities: list[tuple[str, str]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise PublicDatasetInstallationError(
                f"dataset row {index} is not an object"
            )
        source_id = record.get("source_id")
        external_id = record.get("external_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise PublicDatasetInstallationError(
                f"dataset row {index} source_id is invalid"
            )
        if not isinstance(external_id, str) or not external_id.strip():
            raise PublicDatasetInstallationError(
                f"dataset row {index} external_id is invalid"
            )
        identities.append((source_id, external_id))
    if len(set(identities)) != len(identities):
        raise PublicDatasetInstallationError(
            "dataset contains duplicate policy identities"
        )

    return VerifiedPublicDataset(
        dataset_version=dataset_version,
        manifest_path=manifest_path,
        dataset_path=dataset_path,
        manifest_sha256=_sha256_bytes(manifest_bytes),
        artifact_sha256=artifact_sha256,
        expected_policy_count=row_count,
        identities=tuple(identities),
    )


def policy_identity_sha256(identities: Sequence[tuple[str, str]]) -> str:
    canonical = json.dumps(
        sorted(identities),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _resolve_policy_ids(
    db: Session,
    identities: Sequence[tuple[str, str]],
) -> dict[tuple[str, str], int]:
    resolved: dict[tuple[str, str], int] = {}
    for start in range(0, len(identities), 250):
        chunk = identities[start : start + 250]
        rows = db.execute(
            select(Policy.id, Policy.source_id, Policy.external_id).where(
                or_(
                    *(
                        (Policy.source_id == source_id)
                        & (Policy.external_id == external_id)
                        for source_id, external_id in chunk
                    )
                )
            )
        ).all()
        for policy_id, source_id, external_id in rows:
            if external_id is not None:
                resolved[(source_id, external_id)] = policy_id
    return resolved


def install_public_dataset(
    db: Session,
    verified: VerifiedPublicDataset,
) -> PublicDatasetInstallationResult:
    """Import, map, and activate a verified release in one transaction."""

    with db.begin():
        result = import_seed_data(
            db,
            verified.dataset_path,
            transaction_owner=False,
            allow_active_public_updates=True,
        )
        has_import_errors = bool(
            result.skipped
            or result.rejected
            or result.failed
            or result.total != verified.expected_policy_count
            or result.accepted != verified.expected_policy_count
        )
        if has_import_errors:
            raise PublicDatasetInstallationError(
                "dataset import counts did not match the verified manifest"
            )

        policies = _resolve_policy_ids(db, verified.identities)
        if len(policies) != verified.expected_policy_count:
            raise PublicDatasetInstallationError(
                "dataset membership could not resolve every policy identity"
            )

        installation = db.get(
            PublicDatasetInstallation,
            verified.dataset_version,
        )
        if installation is None:
            installation = PublicDatasetInstallation(
                dataset_version=verified.dataset_version,
                manifest_sha256=verified.manifest_sha256,
                artifact_sha256=verified.artifact_sha256,
                expected_policy_count=verified.expected_policy_count,
                status="installed",
                activated_at=None,
            )
            db.add(installation)
            db.flush()
        elif (
            installation.manifest_sha256 != verified.manifest_sha256
            or installation.artifact_sha256 != verified.artifact_sha256
            or installation.expected_policy_count
            != verified.expected_policy_count
        ):
            raise PublicDatasetInstallationError(
                "dataset version is already installed with different content"
            )

        db.execute(
            delete(PublicDatasetMembership).where(
                PublicDatasetMembership.dataset_version
                == verified.dataset_version
            )
        )
        db.add_all(
            PublicDatasetMembership(
                dataset_version=verified.dataset_version,
                source_id=source_id,
                external_id=external_id,
                policy_id=policies[(source_id, external_id)],
            )
            for source_id, external_id in verified.identities
        )
        db.flush()

        db.execute(
            update(PublicDatasetInstallation)
            .where(PublicDatasetInstallation.status == "active")
            .values(status="installed", activated_at=None)
        )
        installation.status = "active"
        installation.activated_at = datetime.now(timezone.utc)
        db.flush()

    return PublicDatasetInstallationResult(
        dataset_version=verified.dataset_version,
        expected_policy_count=verified.expected_policy_count,
        identity_sha256=policy_identity_sha256(verified.identities),
        import_result=result,
    )
