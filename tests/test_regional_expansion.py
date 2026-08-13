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
    REGIONAL_PAGINATION_SPECS,
    RegionalBatchCheckpoint,
    RegionalBrowserCaptureStore,
    RegionalBrowserExtractor,
    RegionalCheckpointStore,
    RegionalOutcome,
    RegionalPaginationTermination,
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
from scripts.serve_regional_browser_capture import (
    _pending_detail_ids,
    _store_recovery,
    _store_recapture,
    _store_discovery,
    _store_failure,
)


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


def gangwon_recovery_capture() -> dict[str, object]:
    external_id = "A2026040800300200900100004"
    return {
        "source_id": GANGWON_SOURCE_ID,
        "list_url": (
            "https://job.gwd.go.kr/youth/policies/search/gangwon_policies"
        ),
        "page": 1,
        "total_count": 1,
        "has_next": False,
        "discovered_ids": [external_id],
        "action_trace": [
            "goto approved list",
            "paginate page 2",
            "recover selected failed detail",
        ],
        "items": [
            {
                "external_id": external_id,
                "title": "2026 청년도전지원사업",
                "summary": None,
                "category": "교육",
                "detail_url": (
                    "https://job.gwd.go.kr/youth/policies/search/"
                    "gangwon_policies"
                ),
                "request_identity": f"bizId={external_id}&mode=gw",
                "detail": {
                    "title": "2026 청년도전지원사업",
                    "organization": "춘천시청 기업지원과",
                    "category": "교육",
                    "application_period": "상시",
                    "source_region": "강원특별자치도",
                    "eligibility": "최근 6개월간 취업 이력이 없는 주민",
                    "support_content": "참여수당 지급",
                    "application_method": "사회적협동조합 문의",
                    "contact": "033-818-9288",
                    "required_documents": None,
                    "exclusions": "재학생",
                    "age": None,
                },
            }
        ],
    }


