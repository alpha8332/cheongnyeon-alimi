from __future__ import annotations

import unittest
import urllib.parse
import tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from collectors.extracted import ExtractionError
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
    KOSAF_LIST_URL,
    KOSAF_SOURCE_ID,
    LH_LIST_URL,
    LH_SOURCE_ID,
    WORK24_LIST_URL,
    WORK24_SOURCE_ID,
    SupplementalOfficialExtractor,
    SupplementalOutcome,
    decide_supplemental_policy,
    discover_supplemental_list_items,
    map_supplemental_duplicate_evidence,
)
from collectors.runtime import replay_runtime_raw
from collectors.storage import RawDocumentStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "data/fixtures/html"
COLLECTED_AT = datetime(2026, 8, 17, 2, 30, tzinfo=timezone.utc)
LIST_URLS = {
    WORK24_SOURCE_ID: WORK24_LIST_URL,
    LH_SOURCE_ID: LH_LIST_URL,
    KOSAF_SOURCE_ID: KOSAF_LIST_URL,
    KINFA_SOURCE_ID: KINFA_LIST_URL,
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


class SupplementalListAdapterTests(unittest.TestCase):
    def test_discovers_each_approved_stable_identity(self) -> None:
        expected = {
            WORK24_SOURCE_ID: ("SI00000318",),
            LH_SOURCE_ID: ("2015122300020572",),
            KOSAF_SOURCE_ID: ("scholarship05_04_01",),
            KINFA_SOURCE_ID: ("hessalLoanYoos", "youngFutureLinkLoan"),
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
    def test_extracts_four_source_specific_details_without_leaking_fields(self) -> None:
        expected = {
            WORK24_SOURCE_ID: ("SI00000318", "고용노동부·한국고용정보원"),
            LH_SOURCE_ID: ("2015122300020572", "한국토지주택공사"),
            KOSAF_SOURCE_ID: ("scholarship05_04_01", "한국장학재단"),
            KINFA_SOURCE_ID: ("hessalLoanYoos", "서민금융진흥원"),
        }
        for source_id, (external_id, organization) in expected.items():
            detail_name = (
                "detail_closed.html"
                if source_id == LH_SOURCE_ID
                else "detail_normal.html"
            )
            with self.subTest(source_id=source_id):
                policy = SupplementalOfficialExtractor(source_id).extract(
                    documents(source_id, detail_name=detail_name)
                )[0]
                self.assertEqual(external_id, policy.external_id)
                self.assertEqual(organization, policy.organization)
                self.assertEqual(3, len(policy.provenance))
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
        for source_id in (WORK24_SOURCE_ID, KOSAF_SOURCE_ID, KINFA_SOURCE_ID):
            with self.subTest(source_id=source_id):
                policy = SupplementalOfficialExtractor(source_id).extract(
                    documents(source_id)
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
