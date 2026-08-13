from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime, timezone

from collectors.base import CollectionOptions
from collectors.errors import ResponseParseError
from collectors.extracted import ExtractionError
from collectors.http import TransportResponse
from collectors.regional_pilot import (
    BUSAN_DETAIL_URL,
    BUSAN_LIST_URL,
    BUSAN_SOURCE_ID,
    SEOUL_SOURCE_ID,
    BusanYouthCollector,
    BusanYouthExtractor,
    SeoulBrowserCaptureStore,
    SeoulYouthExtractor,
    decide_representative_regional_policy,
)
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalityStatus,
)
from collectors.storage import RawDocumentStore
from collectors.runtime import replay_runtime_raw
from collectors.normalizer import Normalizer


NOW = datetime(2026, 8, 11, 5, tzinfo=timezone.utc)


class StubHttpClient:
    def __init__(self, responses: list[TransportResponse]) -> None:
        self.responses = iter(responses)
        self.calls: list[dict[str, object]] = []

    def get(self, **kwargs: object) -> TransportResponse:
        self.calls.append(kwargs)
        return next(self.responses)


def response(body: str) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        body=body.encode("utf-8"),
    )


BUSAN_LIST = """
<div class="total">총 <span class="blue">1</span>건</div>
<a href="/policySupport/view.nm?menuCd=13&bizSid=SUP0000003570">
 <div class="cd_state ing">모집중</div>
 <span class="card_cate">[교육분야]</span>
 <span class="card_tit">부산 청년 한국사 스터디</span>
 <div class="card_dptmt">부산광역시 사상구</div>
 <div class="period_num">2026-08-10 ~ 2026-08-20</div>
</a>
"""
BUSAN_DETAIL = """
<span class="dt_tit">부산 청년 한국사 스터디</span>
<span class="dtif_atc">신청기간</span>
<span class="dtif_cont">2026-08-10 ~ 2026-08-20</span>
<span class="dtif_atc">담당기관</span>
<span class="dtif_cont">부산광역시 사상구</span>
<span class="dtif_atc">지원대상</span>
<span class="dtif_cont">청년</span>
"""


class BusanPilotTests(unittest.TestCase):
    def test_collect_extract_and_hold_generic_target_for_review(self) -> None:
        client = StubHttpClient([response(BUSAN_LIST), response(BUSAN_DETAIL)])
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            result = BusanYouthCollector(
                http_client=client,
                store=store,
                now=lambda: NOW,
            ).collect(CollectionOptions(limit=1, detail_limit=1))
            policy = BusanYouthExtractor().extract(
                store.load(path) for path in result.stored_paths
            )[0]

        self.assertEqual(BUSAN_SOURCE_ID, result.source_id)
        self.assertEqual(3, result.raw_document_count)
        self.assertEqual(BUSAN_LIST_URL, client.calls[0]["url"])
        self.assertEqual(BUSAN_DETAIL_URL, client.calls[1]["url"])
        decision = decide_representative_regional_policy(
            policy, as_of=date(2026, 8, 11)
        )
        self.assertIs(
            RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
            decision.regionality,
        )
        self.assertIs(ApplicationAvailability.OPEN, decision.application)
        self.assertFalse(decision.accepted)

    def test_detail_identity_drift_stores_no_partial_raw(self) -> None:
        drifted = BUSAN_DETAIL.replace(
            "부산 청년 한국사 스터디", "다른 정책"
        )
        client = StubHttpClient([response(BUSAN_LIST), response(drifted)])
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ResponseParseError):
                BusanYouthCollector(
                    http_client=client,
                    store=RawDocumentStore(temp_dir),
                    now=lambda: NOW,
                ).collect(CollectionOptions(limit=1, detail_limit=1))
            self.assertEqual([], list(RawDocumentStore(temp_dir).root.rglob("*.json")))

    def test_operational_page_uses_the_official_recruiting_filter(self) -> None:
        client = StubHttpClient([response(BUSAN_LIST)])
        with tempfile.TemporaryDirectory() as temp_dir:
            result = BusanYouthCollector(
                http_client=client,
                store=RawDocumentStore(temp_dir),
                now=lambda: NOW,
            ).collect(
                CollectionOptions(page=2, limit=12, detail_limit=0)
            )

        self.assertEqual(2, result.page)
        self.assertEqual(
            {"menuCd": "12", "endstat": "Y", "pageIndex": "2"},
            client.calls[0]["query"],
        )


