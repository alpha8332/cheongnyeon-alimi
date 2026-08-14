from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from collectors.cross_source_duplicate import (
    AggregatorBaseline,
    AnnouncementIdentity,
    BaselineDescriptor,
    BaselineRecord,
    CrossSourceDecisionManifest,
    CrossSourceDecisionManifestStore,
    CrossSourceDuplicateError,
    DuplicateEvidence,
    PolicyIdentity,
    evaluate_cross_source_duplicate,
)
from collectors.normalized import NormalizedProgram


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads(
    (
        ROOT
        / "data"
        / "fixtures"
        / "regional"
        / "cross_source_duplicate_cases.json"
    ).read_text(encoding="utf-8")
)["cases"]
CHECKED_AT = datetime(2026, 8, 11, 6, tzinfo=timezone.utc)


def candidate_program(**changes) -> NormalizedProgram:
    value = json.loads(
        (ROOT / "data" / "fixtures" / "normalized" / "programs.json")
        .read_text(encoding="utf-8")
    )[0]
    value.update(
        {
            "source_id": "regional-gyeongbuk-youth-platform",
            "source_name": "경북청년포털 청년e끌림",
            "external_id": "regional-001",
            "title": "경북 청년 행복카드 지원사업",
            "organization": "경상북도경제진흥원",
            "application_start": "2026-06-01",
            "application_end": "2026-06-30",
            "application_status": "open",
            "region_text": "경상북도",
            "regions": ["경상북도"],
            "coverage_scope": "regional",
            "region_rules": [
                {
                    "relation": "include",
                    "resolution_status": "matched",
                    "region_scheme": "kr-bjd-20260803",
                    "region_code": "4700000000",
                    "source_code": None,
                    "source_text": "경상북도"
                }
            ],
            "support_content": "1인당 100만원 복지포인트 지원",
            "source_url": "https://gbyouth.fixture.invalid/policy/1",
        }
    )
    value.update(changes)
    return NormalizedProgram.from_dict(value)


def descriptor(source_id: str) -> BaselineDescriptor:
    marker = "1" if source_id == "youthcenter-api" else "2"
    return BaselineDescriptor(
        source_id=source_id,
        snapshot_id=marker * 32,
        snapshot_collected_at=CHECKED_AT,
        snapshot_policy_count=1,
        database_checked_at=CHECKED_AT,
        database_policy_count=1,
    )


def baseline(*, mode: str = "default") -> AggregatorBaseline:
    youth = BaselineRecord(
        identity=PolicyIdentity("youthcenter-api", "YOUTH-001"),
        title="경북 청년 행복카드 지원사업",
        organization=(
            None if mode == "title_incomplete" else "경상북도경제진흥원"
        ),
        canonical_region_keys=("kr-bjd-20260803:4700000000",),
        application_start=datetime(2026, 6, 1).date(),
        application_end=datetime(2026, 6, 30).date(),
        support_content=(
            "서로 다른 지원 내용"
            if mode == "title_different"
            else "1인당 100만원 복지포인트 지원"
        ),
        canonical_urls=(
            "https://apply.fixture.invalid/program/1?utm_source=test",
        ),
        announcement_identities=(
            AnnouncementIdentity("경상북도", "공고-2026-101"),
        ),
        database_row_id=1,
    )
    bokjiro = BaselineRecord(
        identity=PolicyIdentity(
            "bokjiro-central-welfare-api", "BOKJIRO-001"
        ),
        title="무관한 중앙 복지정책",
        organization="중앙기관",
        canonical_region_keys=(),
        application_start=datetime(2026, 1, 1).date(),
        application_end=datetime(2026, 12, 31).date(),
        support_content="중앙 복지 지원",
        canonical_urls=("https://bokjiro.fixture.invalid/program/1",),
        database_row_id=2,
    )
    return AggregatorBaseline(
        descriptors=(
            descriptor("youthcenter-api"),
            descriptor("bokjiro-central-welfare-api"),
        ),
        records=(youth, bokjiro),
    )


