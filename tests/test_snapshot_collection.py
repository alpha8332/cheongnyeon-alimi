from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from collectors.base import CollectionOptions, CollectionResult
from collectors.snapshot import (
    SnapshotError,
    SnapshotManifestStore,
    collect_snapshot,
)


STARTED_AT = datetime(2026, 8, 4, 1, 0, tzinfo=timezone.utc)


class FakePagedCollector:
    source_id = "youthcenter-api"

    def __init__(self, total_count: int) -> None:
        self.total_count = total_count
        self.calls: list[CollectionOptions] = []

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        self.calls.append(selected)
        start = (selected.page - 1) * selected.limit
        end = min(start + selected.limit, self.total_count)
        external_ids = tuple(
            f"POLICY-{index:04d}" for index in range(start, end)
        )
        detail_count = min(selected.detail_limit, len(external_ids))
        return CollectionResult(
            source_id=self.source_id,
            request_count=1 + detail_count,
            item_count=len(external_ids),
            detail_count=detail_count,
            stored_paths=(),
            page=selected.page,
            page_size=selected.limit,
            total_count=self.total_count,
            external_ids=external_ids,
            list_response_document_id=f"{selected.page:032x}",
            detail_document_ids=tuple(
                f"{1000 + index:032x}"
                for index in range(detail_count)
            ),
        )


class SnapshotCollectionTests(unittest.TestCase):
    def test_collects_all_pages_and_writes_complete_manifest(self) -> None:
        collector = FakePagedCollector(total_count=12)
        times = iter((STARTED_AT, STARTED_AT + timedelta(seconds=1)))
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SnapshotManifestStore(temp_dir)
            manifest = collect_snapshot(
                collector,
                manifest_store=store,
                page_size=5,
                detail_limit=2,
                request_budget=5,
                now=lambda: next(times),
            )
            loaded = store.load(
                collector.source_id,
                manifest.snapshot_id,
            )

        self.assertEqual(12, loaded.item_count)
        self.assertEqual(5, loaded.request_count)
        self.assertEqual(3, len(loaded.list_response_document_ids))
        self.assertEqual(2, len(loaded.detail_document_ids))
        self.assertEqual(
            [2, 0, 0],
            [call.detail_limit for call in collector.calls],
        )

    def test_insufficient_budget_leaves_no_complete_manifest(self) -> None:
        collector = FakePagedCollector(total_count=12)
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SnapshotManifestStore(temp_dir)
            with self.assertRaisesRegex(
                SnapshotError,
                "request budget is insufficient",
            ):
                collect_snapshot(
                    collector,
                    manifest_store=store,
                    page_size=5,
                    request_budget=2,
                    now=lambda: STARTED_AT,
                )

            self.assertIsNone(store.latest(collector.source_id))

    def test_inconsistent_collector_counts_are_not_manifested(self) -> None:
        collector = FakePagedCollector(total_count=1)
        original_collect = collector.collect

        def inconsistent_collect(
            options: CollectionOptions | None = None,
        ) -> CollectionResult:
            return replace(original_collect(options), item_count=2)

        collector.collect = inconsistent_collect  # type: ignore[method-assign]
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SnapshotManifestStore(temp_dir)
            with self.assertRaisesRegex(
                SnapshotError,
                "snapshot counts do not match",
            ):
                collect_snapshot(
                    collector,
                    manifest_store=store,
                    page_size=1,
                    request_budget=1,
                    now=lambda: STARTED_AT,
                )

            self.assertIsNone(store.latest(collector.source_id))

    def test_manifest_identity_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SnapshotManifestStore(Path(temp_dir))
            with self.assertRaisesRegex(SnapshotError, "invalid snapshot ID"):
                store.load("youthcenter-api", "../secret")


if __name__ == "__main__":
    unittest.main()