class SeoulBrowserPilotTests(unittest.TestCase):
    def capture(self) -> dict[str, object]:
        return {
            "source_id": SEOUL_SOURCE_ID,
            "list_url": (
                "https://youth.seoul.go.kr/infoData/plcyInfo/list.do"
                "?key=2309150002"
            ),
            "action_trace": ["home", "서울시 정책", "detail"],
            "items": [
                {
                    "external_id": "20260804005400213319",
                    "title": "은평 청년 버스킹 페스타",
                    "summary": "서울 청년의 지역 활동 참여 지원",
                    "category": "참여.권리",
                    "detail_url": (
                        "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"
                        "?key=2309150002&plcyBizId=20260804005400213319"
                    ),
                    "detail": {
                        "title": "은평 청년 버스킹 페스타",
                        "organization": "서울특별시 은평구",
                        "category": "참여.권리",
                        "application_period": "2026-07-27 ~ 2026-08-14",
                        "source_region": "서울특별시 은평구",
                        "eligibility": "서울특별시 은평구 청년",
                        "support_content": "청년 버스킹 경연 및 시상",
                        "application_method": "https://docs.google.com/forms/",
                        "contact": None,
                        "required_documents": "신청서, 공연 영상",
                        "exclusions": None,
                        "age": "만 19세 ~ 만 39세",
                    },
                }
            ],
        }
    def test_capture_is_replayable_and_open_regional_policy_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            first = SeoulBrowserCaptureStore(
                store=store, now=lambda: NOW
            ).save(self.capture())
            policy = SeoulYouthExtractor().extract(
                store.load(path) for path in first.stored_paths
            )[0]
            replay_one = replay_runtime_raw(
                raw_root=temp_dir,
                source_id=SEOUL_SOURCE_ID,
                limit=1,
            )
            replay_two = replay_runtime_raw(
                raw_root=temp_dir,
                source_id=SEOUL_SOURCE_ID,
                limit=1,
            )

        decision = decide_representative_regional_policy(
            policy, as_of=date(2026, 8, 11)
        )
        self.assertEqual(3, first.raw_document_count)
        self.assertIs(RegionalityStatus.REGIONAL_CONFIRMED, decision.regionality)
        self.assertIs(ApplicationAvailability.OPEN, decision.application)
        self.assertTrue(decision.accepted)
        self.assertEqual("신청서, 공연 영상", policy.extra["required_documents"])
        normalized = Normalizer().normalize(policy).program
        assert normalized is not None
        self.assertEqual(
            ["신청서, 공연 영상"],
            [item.text for item in normalized.eligibility_summary.documents],
        )
        self.assertEqual(replay_one.programs, replay_two.programs)
        self.assertEqual(
            replay_one.regional_decisions,
            replay_two.regional_decisions,
        )

    def test_capture_rejects_detail_identity_drift(self) -> None:
        capture = deepcopy(self.capture())
        items = capture["items"]
        assert isinstance(items, list)
        items[0]["detail_url"] = (
            "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"
            "?key=2309150002&plcyBizId=WRONG"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExtractionError):
                SeoulBrowserCaptureStore(
                    store=RawDocumentStore(temp_dir), now=lambda: NOW
                ).save(capture)

    def test_capture_rejects_lookalike_detail_host(self) -> None:
        capture = deepcopy(self.capture())
        items = capture["items"]
        assert isinstance(items, list)
        items[0]["detail_url"] = (
            "https://youth.seoul.go.kr.invalid/infoData/plcyInfo/view.do"
            "?key=2309150002&plcyBizId=20260804005400213319"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExtractionError):
                SeoulBrowserCaptureStore(
                    store=RawDocumentStore(temp_dir), now=lambda: NOW
                ).save(capture)


if __name__ == "__main__":
    unittest.main()
