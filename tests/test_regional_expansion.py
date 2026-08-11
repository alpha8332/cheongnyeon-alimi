from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

from collectors.extracted import ExtractionError
from collectors.regional_expansion import (
    RegionalBatchCheckpoint,
    RegionalBrowserCaptureStore,
    RegionalBrowserExtractor,
    RegionalCheckpointStore,
    RegionalOutcome,
    decide_expanded_regional_policy,
    outcome_from_decisions,
)
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalityStatus,
)
from collectors.runtime import replay_runtime_raw
from collectors.normalizer import Normalizer
from collectors.storage import RawDocumentStore
from scripts.import_regional_browser_capture import main as import_capture_main


NOW = datetime(2026, 8, 11, 5, tzinfo=timezone.utc)
DAEGU_SOURCE_ID = "regional-daegu-youth-platform"
GANGWON_SOURCE_ID = "regional-gangwon-youth-platform"


def daegu_capture() -> dict[str, object]:
    return {
        "source_id": DAEGU_SOURCE_ID,
        "list_url": (
            "https://www.dgjump.com/open_content/info/info_list_01?page=1"
        ),
        "page": 1,
        "total_count": 1,
        "has_next": False,
        "action_trace": ["홈", "청년 꿀정보", "정책 상세"],
        "items": [
            {
                "external_id": "8366",
                "title": "대구 청년 응시료 지원",
                "summary": "대구 청년의 구직 비용 지원",
                "category": "일자리",
                "detail_url": (
                    "https://www.dgjump.com/open_content/info/"
                    "info_list_01_view?ap_seq=8366"
                ),
                "request_identity": None,
                "detail": {
                    "title": "대구 청년 응시료 지원",
                    "organization": "대구광역시 청년정책과",
                    "category": "일자리",
                    "application_period": "2026-08-01 ~ 2026-08-31",
                    "source_region": "대구광역시",
                    "eligibility": "대구광역시에 거주하는 청년",
                    "support_content": "자격시험 응시료 지원",
                    "application_method": "https://www.dgjump.com/apply",
                    "contact": "대구광역시 청년정책과 053-000-0000",
                    "required_documents": "신청서",
                    "exclusions": None,
                    "age": "만 19세 ~ 만 39세",
                },
            }
        ],
    }


class RegionalBrowserExpansionTests(unittest.TestCase):
    def test_capture_cli_stores_replayable_raw(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            capture_path = root / "capture.json"
            capture_path.write_text(
                json.dumps(daegu_capture(), ensure_ascii=False),
                encoding="utf-8",
            )
            stdout = StringIO()
            result = import_capture_main(
                [str(capture_path), "--raw-root", str(root / "raw")],
                stdout=stdout,
            )
            stored = list((root / "raw").rglob("*.json"))
        self.assertEqual(0, result)
        self.assertEqual(3, len(stored))
        self.assertIn("items=1 raw_documents=3", stdout.getvalue())

    def test_capture_cli_rejects_invalid_root_without_raw(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            capture_path = root / "capture.json"
            capture_path.write_text("[]", encoding="utf-8")
            stderr = StringIO()
            result = import_capture_main(
                [str(capture_path), "--raw-root", str(root / "raw")],
                stderr=stderr,
            )
        self.assertEqual(1, result)
        self.assertIn("capture rejected", stderr.getvalue())
        self.assertFalse((root / "raw").exists())

    def test_actual_capture_replays_through_region_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            result = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID, store=store, now=lambda: NOW
            ).save(daegu_capture())
            policy = RegionalBrowserExtractor(DAEGU_SOURCE_ID).extract(
                store.load(path) for path in result.stored_paths
            )[0]
            replay = replay_runtime_raw(
                raw_root=temp_dir, source_id=DAEGU_SOURCE_ID, limit=1
            )
        decision = decide_expanded_regional_policy(
            policy, as_of=date(2026, 8, 11)
        )
        self.assertEqual(3, result.raw_document_count)
        self.assertIs(RegionalityStatus.REGIONAL_CONFIRMED, decision.regionality)
        self.assertIs(ApplicationAvailability.OPEN, decision.application)
        self.assertTrue(decision.accepted)
        self.assertTrue(replay.regional_decisions[0]["accepted"])
        self.assertFalse(replay.duplicate_decisions[0]["accepted"])
        normalized = Normalizer().normalize(policy).program
        assert normalized is not None
        self.assertEqual("partial", normalized.eligibility_summary.coverage.value)
        self.assertEqual(
            ["신청서"],
            [item.text for item in normalized.eligibility_summary.documents],
        )
        self.assertEqual(
            ["대구광역시 청년정책과 053-000-0000"],
            [
                item.value
                for item in normalized.eligibility_summary.institutional_contacts
            ],
        )

    def test_capture_rejects_unapproved_detail_identity(self) -> None:
        capture = deepcopy(daegu_capture())
        capture["items"][0]["detail_url"] = (
            "https://www.dgjump.com/open_content/info/"
            "info_list_01_view?ap_seq=9999"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExtractionError):
                RegionalBrowserCaptureStore(
                    DAEGU_SOURCE_ID, store=RawDocumentStore(temp_dir)
                ).save(capture)

    def test_portal_location_does_not_replace_youth_target_evidence(self) -> None:
        capture = daegu_capture()
        item = capture["items"][0]
        item["title"] = "지역 관광상품 개발 지원"
        item["detail"]["title"] = "지역 관광상품 개발 지원"
        item["detail"]["eligibility"] = "대구광역시 관내 관광사업자"
        item["detail"]["age"] = None
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            result = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID, store=store, now=lambda: NOW
            ).save(capture)
            policy = RegionalBrowserExtractor(DAEGU_SOURCE_ID).extract(
                store.load(path) for path in result.stored_paths
            )[0]
        decision = decide_expanded_regional_policy(
            policy, as_of=date(2026, 8, 11)
        )
        self.assertFalse(decision.accepted)
        self.assertIn("youth_target_unconfirmed", decision.reason_codes)

    def test_post_identity_requires_external_id_and_mode(self) -> None:
        capture = daegu_capture()
        capture["source_id"] = GANGWON_SOURCE_ID
        capture["list_url"] = (
            "https://job.gwd.go.kr/youth/policies/search/gangwon_policies"
        )
        item = capture["items"][0]
        item["external_id"] = "A2026021300300200900000001"
        item["detail_url"] = capture["list_url"]
        item["request_identity"] = "bizId=WRONG&mode=gw"
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExtractionError):
                RegionalBrowserCaptureStore(
                    GANGWON_SOURCE_ID, store=RawDocumentStore(temp_dir)
                ).save(capture)


