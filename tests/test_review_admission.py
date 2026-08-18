from __future__ import annotations

import json
import unittest
from pathlib import Path

from collectors.review_admission import (
    YOUTH_TAXONOMY_GROUPS,
    ReviewAdmissionCandidate,
    classify_review_candidate,
    manifest_hash,
    match_youth_taxonomy,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/fixtures/contracts/review_admission_cases.json"


class ReviewAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_contract_cases(self) -> None:
        for index, case in enumerate(self.fixture["cases"]):
            with self.subTest(case=case["id"]):
                candidate = ReviewAdmissionCandidate(
                    source_id="regional-fixture-youth-platform",
                    external_id=f"RA2-{index:03d}",
                    source_url="https://regional.example.test/policies/1",
                    provenance_ids=tuple(
                        case.get("provenance_ids", ["1" * 32])
                    ),
                    checkpoint_outcome=case.get("checkpoint_outcome", "review"),
                    regionality="regional_review_required",
                    application=case["application"],
                    original_reason_codes=tuple(case["reason_codes"]),
                    item_texts=tuple(case["item_texts"]),
                    normalization_status=case.get(
                        "normalization_status", "partial"
                    ),
                    residual_unknown_codes=tuple(
                        case.get("unknown_codes", ["missing_age_condition"])
                    ),
                    policy_fingerprint="sha256:" + "a" * 64,
                    duplicate_outcome=case.get(
                        "duplicate_outcome", "accepted_regional"
                    ),
                    duplicate_reason_codes=("fixture_duplicate_decision",),
                )
                decision = classify_review_candidate(candidate)
                self.assertEqual(case["expected_outcome"], decision.outcome.value)
                if case.get("unknown_codes"):
                    self.assertEqual(
                        tuple(sorted(case["unknown_codes"])),
                        decision.residual_unknown_codes,
                    )

    def test_every_approved_taxonomy_marker_is_recognized(self) -> None:
        for group, markers in YOUTH_TAXONOMY_GROUPS.items():
            for marker in markers:
                with self.subTest(group=group, marker=marker):
                    matches = match_youth_taxonomy((f"{marker} 지원사업",))
                    self.assertIn((group, marker), matches)

    def test_spacing_brackets_and_case_are_normalized(self) -> None:
        matches = match_youth_taxonomy(
            ("가족돌봄청[소]년, 여성 1인 가구, rotc 지원",)
        )
        self.assertIn(("care_independence", "가족돌봄청소년"), matches)
        self.assertIn(("household_business", "1인가구"), matches)
        self.assertIn(("cohort_military", "ROTC"), matches)

    def test_2030_year_does_not_match_cohort(self) -> None:
        self.assertNotIn(
            ("cohort_military", "2030세대"),
            match_youth_taxonomy(("2030년 중장기 계획",)),
        )
        self.assertIn(
            ("cohort_military", "2030세대"),
            match_youth_taxonomy(("2030 세대 지원",)),
        )

    def test_manifest_hash_ignores_only_hash_field(self) -> None:
        value = {"schema_version": "1.0.0", "decisions": []}
        digest = manifest_hash(value)
        value["manifest_sha256"] = digest
        self.assertEqual(digest, manifest_hash(value))
        value["decisions"].append({"outcome": "hold_review"})
        self.assertNotEqual(digest, manifest_hash(value))


if __name__ == "__main__":
    unittest.main()

