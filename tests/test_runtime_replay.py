from __future__ import annotations

import json
import socket
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.runtime import (
    RuntimeReplayError,
    _latest_batch,
    replay_runtime_raw,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "fixtures" / "raw"


class RuntimeReplayTests(unittest.TestCase):
    def test_synthetic_raw_replays_without_external_network(self) -> None:
        with patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network access is not allowed"),
        ) as connection:
            youth = replay_runtime_raw(
                raw_root=RAW_ROOT,
                source_id="youthcenter-api",
                limit=100,
            )
            bokjiro = replay_runtime_raw(
                raw_root=RAW_ROOT,
                source_id="bokjiro-central-welfare-api",
                limit=100,
            )

        connection.assert_not_called()
        self.assertEqual(4, youth.raw_document_count)
        self.assertEqual(3, youth.extracted_count)
        self.assertEqual(2, youth.valid_count)
        self.assertEqual(0, youth.partial_count)
        self.assertEqual(1, youth.invalid_count)
        self.assertEqual(2, youth.accepted_count)
        self.assertEqual("SYN-YOUTH-REJECTED", youth.issues[0].external_id)
        self.assertEqual(("schema_type",), youth.issues[0].codes)
        self.assertEqual("$.title", youth.issues[0].paths[0])
        self.assertEqual(2, len(youth.issues[0].raw_document_ids))

        self.assertEqual(4, bokjiro.raw_document_count)
        self.assertEqual(2, bokjiro.extracted_count)
        self.assertEqual(0, bokjiro.valid_count)
        self.assertEqual(2, bokjiro.partial_count)
        self.assertEqual(0, bokjiro.invalid_count)
        self.assertEqual(2, bokjiro.accepted_count)

    def test_limit_keeps_parent_and_matching_detail(self) -> None:
        replay = replay_runtime_raw(
            raw_root=RAW_ROOT,
            source_id="bokjiro-central-welfare-api",
            limit=1,
        )

        self.assertEqual(3, replay.raw_document_count)
        self.assertEqual(1, replay.extracted_count)
        self.assertEqual(1, replay.partial_count)
        self.assertEqual("SYN-BOK-001", replay.programs[0]["external_id"])
        self.assertEqual(3, len(replay.programs[0]["provenance"]))

    def test_missing_source_raw_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                RuntimeReplayError,
                "no stored Raw documents",
            ):
                replay_runtime_raw(
                    raw_root=Path(temp_dir),
                    source_id="youthcenter-api",
                    limit=10,
                )

    def test_latest_batch_does_not_mix_older_details(self) -> None:
        existing = tuple(
            RawPolicyDocument.from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
            for path in sorted(
                (RAW_ROOT / "bokjiro-central-welfare-api").glob("*.json")
            )
        )
        collected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
        latest_response = RawPolicyDocument.from_bytes(
            document_id="f" * 32,
            source_id="bokjiro-central-welfare-api",
            source_type=SourceType.API,
            document_role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url="https://fixture.invalid/bokjiro/list",
            collected_at=collected_at,
            content_type="application/xml",
            raw_format=RawFormat.XML,
            raw_payload=b"<wantedList/>",
            http_status=200,
            collector_version="test/1.0",
        )
        latest_item = RawPolicyDocument.from_bytes(
            document_id="e" * 32,
            source_id="bokjiro-central-welfare-api",
            source_type=SourceType.API,
            document_role=RawDocumentRole.LIST_ITEM,
            external_id="SYN-BOK-001",
            parent_document_id=latest_response.document_id,
            source_url="https://fixture.invalid/bokjiro/list",
            collected_at=collected_at,
            content_type="application/xml",
            raw_format=RawFormat.XML,
            raw_payload=(
                b"<servList><servId>SYN-BOK-001</servId>"
                b"<servNm>latest</servNm></servList>"
            ),
            http_status=200,
            collector_version="test/1.0",
        )

        selected = _latest_batch(
            (*existing, latest_response, latest_item),
            limit=10,
        )

        self.assertEqual(
            (latest_response.document_id, latest_item.document_id),
            tuple(document.document_id for document in selected),
        )


if __name__ == "__main__":
    unittest.main()
