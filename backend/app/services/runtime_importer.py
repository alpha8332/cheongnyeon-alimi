from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.seed_importer import ImportResult, import_programs
from app.services.aggregator_baseline import load_aggregator_baseline
from collectors.cross_source_duplicate import (
    CrossSourceDecisionManifestStore,
)
from collectors.gyeongbuk_youth import SOURCE_ID as GYEONGBUK_SOURCE_ID
from collectors.runtime import RuntimeReplayResult, replay_runtime_raw


@dataclass(frozen=True)
class RuntimeImportResult:
    replay: RuntimeReplayResult
    database: ImportResult
    decision_manifest_id: str | None = None


def import_runtime_raw(
    db: Session,
    *,
    raw_root: str | Path,
    source_id: str,
    limit: int,
    snapshot_id: str | None = None,
    dry_run: bool = False,
    decision_root: str | Path | None = None,
) -> RuntimeImportResult:
    """Replay one source batch and pass accepted programs to the importer."""
    replay = replay_runtime_raw(
        raw_root=raw_root,
        source_id=source_id,
        limit=limit,
        snapshot_id=snapshot_id,
    )
    if source_id == GYEONGBUK_SOURCE_ID and replay.duplicate_decisions:
        replay = replay_runtime_raw(
            raw_root=raw_root,
            source_id=source_id,
            limit=limit,
            snapshot_id=snapshot_id,
            duplicate_baseline=load_aggregator_baseline(
                db, raw_root=raw_root
            ),
        )
    decision_manifest_id = None
    if replay.duplicate_manifest is not None and decision_root is not None:
        CrossSourceDecisionManifestStore(decision_root).save(
            replay.duplicate_manifest
        )
        decision_manifest_id = replay.duplicate_manifest.manifest_id
    normalization_issues = replay.normalization_issues or tuple(
        () for _ in replay.programs
    )
    if len(normalization_issues) != len(replay.programs):
        raise ValueError(
            "runtime normalization issues must align with programs"
        )
    database = import_programs(
        db,
        replay.programs,
        dry_run=dry_run,
        normalization_issues=normalization_issues,
    )
    return RuntimeImportResult(
        replay=replay,
        database=database,
        decision_manifest_id=decision_manifest_id,
    )
