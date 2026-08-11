from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from collectors import default_registry
from collectors.base import CollectionOptions
from collectors.errors import CollectorConfigurationError, ResponseParseError
from collectors.cross_source_duplicate import (
    AggregatorBaseline,
    BaselineDescriptor,
    BaselineRecord,
    PolicyIdentity,
)
from collectors.extracted import ExtractionError
from collectors.gyeongbuk_youth import (
    DETAIL_MODAL_URL,
    HOME_URL,
    LIST_FORM,
    LIST_JSON_URL,
    SOURCE_ID,
    GyeongbukYouthCollector,
    GyeongbukYouthExtractor,
    decide_gyeongbuk_regional_policy,
    _prioritize_regional_items,
    _canonicalize_gyeongbuk_evidence,
)
from collectors.http import TransportResponse
from collectors.normalizer import Normalizer
from collectors.normalized import CoverageScope
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.regional_profile import (
    load_approved_regional_profile,
    replay_profile_actions,
)
from collectors.runtime import replay_runtime_raw
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalityStatus,
)
from collectors.storage import RawDocumentStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "data/fixtures/regional/gyeongbuk"
COLLECTED_AT = datetime(2026, 8, 11, 5, 30, tzinfo=timezone.utc)


def fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def response(body: bytes, content_type: str) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": content_type},
        body=body,
    )


