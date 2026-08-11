from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from collectors.extracted import ExtractedPolicy, SourceProvenance
from collectors.normalized import CoverageScope, RegionRelation
from collectors.normalizer import Normalizer
from collectors.raw import RawDocumentRole
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalityStatus,
    RegionalPolicyEvidence,
    evaluate_regional_policy,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "data/fixtures/regional/regional_policy_gate_cases.json"
)
COLLECTED_AT = datetime(2026, 8, 11, tzinfo=timezone.utc)
PROVENANCE = (
    SourceProvenance(
        raw_document_id="1" * 32,
        document_role=RawDocumentRole.DETAIL_RESPONSE,
        content_hash="sha256:" + "a" * 64,
        collected_at=COLLECTED_AT,
        source_url="https://regional.example.test/policies/1",
    ),
)


def policy(case: dict[str, object]) -> ExtractedPolicy:
    return ExtractedPolicy(
        source_id="regional-fixture-youth-platform",
        source_name="RYP3 합성 계약 Source",
        external_id=str(case["id"]),
        title="RYP3 합성 지역정책 판정 사례",
        organization=str(case["implementing_organization_text"]),
        category_text="복지",
        application_period_text=case["application_period_text"],
        region_text=str(case["source_region_text"]),
        age_text=None,
        eligibility_text=str(case["region_eligibility_text"]),
        support_content="합성 계약 검증용 지원 내용",
        application_method=None,
        source_url="https://regional.example.test/policies/1",
        collected_at=COLLECTED_AT,
        provenance=PROVENANCE,
        extra={"synthetic_contract_fixture": True},
    )


def evidence(case: dict[str, object]) -> RegionalPolicyEvidence:
    values = {
        "implementing_organization_text": case[
            "implementing_organization_text"
        ],
        "region_eligibility_text": case["region_eligibility_text"],
        "application_channel_text": None,
        "additional_benefit_text": None,
        "source_region_text": case["source_region_text"],
        "application_period_text": case["application_period_text"],
    }
    return RegionalPolicyEvidence(
        **values,
        field_locators=tuple(
            (field_name, f"fixture:{field_name}")
            for field_name, value in values.items()
            if value is not None
        ),
        provenance=PROVENANCE,
    )


class RegionalPolicyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_contract_cases_are_deterministically_classified(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                decision = evaluate_regional_policy(
                    policy(case),
                    evidence(case),
                    expected_region_text=self.fixture[
                        "expected_region_text"
                    ],
                    as_of=date.fromisoformat(self.fixture["as_of"]),
                )

                self.assertIs(
                    RegionalityStatus(case["expected_regionality"]),
                    decision.regionality,
                )
                self.assertIs(
                    ApplicationAvailability(case["expected_application"]),
                    decision.application,
                )
                self.assertEqual(case["accepted"], decision.accepted)

    def test_accepted_policy_has_canonical_region_rule_and_provenance(self) -> None:
        case = self.fixture["cases"][0]
        decision = evaluate_regional_policy(
            policy(case),
            evidence(case),
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        assert decision.accepted_policy is not None
        result = Normalizer().normalize(decision.accepted_policy)

        self.assertIsNotNone(result.program)
        assert result.program is not None
        self.assertIs(CoverageScope.REGIONAL, result.program.coverage_scope)
        self.assertEqual(("경상북도",), result.program.regions)
        self.assertEqual(1, len(result.program.region_rules))
        self.assertIs(
            RegionRelation.INCLUDE,
            result.program.region_rules[0].relation,
        )
        self.assertEqual("4700000000", result.program.region_rules[0].region_code)
        self.assertEqual(1, len(result.program.provenance))

    def test_regional_district_keeps_the_more_specific_canonical_rule(self) -> None:
        case = next(
            value
            for value in self.fixture["cases"]
            if value["id"] == "regional-district-open"
        )
        decision = evaluate_regional_policy(
            policy(case),
            evidence(case),
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        assert decision.accepted_policy is not None
        result = Normalizer().normalize(decision.accepted_policy)
        self.assertIsNotNone(result.program)
        assert result.program is not None
        self.assertEqual(
            case["expected_region_code"],
            result.program.region_rules[0].region_code,
        )

    def test_portal_location_alone_never_creates_region_evidence(self) -> None:
        case = next(
            value
            for value in self.fixture["cases"]
            if value["id"] == "portal-only-ambiguous"
        )

        decision = evaluate_regional_policy(
            policy(case),
            evidence(case),
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertIs(
            RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
            decision.regionality,
        )
        self.assertIsNone(decision.accepted_policy)

    def test_evidence_value_without_locator_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires one locator"):
            RegionalPolicyEvidence(
                implementing_organization_text="경상북도",
                region_eligibility_text=None,
                application_channel_text=None,
                additional_benefit_text=None,
                source_region_text=None,
                application_period_text=None,
                field_locators=(),
                provenance=PROVENANCE,
            )


if __name__ == "__main__":
    unittest.main()