def evidence(program: NormalizedProgram, mode: str) -> DuplicateEvidence:
    references = ()
    urls = (program.source_url,)
    announcements = ()
    locators = [("canonical_urls", "detail:canonical_url")]
    if mode == "external_id":
        references = (PolicyIdentity("youthcenter-api", "YOUTH-001"),)
        locators.append(("aggregator_references", "detail:plcyNo"))
    elif mode == "canonical_url":
        urls = (
            "https://apply.fixture.invalid/program/1#application",
        )
    elif mode == "announcement_id":
        announcements = (
            AnnouncementIdentity("경상북도", "공고 2026-101"),
        )
        locators.append(
            ("announcement_identities", "detail:announcement_id")
        )
    return DuplicateEvidence(
        aggregator_references=references,
        canonical_urls=urls,
        announcement_identities=announcements,
        field_locators=tuple(locators),
        provenance=program.provenance,
    )


class CrossSourceDuplicateTests(unittest.TestCase):
    def test_contract_cases_are_deterministic(self) -> None:
        self.assertEqual(7, len(CASES))
        for case in CASES:
            with self.subTest(case=case["name"]):
                program = candidate_program(
                    title=(
                        "새로운 경북 청년 지역사업"
                        if case["mode"] == "new_policy"
                        else "경북 청년 행복카드 지원사업"
                    ),
                    organization=(
                        "다른 시행기관"
                        if case["mode"] == "title_different"
                        else "경상북도경제진흥원"
                    ),
                )
                selected_baseline = baseline(mode=case["mode"])
                decision = evaluate_cross_source_duplicate(
                    program,
                    evidence(program, case["mode"]),
                    selected_baseline,
                )
                self.assertEqual(case["expected"], decision.outcome.value)
                self.assertEqual((case["reason"],), decision.reason_codes)

    def test_missing_baseline_never_promotes_a_policy(self) -> None:
        program = candidate_program()
        decision = evaluate_cross_source_duplicate(
            program,
            evidence(program, "new_policy"),
            None,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(
            ("aggregator_baseline_unavailable",), decision.reason_codes
        )

    def test_non_unique_canonical_url_requires_review(self) -> None:
        program = candidate_program()
        selected = baseline()
        shared_url = "https://apply.fixture.invalid/shared"
        selected = replace(
            selected,
            records=tuple(
                replace(record, canonical_urls=(shared_url,))
                for record in selected.records
            ),
        )
        selected_evidence = DuplicateEvidence(
            canonical_urls=(shared_url,),
            field_locators=(("canonical_urls", "detail:application_url"),),
            provenance=program.provenance,
        )

        decision = evaluate_cross_source_duplicate(
            program, selected_evidence, selected
        )

        self.assertFalse(decision.accepted)
        self.assertEqual(
            ("canonical_url_matches_multiple_policies",),
            decision.reason_codes,
        )

    def test_evidence_requires_a_locator_and_matching_provenance(self) -> None:
        program = candidate_program()
        with self.assertRaisesRegex(
            CrossSourceDuplicateError, "requires a locator"
        ):
            DuplicateEvidence(
                canonical_urls=(program.source_url,),
                provenance=program.provenance,
            )
        wrong_evidence = replace(
            evidence(program, "new_policy"), provenance=program.provenance[:1]
        )
        with self.assertRaisesRegex(
            CrossSourceDuplicateError, "provenance must match"
        ):
            evaluate_cross_source_duplicate(
                program, wrong_evidence, baseline()
            )

    def test_manifest_is_deterministic_and_idempotently_stored(self) -> None:
        program = candidate_program(title="새로운 경북 청년 지역사업")
        selected_baseline = baseline()
        decision = evaluate_cross_source_duplicate(
            program,
            evidence(program, "new_policy"),
            selected_baseline,
        )
        manifest = CrossSourceDecisionManifest(
            source_id=program.source_id,
            baseline=selected_baseline,
            decisions=(decision,),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CrossSourceDecisionManifestStore(temp_dir)
            first = store.save(manifest)
            second = store.save(manifest)
            restored = json.loads(first.read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(manifest.manifest_id, restored["manifest_id"])
        self.assertEqual(
            selected_baseline.baseline_id,
            restored["baseline"]["baseline_id"],
        )
        self.assertEqual(
            1, restored["counts"]["accepted_regional"]
        )


if __name__ == "__main__":
    unittest.main()