class RegionalCheckpointTests(unittest.TestCase):
    def test_discovery_queue_allows_bounded_detail_decision_batches(self) -> None:
        discovered = RegionalBatchCheckpoint.initial(DAEGU_SOURCE_ID).discover(
            page=1,
            external_ids=("8366", "8345", "8318", "8301"),
            total_count=4,
            has_next=False,
        )
        first = discovered.decide(
            {
                "8366": RegionalOutcome.ACCEPTED,
                "8345": RegionalOutcome.REVIEW,
                "8318": RegionalOutcome.CLOSED,
            }
        )
        complete = first.decide({"8301": RegionalOutcome.DUPLICATE})
        self.assertTrue(discovered.discovery_complete)
        self.assertFalse(discovered.complete)
        self.assertEqual(1, first.to_dict()["pending_count"])
        self.assertTrue(complete.complete)

    def test_checkpoint_requires_one_decision_per_identity_and_resumes(self) -> None:
        first = RegionalBatchCheckpoint.initial(DAEGU_SOURCE_ID).advance(
            page=1,
            external_ids=("8366", "8345"),
            outcomes={
                "8366": RegionalOutcome.ACCEPTED,
                "8345": RegionalOutcome.CLOSED,
            },
            total_count=3,
            has_next=True,
        )
        complete = first.advance(
            page=2,
            external_ids=("8318",),
            outcomes={"8318": RegionalOutcome.DUPLICATE},
            total_count=3,
            has_next=False,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RegionalCheckpointStore(temp_dir)
            store.save(complete)
            loaded = store.load(DAEGU_SOURCE_ID)
        self.assertEqual(complete, loaded)
        self.assertTrue(complete.complete)
        self.assertEqual(
            {"accepted": 1, "duplicate": 1, "review": 0, "closed": 1, "failed": 0},
            complete.counts(),
        )

    def test_checkpoint_rejects_silent_omission_and_early_end(self) -> None:
        checkpoint = RegionalBatchCheckpoint.initial(DAEGU_SOURCE_ID)
        with self.assertRaises(ValueError):
            checkpoint.advance(
                page=1,
                external_ids=("8366", "8345"),
                outcomes={"8366": RegionalOutcome.ACCEPTED},
                total_count=2,
                has_next=False,
            )
        with self.assertRaises(ValueError):
            checkpoint.advance(
                page=1,
                external_ids=("8366",),
                outcomes={"8366": RegionalOutcome.ACCEPTED},
                total_count=2,
                has_next=False,
            )

    def test_checkpoint_store_rejects_unapproved_path_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RegionalCheckpointStore(temp_dir)
            with self.assertRaises(ValueError):
                store.load("../outside")

    def test_outcome_precedence_is_closed_then_duplicate_then_accepted(self) -> None:
        self.assertIs(
            RegionalOutcome.CLOSED,
            outcome_from_decisions(
                {"application": "closed", "accepted": False}, None
            ),
        )
        self.assertIs(
            RegionalOutcome.DUPLICATE,
            outcome_from_decisions(
                {"application": "open", "accepted": True},
                {"accepted": False},
            ),
        )


if __name__ == "__main__":
    unittest.main()
