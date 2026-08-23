from __future__ import annotations

import unittest
import urllib.parse
import tempfile
from typing import Any
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from collectors.extracted import ExtractionError
from collectors import default_registry
from collectors.base import CollectionOptions
from collectors.errors import CollectorConfigurationError, ResponseParseError
from collectors.cross_source_duplicate import (
    AggregatorBaseline,
    BaselineDescriptor,
    BaselineRecord,
    PolicyIdentity,
)
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.supplemental_official import (
    ADAPTER_VERSION,
    KINFA_LIST_URL,
    KINFA_SOURCE_ID,
    KPASS_LIST_URL,
    KPASS_SOURCE_ID,
    KOSAF_LIST_URL,
    KOSAF_SOURCE_ID,
    LH_LIST_URL,
    LH_SOURCE_ID,
    WORK24_LIST_URL,
    WORK24_SOURCE_ID,
    SupplementalOfficialExtractor,
    SupplementalOfficialCollector,
    SupplementalOutcome,
    decide_supplemental_policy,
    discover_supplemental_list_items,
    map_supplemental_duplicate_evidence,
    supplemental_http_config_from_environment,
)
from collectors.http import TransportResponse
from collectors.runtime import replay_runtime_raw
from collectors.snapshot import SnapshotManifest, SnapshotManifestStore
from collectors.normalized import Category
from collectors.normalizer import Normalizer
from collectors.storage import RawDocumentStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "data/fixtures/html"
COLLECTED_AT = datetime(2026, 8, 17, 2, 30, tzinfo=timezone.utc)
LIST_URLS = {
    WORK24_SOURCE_ID: WORK24_LIST_URL,
    LH_SOURCE_ID: LH_LIST_URL,
    KOSAF_SOURCE_ID: KOSAF_LIST_URL,
    KINFA_SOURCE_ID: KINFA_LIST_URL,
    KPASS_SOURCE_ID: KPASS_LIST_URL,
}


def fixture(source_id: str, name: str) -> bytes:
    return (FIXTURE_ROOT / source_id / name).read_bytes()


def raw(
    source_id: str,
    number: int,
    role: RawDocumentRole,
    payload: bytes,
    source_url: str,
    *,
    external_id: str | None = None,
    parent_document_id: str | None = None,
) -> RawPolicyDocument:
    parsed_url = urllib.parse.urlsplit(source_url)
    raw_source_url = urllib.parse.urlunsplit(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "")
    )
    return RawPolicyDocument.from_bytes(
        source_id=source_id,
        source_type=SourceType.WEB,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=raw_source_url,
        collected_at=COLLECTED_AT + timedelta(minutes=number),
        content_type=(
            "application/json; charset=utf-8"
            if role is RawDocumentRole.LIST_ITEM
            else "text/html; charset=utf-8"
        ),
        raw_format=(
            RawFormat.JSON
            if role is RawDocumentRole.LIST_ITEM
            else RawFormat.HTML
        ),
        raw_payload=payload,
        http_status=200,
        collector_version=ADAPTER_VERSION,
        document_id=f"{number:032x}",
    )


def documents(
    source_id: str,
    *,
    detail_name: str = "detail_normal.html",
    item_index: int = 0,
    include_detail: bool = True,
) -> tuple[RawPolicyDocument, ...]:
    list_payload = fixture(source_id, "list_normal.html")
    item = discover_supplemental_list_items(source_id, list_payload)[item_index]
    response = raw(
        source_id,
        1,
        RawDocumentRole.LIST_RESPONSE,
        list_payload,
        LIST_URLS[source_id],
    )
    list_item = raw(
        source_id,
        2,
        RawDocumentRole.LIST_ITEM,
        item.to_payload(),
        LIST_URLS[source_id],
        external_id=item.external_id,
        parent_document_id=response.document_id,
    )
    if not include_detail:
        return response, list_item
    detail = raw(
        source_id,
        3,
        RawDocumentRole.DETAIL_RESPONSE,
        fixture(source_id, detail_name),
        item.canonical_url,
        external_id=item.external_id,
    )
    return response, list_item, detail


