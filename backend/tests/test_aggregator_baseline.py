import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.aggregator_baseline import load_aggregator_baseline
from app.services.seed_importer import import_programs
from collectors.snapshot import SnapshotManifest, SnapshotManifestStore


ROOT = Path(__file__).resolve().parents[2]


def test_loads_approved_snapshot_and_database_baseline(db, tmp_path) -> None:
    programs = json.loads(
        (ROOT / "data" / "fixtures" / "normalized" / "programs.json")
        .read_text(encoding="utf-8")
    )
    result = import_programs(db, programs)
    assert result.inserted == 4

    source_counts = {
        source_id: sum(
            program["source_id"] == source_id for program in programs
        )
        for source_id in (
            "youthcenter-api",
            "bokjiro-central-welfare-api",
        )
    }
    store = SnapshotManifestStore(tmp_path)
    for source_id, marker in (
        ("youthcenter-api", "1"),
        ("bokjiro-central-welfare-api", "2"),
    ):
        store.save(
            SnapshotManifest(
                snapshot_id=marker * 32,
                source_id=source_id,
                started_at=datetime(2026, 8, 11, tzinfo=timezone.utc),
                completed_at=datetime(
                    2026, 8, 11, 0, 1, tzinfo=timezone.utc
                ),
                page_size=500,
                detail_limit=0,
                request_budget=1,
                request_count=1,
                total_count=source_counts[source_id],
                item_count=source_counts[source_id],
                list_response_document_ids=(marker * 31 + "a",),
                detail_document_ids=(),
            )
        )

    baseline = load_aggregator_baseline(
        db,
        raw_root=tmp_path,
        now=lambda: datetime(2026, 8, 11, 1, tzinfo=timezone.utc),
    )

    assert len(baseline.records) == 4
    assert {
        descriptor.source_id: descriptor.database_policy_count
        for descriptor in baseline.descriptors
    } == source_counts
    assert len(baseline.baseline_id) == 32
