from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.seed_importer import ImportResult, import_programs
from collectors.runtime import RuntimeReplayResult, replay_runtime_raw


@dataclass(frozen=True)
class RuntimeImportResult:
    replay: RuntimeReplayResult
    database: ImportResult


def import_runtime_raw(
    db: Session,
    *,
    raw_root: str | Path,
    source_id: str,
    limit: int,
    snapshot_id: str | None = None,
    dry_run: bool = False,
) -> RuntimeImportResult:
    """Replay one source batch and pass accepted programs to the importer."""
    replay = replay_runtime_raw(
        raw_root=raw_root,
        source_id=source_id,
        limit=limit,
        snapshot_id=snapshot_id,
    )
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
    )