class RegionalBrowserExpansionTests(unittest.TestCase):
    def test_every_approved_source_has_an_operational_pagination_contract(
        self,
    ) -> None:
        self.assertEqual(13, len(REGIONAL_PAGINATION_SPECS))
        self.assertEqual(
            "official_current_filter",
            REGIONAL_PAGINATION_SPECS[
                "regional-busan-youth-platform"
            ].scope,
        )
        self.assertEqual(
            RegionalPaginationTermination.REPORTED_TOTAL,
            REGIONAL_PAGINATION_SPECS[GANGWON_SOURCE_ID].termination,
        )

    def test_pagination_contract_rejects_missing_total_and_safety_overrun(
        self,
    ) -> None:
        reported = REGIONAL_PAGINATION_SPECS[GANGWON_SOURCE_ID]
        with self.assertRaisesRegex(ExtractionError, "total is required"):
            reported.validate_page(
                page=1,
                discovered_count=1,
                total_count=None,
                has_next=True,
            )

        bounded = REGIONAL_PAGINATION_SPECS[DAEGU_SOURCE_ID]
        with self.assertRaisesRegex(ExtractionError, "safety limit"):
            bounded.validate_page(
                page=bounded.safety_max_pages,
                discovered_count=1,
                total_count=None,
                has_next=True,
            )

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
                [
                    str(capture_path),
                    "--raw-root",
                    str(root / "raw"),
                    "--checkpoint-root",
                    str(root / "checkpoints"),
                ],
                stdout=stdout,
            )
            stored = list((root / "raw").rglob("*.json"))
            checkpoint = RegionalCheckpointStore(root / "checkpoints").load(
                DAEGU_SOURCE_ID
            )
        self.assertEqual(0, result)
        self.assertEqual(3, len(stored))
        assert checkpoint is not None
        self.assertEqual(("8366",), checkpoint.discovered_ids)
        self.assertEqual(("8366",), checkpoint.captured_ids)
        self.assertEqual(1, checkpoint.to_dict()["pending_count"])
        self.assertIn(
            "discovered=1 details=1 raw_documents=3 "
            "pending_details=0 pending_decisions=1",
            stdout.getvalue(),
        )

    def test_capture_preserves_field_presence_observations(self) -> None:
        capture = daegu_capture()
        detail = capture["items"][0]["detail"]
        detail["eligibility"] = None
        detail["evidence_observations"] = {
            field_name: {
                "label": field_name if value is not None else None,
                "status": (
                    "value_extracted" if value is not None else "label_not_found"
                ),
            }
            for field_name, value in detail.items()
            if field_name != "title"
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = RawDocumentStore(root / "raw")
            result = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID,
                store=store,
                now=lambda: NOW,
            ).save(capture)
            documents = tuple(store.load(path) for path in result.stored_paths)
            selected = RegionalBrowserExtractor(DAEGU_SOURCE_ID).extract(
                documents
            )[0]

        decision = decide_expanded_regional_policy(
            selected, as_of=date(2026, 8, 11)
        )
        observations = dict(decision.evidence.field_observations)
        self.assertEqual(
            "value_extracted",
            observations["implementing_organization_text"],
        )
        self.assertEqual(
            "label_not_found", observations["region_eligibility_text"]
        )

    def test_ryp8_source_scope_is_staged_without_premature_promotion(
        self,
    ) -> None:
        capture = daegu_capture()
        capture["source_scope"] = {
            "jurisdiction_text": "대구청년커뮤니티포털 '젊프'",
            "operator_text": "대구청년커뮤니티포털 '젊프'",
            "youth_policy_scope_text": "청년 꿀정보",
            "application_scope_text": "현재 모집 중",
        }
        detail = capture["items"][0]["detail"]
        detail["organization"] = "청년지원센터"
        detail["source_region"] = None
        detail["eligibility"] = "청년"
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(Path(temp_dir) / "raw")
            result = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID,
                store=store,
                now=lambda: NOW,
            ).save(capture)
            policy = RegionalBrowserExtractor(DAEGU_SOURCE_ID).extract(
                store.load(path) for path in result.stored_paths
            )[0]

        decision = decide_expanded_regional_policy(
            policy, as_of=date(2026, 8, 11)
        )
        self.assertEqual(
            "현재 모집 중",
            policy.extra["source_scope"]["application_scope_text"],
        )
        self.assertIs(
            RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
            decision.regionality,
        )
        self.assertFalse(decision.accepted)

    def test_capture_rejects_observation_that_disagrees_with_value(self) -> None:
        capture = daegu_capture()
        detail = capture["items"][0]["detail"]
        detail["evidence_observations"] = {
            field_name: {"label": None, "status": "label_not_found"}
            for field_name in detail
            if field_name != "title"
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID,
                store=RawDocumentStore(Path(temp_dir) / "raw"),
                now=lambda: NOW,
            )
            with self.assertRaisesRegex(ExtractionError, "contract drift"):
                store.save(capture)

    def test_capture_accepts_present_label_with_empty_source_value(self) -> None:
        capture = daegu_capture()
        detail = capture["items"][0]["detail"]
        detail["eligibility"] = None
        detail["evidence_observations"] = {
            field_name: {
                "label": (
                    "지원대상"
                    if field_name == "eligibility"
                    else field_name
                    if value is not None
                    else None
                ),
                "status": (
                    "label_present_value_empty"
                    if field_name == "eligibility"
                    else "value_extracted"
                    if value is not None
                    else "label_not_found"
                ),
            }
            for field_name, value in detail.items()
            if field_name != "title"
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result = RegionalBrowserCaptureStore(
                DAEGU_SOURCE_ID,
                store=RawDocumentStore(Path(temp_dir) / "raw"),
                now=lambda: NOW,
            ).save(capture)

        self.assertEqual(1, result.item_count)

    def test_limited_recapture_preserves_completed_checkpoint(self) -> None:
        capture = daegu_capture()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_store = RegionalCheckpointStore(root / "checkpoints")
            checkpoint = RegionalBatchCheckpoint.initial(
                DAEGU_SOURCE_ID
            ).discover(
                page=1,
                external_ids=("8366",),
                total_count=1,
                has_next=False,
            )
            checkpoint = checkpoint.capture(("8366",)).decide(
                {"8366": RegionalOutcome.REVIEW}
            )
            checkpoint_store.save(checkpoint)

            result, unchanged = _store_recapture(
                capture,
                raw_root=root / "raw",
                checkpoint_root=root / "checkpoints",
            )

            self.assertEqual(3, result.raw_document_count)
            self.assertEqual(checkpoint, unchanged)
            self.assertEqual(
                checkpoint,
                checkpoint_store.load(DAEGU_SOURCE_ID),
            )

    def test_recapture_allows_explicit_current_only_identity(self) -> None:
        capture = daegu_capture()
        capture["total_count"] = 2
        capture["recapture_excluded_ids"] = ["8345"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_store = RegionalCheckpointStore(root / "checkpoints")
            checkpoint = RegionalBatchCheckpoint.initial(
                DAEGU_SOURCE_ID
            ).discover(
                page=1,
                external_ids=("8366",),
                total_count=1,
                has_next=False,
            )
            checkpoint = checkpoint.capture(("8366",)).decide(
                {"8366": RegionalOutcome.REVIEW}
            )
            checkpoint_store.save(checkpoint)

            result, unchanged = _store_recapture(
                capture,
                raw_root=root / "raw",
                checkpoint_root=root / "checkpoints",
            )

            self.assertEqual(3, result.raw_document_count)
            self.assertEqual(checkpoint, unchanged)
            self.assertEqual(checkpoint, checkpoint_store.load(DAEGU_SOURCE_ID))

    def test_recapture_rejects_checkpoint_identity_as_current_only(self) -> None:
        capture = daegu_capture()
        capture["total_count"] = 2
        capture["recapture_excluded_ids"] = ["8366"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_store = RegionalCheckpointStore(root / "checkpoints")
            checkpoint = RegionalBatchCheckpoint.initial(
                DAEGU_SOURCE_ID
            ).discover(
                page=1,
                external_ids=("8366",),
                total_count=1,
                has_next=False,
            )
            checkpoint = checkpoint.capture(("8366",)).decide(
                {"8366": RegionalOutcome.REVIEW}
            )
            checkpoint_store.save(checkpoint)

            with self.assertRaisesRegex(
                ValueError,
                "recapture does not match completed checkpoint",
            ):
                _store_recapture(
                    capture,
                    raw_root=root / "raw",
                    checkpoint_root=root / "checkpoints",
                )

            self.assertFalse((root / "raw").exists())

    def test_recapture_rejects_unnecessary_current_only_identity(self) -> None:
        capture = daegu_capture()
        capture["recapture_excluded_ids"] = ["8345"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_store = RegionalCheckpointStore(root / "checkpoints")
            checkpoint = RegionalBatchCheckpoint.initial(
                DAEGU_SOURCE_ID
            ).discover(
                page=1,
                external_ids=("8366",),
                total_count=1,
                has_next=False,
            )
            checkpoint = checkpoint.capture(("8366",)).decide(
                {"8366": RegionalOutcome.REVIEW}
            )
            checkpoint_store.save(checkpoint)

            with self.assertRaisesRegex(
                ValueError,
                "recapture does not match completed checkpoint",
            ):
                _store_recapture(
                    capture,
                    raw_root=root / "raw",
                    checkpoint_root=root / "checkpoints",
                )

            self.assertFalse((root / "raw").exists())

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

    def test_capture_cli_tracks_all_list_ids_with_bounded_details(self) -> None:
        first = daegu_capture()
        first["total_count"] = 3
        first["has_next"] = True
        first["discovered_ids"] = ["8366", "8345"]
        second = deepcopy(daegu_capture())
        second["page"] = 2
        second["list_url"] = (
            "https://www.dgjump.com/open_content/info/info_list_01?page=2"
        )
        second["items"][0]["external_id"] = "8318"
        second["items"][0]["detail_url"] = (
            "https://www.dgjump.com/open_content/info/"
            "info_list_01_view?ap_seq=8318"
        )
        second["discovered_ids"] = ["8318"]
        second["total_count"] = 3
        second["has_next"] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            capture_path = root / "capture.json"
            capture_path.write_text(
                json.dumps([first, second], ensure_ascii=False),
                encoding="utf-8",
            )
            result = import_capture_main(
                [
                    str(capture_path),
                    "--raw-root",
                    str(root / "raw"),
                    "--checkpoint-root",
                    str(root / "checkpoints"),
                ]
            )
            checkpoint = RegionalCheckpointStore(root / "checkpoints").load(
                DAEGU_SOURCE_ID
            )
        self.assertEqual(0, result)
        assert checkpoint is not None
        self.assertEqual(("8366", "8345", "8318"), checkpoint.discovered_ids)
        self.assertTrue(checkpoint.discovery_complete)
        self.assertFalse(checkpoint.complete)
        self.assertEqual(3, checkpoint.to_dict()["pending_count"])

    def test_capture_cli_resumes_a_second_detail_batch_on_the_same_page(
        self,
    ) -> None:
        first = daegu_capture()
        first["total_count"] = 2
        first["discovered_ids"] = ["8366", "8345"]
        second = deepcopy(first)
        second_item = second["items"][0]
        second_item["external_id"] = "8345"
        second_item["title"] = "second policy"
        second_item["detail_url"] = (
            "https://www.dgjump.com/open_content/info/"
            "info_list_01_view?ap_seq=8345"
        )
        second_item["detail"]["title"] = "second policy"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_root = root / "checkpoints"
            raw_root = root / "raw"
            for index, capture in enumerate((first, second), start=1):
                capture_path = root / f"capture-{index}.json"
                capture_path.write_text(
                    json.dumps(capture, ensure_ascii=False),
                    encoding="utf-8",
                )
                self.assertEqual(
                    0,
                    import_capture_main(
                        [
                            str(capture_path),
                            "--raw-root",
                            str(raw_root),
                            "--checkpoint-root",
                            str(checkpoint_root),
                        ],
                        stdout=StringIO(),
                    ),
                )
            checkpoint = RegionalCheckpointStore(checkpoint_root).load(
                DAEGU_SOURCE_ID
            )

        assert checkpoint is not None
        self.assertEqual(("8366", "8345"), checkpoint.discovered_ids)
        self.assertEqual(("8366", "8345"), checkpoint.captured_ids)
        self.assertEqual(0, checkpoint.to_dict()["pending_detail_count"])

    def test_capture_cli_preflight_failure_leaves_no_partial_raw(self) -> None:
        captures = [daegu_capture(), deepcopy(daegu_capture())]
        captures[1]["page"] = 3
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            capture_path = root / "capture.json"
            capture_path.write_text(
                json.dumps(captures, ensure_ascii=False),
                encoding="utf-8",
            )
            result = import_capture_main(
                [
                    str(capture_path),
                    "--raw-root",
                    str(root / "raw"),
                    "--checkpoint-root",
                    str(root / "checkpoints"),
                ]
            )
        self.assertEqual(1, result)
        self.assertFalse((root / "raw").exists())
        self.assertFalse((root / "checkpoints").exists())

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
    def test_discovery_endpoint_returns_only_unprocessed_detail_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            discovery = {
                "source_id": DAEGU_SOURCE_ID,
                "page": 1,
                "total_count": 2,
                "has_next": False,
                "discovered_ids": ["8366", "8345"],
            }
            checkpoint = _store_discovery(
                discovery, checkpoint_root=root
            )
            checkpoint = checkpoint.capture(("8366",))
            RegionalCheckpointStore(root).save(checkpoint)

            resumed = _store_discovery(
                discovery, checkpoint_root=root
            )

        self.assertEqual(["8345"], _pending_detail_ids(resumed))

    def test_failed_detail_completes_checkpoint_without_fake_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint = _store_failure(
                {
                    "source_id": GANGWON_SOURCE_ID,
                    "page": 1,
                    "total_count": 1,
                    "has_next": False,
                    "discovered_ids": ["A2026021300300200900000001"],
                    "failed_id": "A2026021300300200900000001",
                    "reason": "official detail error page",
                },
                checkpoint_root=Path(temp_dir),
            )

        self.assertTrue(checkpoint.complete)
        self.assertEqual((), checkpoint.captured_ids)
        self.assertEqual(0, checkpoint.to_dict()["pending_detail_count"])
        self.assertEqual(1, checkpoint.counts()["failed"])

    def test_failed_detail_recovery_replays_raw_and_reclassifies_review(
        self,
    ) -> None:
        capture = gangwon_recovery_capture()
        external_id = capture["items"][0]["external_id"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_root = root / "checkpoints"
            checkpoint = RegionalBatchCheckpoint.initial(
                GANGWON_SOURCE_ID
            ).discover(
                page=1,
                external_ids=(external_id,),
                total_count=1,
                has_next=False,
            ).decide({external_id: RegionalOutcome.FAILED})
            RegionalCheckpointStore(checkpoint_root).save(checkpoint)

            result, recovered = _store_recovery(
                capture,
                raw_root=root / "raw",
                checkpoint_root=checkpoint_root,
            )

            stored = RegionalCheckpointStore(checkpoint_root).load(
                GANGWON_SOURCE_ID
            )

        self.assertEqual(3, result.raw_document_count)
        self.assertEqual((external_id,), recovered.captured_ids)
        self.assertEqual(0, recovered.counts()["failed"])
        self.assertEqual(1, recovered.counts()["review"])
        self.assertEqual(recovered, stored)

    def test_failed_reclassification_rejects_uncorroborated_acceptance(
        self,
    ) -> None:
        external_id = "A2026040800300200900100004"
        checkpoint = RegionalBatchCheckpoint.initial(
            GANGWON_SOURCE_ID
        ).discover(
            page=1,
            external_ids=(external_id,),
            total_count=1,
            has_next=False,
        ).capture((external_id,)).decide(
            {external_id: RegionalOutcome.FAILED}
        )

        with self.assertRaisesRegex(ValueError, "requires review"):
            checkpoint.reclassify_failed(
                {external_id: RegionalOutcome.ACCEPTED}
            )

    def test_failed_recovery_rejects_acceptance_without_partial_raw(
        self,
    ) -> None:
        capture = gangwon_recovery_capture()
        item = capture["items"][0]
        external_id = item["external_id"]
        item["detail"].update(
            {
                "organization": "강원특별자치도 청년정책과",
                "source_region": "강원특별자치도",
                "eligibility": "강원특별자치도 거주 청년",
                "age": "만 19세 ~ 39세",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_root = root / "raw"
            checkpoint_root = root / "checkpoints"
            checkpoint = RegionalBatchCheckpoint.initial(
                GANGWON_SOURCE_ID
            ).discover(
                page=1,
                external_ids=(external_id,),
                total_count=1,
                has_next=False,
            ).decide({external_id: RegionalOutcome.FAILED})
            store = RegionalCheckpointStore(checkpoint_root)
            store.save(checkpoint)

            with self.assertRaisesRegex(
                ValueError, "duplicate baseline review"
            ):
                _store_recovery(
                    capture,
                    raw_root=raw_root,
                    checkpoint_root=checkpoint_root,
                )

            remaining_raw = (
                tuple(path for path in raw_root.rglob("*") if path.is_file())
                if raw_root.exists()
                else ()
            )
            unchanged = store.load(GANGWON_SOURCE_ID)

        self.assertEqual((), remaining_raw)
        self.assertEqual(checkpoint, unchanged)

    def test_discovery_queue_allows_bounded_detail_decision_batches(self) -> None:
        discovered = RegionalBatchCheckpoint.initial(DAEGU_SOURCE_ID).discover(
            page=1,
            external_ids=("8366", "8345", "8318", "8301"),
            total_count=4,
            has_next=False,
        )
        first = discovered.capture(("8366", "8345", "8318")).decide(
            {
                "8366": RegionalOutcome.ACCEPTED,
                "8345": RegionalOutcome.REVIEW,
                "8318": RegionalOutcome.CLOSED,
            }
        )
        complete = first.capture(("8301",)).decide(
            {"8301": RegionalOutcome.DUPLICATE}
        )
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