def kpass_documents() -> tuple[RawPolicyDocument, ...]:
    source_id = KPASS_SOURCE_ID
    list_payload = fixture(source_id, "list_normal.html")
    item = discover_supplemental_list_items(source_id, list_payload)[0]
    list_response = raw(
        source_id,
        1,
        RawDocumentRole.LIST_RESPONSE,
        list_payload,
        KPASS_LIST_URL,
    )
    list_item = raw(
        source_id,
        2,
        RawDocumentRole.LIST_ITEM,
        item.to_payload(),
        KPASS_LIST_URL,
        external_id=item.external_id,
        parent_document_id=list_response.document_id,
    )
    intro = raw(
        source_id,
        3,
        RawDocumentRole.DETAIL_RESPONSE,
        fixture(source_id, "detail_intro.html"),
        item.canonical_url,
        external_id=item.external_id,
    )
    join = raw(
        source_id,
        4,
        RawDocumentRole.DETAIL_RESPONSE,
        fixture(source_id, "detail_join.html"),
        "https://korea-pass.kr/info/use_join.do",
        external_id=item.external_id,
    )
    return list_response, list_item, intro, join


def duplicate_baseline(canonical_url: str) -> AggregatorBaseline:
    descriptors = tuple(
        BaselineDescriptor(
            source_id=source_id,
            snapshot_id=f"{number:032x}",
            snapshot_collected_at=COLLECTED_AT,
            snapshot_policy_count=1,
            database_checked_at=COLLECTED_AT,
            database_policy_count=1,
        )
        for number, source_id in enumerate(
            ("bokjiro-central-welfare-api", "youthcenter-api"),
            start=20,
        )
    )
    records = (
        BaselineRecord(
            identity=PolicyIdentity("bokjiro-central-welfare-api", "BOK-1"),
            title="기존 집계 정책",
            organization="기존 기관",
            canonical_region_keys=(),
            application_start=None,
            application_end=None,
            support_content=None,
            canonical_urls=(canonical_url,),
        ),
        BaselineRecord(
            identity=PolicyIdentity("youthcenter-api", "YOUTH-1"),
            title="다른 집계 정책",
            organization="다른 기관",
            canonical_region_keys=(),
            application_start=None,
            application_end=None,
            support_content=None,
            canonical_urls=("https://example.org/unrelated",),
        ),
    )
    return AggregatorBaseline(descriptors=descriptors, records=records)


def response(body: bytes) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        body=body,
    )


class StubHttpClient:
    def __init__(self, outcomes: list[TransportResponse]) -> None:
        self._outcomes = iter(outcomes)
        self.calls: list[dict[str, Any]] = []

    def get(self, **kwargs: Any) -> TransportResponse:
        self.calls.append(kwargs)
        return next(self._outcomes)