class StubHttpClient:
    def __init__(self, outcomes: list[TransportResponse | BaseException]):
        self._outcomes = iter(outcomes)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(("get", kwargs))
        return self._outcome()

    def post_form(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(("post_form", kwargs))
        return self._outcome()

    def _outcome(self) -> TransportResponse:
        value = next(self._outcomes)
        if isinstance(value, BaseException):
            raise value
        return value


def raw_document(
    *,
    number: int,
    role: RawDocumentRole,
    payload: bytes,
    raw_format: RawFormat,
    source_url: str,
    external_id: str | None = None,
    parent_document_id: str | None = None,
    collected_at: datetime = COLLECTED_AT,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        document_id=f"{number:032x}",
        source_id=SOURCE_ID,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=source_url,
        collected_at=collected_at,
        content_type=(
            "application/json; charset=utf-8"
            if raw_format is RawFormat.JSON
            else "text/html; charset=utf-8"
        ),
        raw_format=raw_format,
        raw_payload=payload,
        http_status=200,
        collector_version="test/1.0",
    )


def extraction_documents(
    detail_name: str = "detail_1098.html",
) -> tuple[RawPolicyDocument, ...]:
    list_payload = json.loads(fixture("list_response.json"))
    item_payload = json.dumps(
        list_payload["resultList1"][0],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    parent = raw_document(
        number=1,
        role=RawDocumentRole.LIST_RESPONSE,
        payload=fixture("list_response.json"),
        raw_format=RawFormat.JSON,
        source_url=LIST_JSON_URL,
    )
    item = raw_document(
        number=2,
        role=RawDocumentRole.LIST_ITEM,
        payload=item_payload,
        raw_format=RawFormat.JSON,
        source_url=LIST_JSON_URL,
        external_id="1098",
        parent_document_id=parent.document_id,
    )
    detail = raw_document(
        number=3,
        role=RawDocumentRole.DETAIL_RESPONSE,
        payload=fixture(detail_name),
        raw_format=RawFormat.HTML,
        source_url=DETAIL_MODAL_URL,
        external_id="1098",
        collected_at=COLLECTED_AT + timedelta(minutes=1),
    )
    return parent, item, detail


class GyeongbukProfileTests(unittest.TestCase):
    def test_profile_loads_and_replays_repository_action_contract(self) -> None:
        profile = load_approved_regional_profile(SOURCE_ID)

        replayed = replay_profile_actions(
            profile,
            [
                {
                    "kind": action.kind,
                    "target": action.target,
                    "value": action.value,
                }
                for action in profile.actions
            ],
        )

        self.assertEqual("http_json", profile.collection_mode)
        self.assertEqual((LIST_JSON_URL,), profile.approved_list_urls)
        self.assertEqual("1098", profile.sample_external_id)
        self.assertEqual(len(profile.actions), len(replayed))

    def test_detail_candidates_prefer_agreeing_regional_evidence(self) -> None:
        items = (
            {
                "no": "1",
                "rgnSeNm": "경상북도",
                "sprvsnInstNm": "경상북도",
                "policyScl": "청년",
            },
            {
                "no": "2",
                "rgnSeNm": "포항시",
                "sprvsnInstNm": "포항시",
                "policyScl": "포항시 거주 청년",
            },
        )

        selected = _prioritize_regional_items(items)

        self.assertEqual(["2", "1"], [item["no"] for item in selected])

    def test_official_gyeongbuk_address_shorthand_is_canonicalized(self) -> None:
        self.assertEqual(
            "경상북도 주소를 둔 미취업 청년",
            _canonicalize_gyeongbuk_evidence("경북 주소를 둔 미취업 청년"),
        )


class GyeongbukCollectorTests(unittest.TestCase):
    def test_registry_includes_gyeongbuk_profile_collector(self) -> None:
        self.assertIn(SOURCE_ID, default_registry.source_ids())

    def test_collects_approved_json_and_modal_with_csrf_contract(self) -> None:
        client = StubHttpClient(
            [
                response(fixture("home.html"), "text/html; charset=utf-8"),
                response(
                    fixture("list_response.json"),
                    "application/json; charset=utf-8",
                ),
                response(
                    fixture("detail_1098.html"),
                    "text/html; charset=utf-8",
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            result = GyeongbukYouthCollector(
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            ).collect(CollectionOptions(limit=1, detail_limit=1))
            documents = tuple(store.load(path) for path in result.stored_paths)

        self.assertEqual(3, result.request_count)
        self.assertEqual(1, result.item_count)
        self.assertEqual(1, result.detail_count)
        self.assertEqual(243, result.total_count)
        self.assertEqual(("1098",), result.external_ids)
        self.assertEqual(3, result.raw_document_count)
        self.assertEqual(
            [
                ("get", HOME_URL),
                ("post_form", LIST_JSON_URL),
                ("post_form", DETAIL_MODAL_URL),
            ],
            [(method, values["url"]) for method, values in client.calls],
        )
        list_call = client.calls[1][1]
        self.assertEqual(LIST_FORM, list_call["form"])
        self.assertEqual(
            "fixture-csrf-token",
            list_call["headers"]["X-CSRF-TOKEN"],
        )
        self.assertEqual(
            [RawFormat.JSON, RawFormat.JSON, RawFormat.HTML],
            [document.raw_format for document in documents],
        )
        self.assertEqual(
            documents[0].document_id,
            documents[1].parent_document_id,
        )
        self.assertIsNone(documents[2].parent_document_id)

    def test_budget_and_page_are_rejected_before_request(self) -> None:
        for options in (
            CollectionOptions(page=2),
            CollectionOptions(detail_limit=4),
        ):
            with self.subTest(options=options):
                client = StubHttpClient([])
                with self.assertRaises(CollectorConfigurationError):
                    GyeongbukYouthCollector(http_client=client).collect(options)
                self.assertEqual([], client.calls)

    def test_detail_drift_stores_no_partial_raw(self) -> None:
        client = StubHttpClient(
            [
                response(fixture("home.html"), "text/html"),
                response(fixture("list_response.json"), "application/json"),
                response(fixture("detail_drift.html"), "text/html"),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ResponseParseError):
                GyeongbukYouthCollector(
                    http_client=client,
                    store=RawDocumentStore(temp_dir),
                    now=lambda: COLLECTED_AT,
                ).collect(CollectionOptions(limit=1, detail_limit=1))
            self.assertEqual([], list(Path(temp_dir).rglob("*.json")))


class GyeongbukExtractorTests(unittest.TestCase):
    def test_maps_json_and_detail_fields_without_regional_inference(self) -> None:
        policy = GyeongbukYouthExtractor().extract(extraction_documents())[0]

        self.assertEqual("1098", policy.external_id)
        self.assertEqual("2026 경북 청년 행복카드 지원사업", policy.title)
        self.assertEqual("(재)경상북도경제진흥원", policy.organization)
        self.assertEqual("복지", policy.category_text)
        self.assertEqual("경상북도", policy.region_text)
        self.assertEqual(
            "경상북도 거주 도내 중소기업 재직 청년 885명",
            policy.eligibility_text,
        )
        self.assertEqual("1인당 100만원 복지포인트 지원", policy.support_content)
        self.assertEqual(
            "054-470-8589", policy.extra["institutional_contact"]
        )
        self.assertEqual(3, len(policy.provenance))

        normalized = Normalizer().normalize(policy)
        self.assertIsNotNone(normalized.program)
        assert normalized.program is not None
        self.assertEqual("1098", normalized.program.external_id)

    def test_regional_gate_maps_actual_fixture_to_canonical_region(self) -> None:
        policy = GyeongbukYouthExtractor().extract(extraction_documents())[0]
        decision = decide_gyeongbuk_regional_policy(
            policy,
            as_of=date(2026, 6, 10),
        )

        self.assertIs(
            RegionalityStatus.REGIONAL_CONFIRMED,
            decision.regionality,
        )
        self.assertIs(ApplicationAvailability.OPEN, decision.application)
        assert decision.accepted_policy is not None
        normalized = Normalizer().normalize(decision.accepted_policy)
        self.assertIsNotNone(normalized.program)
        assert normalized.program is not None
        self.assertIs(CoverageScope.REGIONAL, normalized.program.coverage_scope)
        self.assertEqual("4700000000", normalized.program.region_rules[0].region_code)

    def test_raw_replay_is_network_free_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            for document in extraction_documents():
                store.save(document)
            first = replay_runtime_raw(
                raw_root=temp_dir,
                source_id=SOURCE_ID,
                limit=1,
            )
            second = replay_runtime_raw(
                raw_root=temp_dir,
                source_id=SOURCE_ID,
                limit=1,
            )

        self.assertEqual(first.programs, second.programs)
        self.assertEqual(first.regional_decisions, second.regional_decisions)
        self.assertEqual(1, first.extracted_count)
        self.assertEqual(0, first.accepted_count)
        self.assertEqual(1, first.regional_skipped_count)
        self.assertEqual("closed", first.regional_decisions[0]["application"])

    def test_open_policy_passes_cross_source_gate_with_baseline(self) -> None:
        checked_at = datetime(2026, 8, 11, tzinfo=timezone.utc)
        baseline = AggregatorBaseline(
            descriptors=tuple(
                BaselineDescriptor(
                    source_id=source_id,
                    snapshot_id=marker * 32,
                    snapshot_collected_at=checked_at,
                    snapshot_policy_count=1,
                    database_checked_at=checked_at,
                    database_policy_count=1,
                )
                for source_id, marker in (
                    ("youthcenter-api", "1"),
                    ("bokjiro-central-welfare-api", "2"),
                )
            ),
            records=tuple(
                BaselineRecord(
                    identity=PolicyIdentity(source_id, f"UNRELATED-{marker}"),
                    title=f"무관 정책 {marker}",
                    organization="중앙기관",
                    canonical_region_keys=(),
                    application_start=date(2026, 1, 1),
                    application_end=date(2026, 12, 31),
                    support_content="무관 지원",
                    canonical_urls=(
                        f"https://fixture.invalid/central/{marker}",
                    ),
                    database_row_id=int(marker),
                )
                for source_id, marker in (
                    ("youthcenter-api", "1"),
                    ("bokjiro-central-welfare-api", "2"),
                )
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RawDocumentStore(temp_dir)
            for document in extraction_documents():
                store.save(document)
            original = decide_gyeongbuk_regional_policy
            with patch(
                "collectors.runtime.decide_gyeongbuk_regional_policy",
                side_effect=lambda policy: original(
                    policy, as_of=date(2026, 6, 10)
                ),
            ):
                replay = replay_runtime_raw(
                    raw_root=temp_dir,
                    source_id=SOURCE_ID,
                    limit=1,
                    duplicate_baseline=baseline,
                )

        self.assertEqual(1, replay.accepted_count)
        self.assertEqual(0, replay.cross_source_skipped_count)
        self.assertEqual(
            "accepted_regional",
            replay.duplicate_decisions[0]["outcome"],
        )
        self.assertIsNotNone(replay.duplicate_manifest)
        self.assertEqual(
            baseline.baseline_id,
            replay.duplicate_baseline["baseline_id"],
        )

    def test_detail_drift_is_not_treated_as_empty_policy(self) -> None:
        with self.assertRaisesRegex(ExtractionError, "selector drift"):
            GyeongbukYouthExtractor().extract(
                extraction_documents("detail_drift.html")
            )


if __name__ == "__main__":
    unittest.main()