class SupplementalCollectorTests(unittest.TestCase):
    def test_registry_includes_all_approved_sources(self) -> None:
        self.assertTrue(
            {
                WORK24_SOURCE_ID,
                LH_SOURCE_ID,
                KOSAF_SOURCE_ID,
                KINFA_SOURCE_ID,
                KPASS_SOURCE_ID,
            }.issubset(default_registry.source_ids())
        )

    def test_http_config_enforces_two_second_floor(self) -> None:
        minimum = supplemental_http_config_from_environment(
            environ={"HTTP_REQUEST_DELAY_SECONDS": "0.25"}
        )
        larger = supplemental_http_config_from_environment(
            environ={"HTTP_REQUEST_DELAY_SECONDS": "3.5"}
        )

        self.assertEqual(2.0, minimum.request_interval_seconds)
        self.assertEqual(3.5, larger.request_interval_seconds)

    def test_collects_bounded_list_items_and_details(self) -> None:
        client = StubHttpClient(
            [
                response(fixture(KINFA_SOURCE_ID, "list_normal.html")),
                response(fixture(KINFA_SOURCE_ID, "detail_normal.html")),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            result = SupplementalOfficialCollector(
                KINFA_SOURCE_ID,
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            ).collect(CollectionOptions(limit=2, detail_limit=1))
            selected = tuple(store.load(path) for path in result.stored_paths)

        self.assertEqual(2, result.request_count)
        self.assertEqual(2, result.item_count)
        self.assertEqual(1, result.detail_count)
        self.assertEqual(4, result.raw_document_count)
        self.assertEqual(1, len(tuple(
            document for document in selected
            if document.document_role is RawDocumentRole.DETAIL_RESPONSE
        )))
        self.assertTrue(all("?" not in document.source_url for document in selected))

    def test_kosaf_uses_three_tabs_for_one_stable_identity(self) -> None:
        client = StubHttpClient(
            [
                response(fixture(KOSAF_SOURCE_ID, "list_normal.html")),
                response(fixture(KOSAF_SOURCE_ID, "detail_normal.html")),
                response(fixture(KOSAF_SOURCE_ID, "detail_normal.html")),
                response(fixture(KOSAF_SOURCE_ID, "detail_normal.html")),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = SupplementalOfficialCollector(
                KOSAF_SOURCE_ID,
                http_client=client,
                store=RawDocumentStore(temporary_directory),
                now=lambda: COLLECTED_AT,
            ).collect(CollectionOptions(limit=10, detail_limit=3))

        self.assertEqual(4, result.request_count)
        self.assertEqual(3, result.detail_count)
        self.assertEqual(3, len(set(result.detail_document_ids)))
        self.assertEqual(
            [None, None, "3", "4"],
            [call["query"].get("ttab1") for call in client.calls],
        )

    def test_kpass_uses_intro_and_join_conditions_for_one_identity(self) -> None:
        client = StubHttpClient(
            [
                response(fixture(KPASS_SOURCE_ID, "list_normal.html")),
                response(fixture(KPASS_SOURCE_ID, "detail_intro.html")),
                response(fixture(KPASS_SOURCE_ID, "detail_join.html")),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            result = SupplementalOfficialCollector(
                KPASS_SOURCE_ID,
                http_client=client,
                store=store,
                now=lambda: COLLECTED_AT,
            ).collect(CollectionOptions(limit=1, detail_limit=2))
            selected = tuple(store.load(path) for path in result.stored_paths)

        self.assertEqual(3, result.request_count)
        self.assertEqual(1, result.item_count)
        self.assertEqual(2, result.detail_count)
        self.assertEqual(
            {
                "https://korea-pass.kr/info/intro.do",
                "https://korea-pass.kr/info/use_join.do",
            },
            {
                document.source_url
                for document in selected
                if document.document_role is RawDocumentRole.DETAIL_RESPONSE
            },
        )

    def test_rejects_page_or_detail_expansion_before_request(self) -> None:
        client = StubHttpClient([])
        collector = SupplementalOfficialCollector(
            WORK24_SOURCE_ID,
            http_client=client,
        )
        with self.assertRaises(CollectorConfigurationError):
            collector.collect(CollectionOptions(page=2))
        with self.assertRaises(CollectorConfigurationError):
            collector.collect(CollectionOptions(detail_limit=4))
        self.assertEqual([], client.calls)

    def test_selector_drift_stores_no_partial_raw(self) -> None:
        client = StubHttpClient(
            [
                response(fixture(KINFA_SOURCE_ID, "list_normal.html")),
                response(
                    fixture(KINFA_SOURCE_ID, "detail_selector_drift.html")
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ResponseParseError):
                SupplementalOfficialCollector(
                    KINFA_SOURCE_ID,
                    http_client=client,
                    store=RawDocumentStore(temporary_directory),
                    now=lambda: COLLECTED_AT,
                ).collect(CollectionOptions(limit=2, detail_limit=1))
            self.assertEqual(
                [],
                list(Path(temporary_directory).rglob("*.json")),
            )


class SupplementalListAdapterTests(unittest.TestCase):
    def test_discovers_each_approved_stable_identity(self) -> None:
        expected = {
            WORK24_SOURCE_ID: ("SI00000318",),
            LH_SOURCE_ID: ("2015122300020572",),
            KOSAF_SOURCE_ID: ("scholarship05_04_01",),
            KINFA_SOURCE_ID: ("hessalLoanYoos", "youngFutureLinkLoan"),
            KPASS_SOURCE_ID: ("intro",),
        }
        for source_id, identities in expected.items():
            with self.subTest(source_id=source_id):
                items = discover_supplemental_list_items(
                    source_id, fixture(source_id, "list_normal.html")
                )
                self.assertEqual(
                    identities,
                    tuple(item.external_id for item in items),
                )
                self.assertEqual(
                    len(identities),
                    len({item.canonical_url for item in items}),
                )

    def test_list_replay_is_deterministic(self) -> None:
        payload = fixture(WORK24_SOURCE_ID, "list_normal.html")
        first = discover_supplemental_list_items(WORK24_SOURCE_ID, payload)
        second = discover_supplemental_list_items(WORK24_SOURCE_ID, payload)
        self.assertEqual(first, second)
        self.assertEqual(first[0].to_payload(), second[0].to_payload())

    def test_selector_drift_is_not_treated_as_an_empty_list(self) -> None:
        with self.assertRaisesRegex(ExtractionError, "selector drift"):
            discover_supplemental_list_items(
                WORK24_SOURCE_ID,
                fixture(WORK24_SOURCE_ID, "list_selector_drift.html"),
            )


class SupplementalExtractorTests(unittest.TestCase):
    def test_kosaf_scholarship_maps_to_education_category(self) -> None:
        policy = SupplementalOfficialExtractor(KOSAF_SOURCE_ID).extract(
            documents(KOSAF_SOURCE_ID)
        )[0]
        result = Normalizer().normalize(policy)

        self.assertIsNotNone(result.program)
        assert result.program is not None
        self.assertEqual((Category.EDUCATION,), result.program.categories)

    def test_extracts_five_source_specific_details_without_leaking_fields(self) -> None:
        expected = {
            WORK24_SOURCE_ID: ("SI00000318", "고용노동부·한국고용정보원"),
            LH_SOURCE_ID: ("2015122300020572", "한국토지주택공사"),
            KOSAF_SOURCE_ID: ("scholarship05_04_01", "한국장학재단"),
            KINFA_SOURCE_ID: ("hessalLoanYoos", "서민금융진흥원"),
            KPASS_SOURCE_ID: (
                "intro",
                "국토교통부 대도시권광역위원회·한국교통안전공단·전국 지자체",
            ),
        }
        for source_id, (external_id, organization) in expected.items():
            detail_name = (
                "detail_closed.html"
                if source_id == LH_SOURCE_ID
                else "detail_normal.html"
            )
            with self.subTest(source_id=source_id):
                selected = (
                    kpass_documents()
                    if source_id == KPASS_SOURCE_ID
                    else documents(source_id, detail_name=detail_name)
                )
                policy = SupplementalOfficialExtractor(source_id).extract(
                    selected
                )[0]
                self.assertEqual(external_id, policy.external_id)
                self.assertEqual(organization, policy.organization)
                self.assertEqual(
                    4 if source_id == KPASS_SOURCE_ID else 3,
                    len(policy.provenance),
                )
                self.assertIn("field_locators", policy.extra)
                self.assertNotIn("panId", policy.to_dict())
                self.assertNotIn("systId", policy.to_dict())

    def test_same_raw_replay_produces_the_same_extracted_policy(self) -> None:
        selected = documents(WORK24_SOURCE_ID)
        extractor = SupplementalOfficialExtractor(WORK24_SOURCE_ID)
        first = extractor.extract(selected)[0].to_dict()
        second = extractor.extract(selected)[0].to_dict()
        self.assertEqual(first, second)
        self.assertEqual(
            selected[2].raw_bytes,
            fixture(WORK24_SOURCE_ID, "detail_normal.html"),
        )
        self.assertTrue(selected[2].content_hash.startswith("sha256:"))

    def test_missing_detail_fails_the_replay_instead_of_importing_list_text(
        self,
    ) -> None:
        with self.assertRaisesRegex(ExtractionError, "incomplete"):
            SupplementalOfficialExtractor(WORK24_SOURCE_ID).extract(
                documents(WORK24_SOURCE_ID, include_detail=False)
            )

    def test_detail_title_drift_fails_closed(self) -> None:
        with self.assertRaisesRegex(ExtractionError, "title drift"):
            SupplementalOfficialExtractor(KINFA_SOURCE_ID).extract(
                documents(
                    KINFA_SOURCE_ID,
                    detail_name="detail_selector_drift.html",
                )
            )


class SupplementalGateTests(unittest.TestCase):
    def test_accepts_only_complete_open_official_evidence(self) -> None:
        for source_id in (
            WORK24_SOURCE_ID,
            KOSAF_SOURCE_ID,
            KINFA_SOURCE_ID,
            KPASS_SOURCE_ID,
        ):
            with self.subTest(source_id=source_id):
                selected = (
                    kpass_documents()
                    if source_id == KPASS_SOURCE_ID
                    else documents(source_id)
                )
                policy = SupplementalOfficialExtractor(source_id).extract(
                    selected
                )[0]
                decision = decide_supplemental_policy(
                    policy, as_of=date(2026, 8, 17)
                )
                self.assertIs(SupplementalOutcome.ACCEPTED, decision.outcome)
                self.assertIs(policy, decision.accepted_policy)

    def test_closed_lh_announcement_has_no_accepted_policy(self) -> None:
        policy = SupplementalOfficialExtractor(LH_SOURCE_ID).extract(
            documents(LH_SOURCE_ID, detail_name="detail_closed.html")
        )[0]
        decision = decide_supplemental_policy(policy, as_of=date(2026, 8, 17))
        self.assertIs(SupplementalOutcome.CLOSED, decision.outcome)
        self.assertIsNone(decision.accepted_policy)

    def test_missing_required_documents_goes_to_review(self) -> None:
        policy = SupplementalOfficialExtractor(KOSAF_SOURCE_ID).extract(
            documents(
                KOSAF_SOURCE_ID,
                detail_name="detail_missing_evidence.html",
            )
        )[0]
        decision = decide_supplemental_policy(policy, as_of=date(2026, 8, 17))
        self.assertIs(SupplementalOutcome.REVIEW, decision.outcome)
        self.assertIn("required_documents_unconfirmed", decision.reason_codes)
        self.assertIsNone(decision.accepted_policy)

    def test_evidence_contract_failure_is_separate_from_review(self) -> None:
        policy = SupplementalOfficialExtractor(WORK24_SOURCE_ID).extract(
            documents(WORK24_SOURCE_ID)
        )[0]
        failed = decide_supplemental_policy(
            replace(policy, extra={}), as_of=date(2026, 8, 17)
        )
        self.assertIs(SupplementalOutcome.FAILED, failed.outcome)
        self.assertIsNone(failed.accepted_policy)

    def test_duplicate_evidence_uses_only_canonical_url_and_raw_provenance(
        self,
    ) -> None:
        policy = SupplementalOfficialExtractor(WORK24_SOURCE_ID).extract(
            documents(WORK24_SOURCE_ID)
        )[0]
        evidence = map_supplemental_duplicate_evidence(policy)
        self.assertEqual((policy.source_url,), evidence.canonical_urls)
        self.assertEqual(policy.provenance, evidence.provenance)
        self.assertEqual(
            {"canonical_urls": "detail_response:canonical_url"},
            dict(evidence.field_locators),
        )

    def test_runtime_keeps_gate_and_duplicate_outcomes_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            for document in documents(WORK24_SOURCE_ID):
                store.save(document)
            result = replay_runtime_raw(
                raw_root=temporary_directory,
                source_id=WORK24_SOURCE_ID,
                limit=10,
            )

        self.assertEqual("accepted", result.supplemental_decisions[0]["outcome"])
        self.assertEqual(
            "duplicate_review_required",
            result.duplicate_decisions[0]["outcome"],
        )
        self.assertEqual(0, result.accepted_count)

    def test_runtime_excludes_exact_aggregator_url_duplicate(self) -> None:
        selected = documents(WORK24_SOURCE_ID)
        candidate_url = SupplementalOfficialExtractor(WORK24_SOURCE_ID).extract(
            selected
        )[0].source_url
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            for document in selected:
                store.save(document)
            result = replay_runtime_raw(
                raw_root=temporary_directory,
                source_id=WORK24_SOURCE_ID,
                limit=10,
                duplicate_baseline=duplicate_baseline(candidate_url),
            )

        self.assertEqual(
            "excluded_aggregator_duplicate",
            result.duplicate_decisions[0]["outcome"],
        )
        self.assertEqual(
            ["canonical_url"],
            result.duplicate_decisions[0]["match_fields"],
        )
        self.assertEqual(0, result.accepted_count)

    def test_runtime_reviews_kpass_material_title_containment(self) -> None:
        selected = kpass_documents()
        baseline = duplicate_baseline("https://example.org/unrelated-kpass")
        baseline = replace(
            baseline,
            records=(
                replace(
                    baseline.records[0],
                    title="대중교통비 환급 지원(모두의카드)",
                    canonical_urls=("https://www.bokjiro.go.kr/program",),
                ),
                baseline.records[1],
            ),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            for document in selected:
                store.save(document)
            SnapshotManifestStore(temporary_directory).save(
                SnapshotManifest(
                    snapshot_id="f" * 32,
                    source_id=KPASS_SOURCE_ID,
                    started_at=COLLECTED_AT,
                    completed_at=COLLECTED_AT + timedelta(minutes=4),
                    page_size=1,
                    detail_limit=2,
                    request_budget=3,
                    request_count=3,
                    total_count=1,
                    item_count=1,
                    list_response_document_ids=(selected[0].document_id,),
                    detail_document_ids=(
                        selected[2].document_id,
                        selected[3].document_id,
                    ),
                )
            )
            result = replay_runtime_raw(
                raw_root=temporary_directory,
                source_id=KPASS_SOURCE_ID,
                limit=10,
                duplicate_baseline=baseline,
            )

        self.assertEqual("accepted", result.supplemental_decisions[0]["outcome"])
        self.assertEqual(
            "duplicate_review_required",
            result.duplicate_decisions[0]["outcome"],
        )
        self.assertEqual(
            ["material_title_containment_requires_review"],
            result.duplicate_decisions[0]["reason_codes"],
        )
        self.assertEqual(0, result.accepted_count)

    def test_runtime_closed_outcome_never_reaches_normalizer_or_duplicate_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            for document in documents(
                LH_SOURCE_ID, detail_name="detail_closed.html"
            ):
                store.save(document)
            result = replay_runtime_raw(
                raw_root=temporary_directory,
                source_id=LH_SOURCE_ID,
                limit=10,
            )

        self.assertEqual("closed", result.supplemental_decisions[0]["outcome"])
        self.assertEqual((), result.duplicate_decisions)
        self.assertEqual(0, result.accepted_count)


if __name__ == "__main__":
    unittest.main()
