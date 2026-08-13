from __future__ import annotations

import json
import unittest
from dataclasses import replace
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
    RegionalSourceScopeEvidence,
    enforce_youth_target,
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
LIST_PROVENANCE = SourceProvenance(
    raw_document_id="2" * 32,
    document_role=RawDocumentRole.LIST_RESPONSE,
    content_hash="sha256:" + "b" * 64,
    collected_at=COLLECTED_AT,
    source_url="https://regional.example.test/policies",
)
SCOPED_PROVENANCE = (LIST_PROVENANCE, *PROVENANCE)


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


def source_scope(
    *,
    jurisdiction_text: str = "경상북도",
    operator_text: str = "경상북도 청년정책 담당기관",
    youth_policy_scope_text: str | None = "경상북도 청년정책 목록",
    application_scope_text: str | None = None,
) -> RegionalSourceScopeEvidence:
    values = {
        "jurisdiction_text": jurisdiction_text,
        "operator_text": operator_text,
        "youth_policy_scope_text": youth_policy_scope_text,
        "application_scope_text": application_scope_text,
    }
    return RegionalSourceScopeEvidence(
        **values,
        field_locators=tuple(
            (field_name, f"fixture:list_scope:{field_name}")
            for field_name, value in values.items()
            if value is not None
        ),
        provenance=(LIST_PROVENANCE,),
    )


def scoped_policy_and_evidence(
    case: dict[str, object],
    *,
    scope: RegionalSourceScopeEvidence,
    organization: str | None,
    eligibility: str | None,
    source_region: str | None = None,
    application_period: str | None = "2026-08-01 ~ 2026-08-31",
    title: str = "주거비 지원사업",
    age_text: str | None = None,
) -> tuple[ExtractedPolicy, RegionalPolicyEvidence]:
    selected_policy = replace(
        policy(case),
        title=title,
        organization=organization,
        eligibility_text=eligibility,
        region_text=source_region,
        application_period_text=application_period,
        age_text=age_text,
        provenance=SCOPED_PROVENANCE,
    )
    values = {
        "implementing_organization_text": organization,
        "region_eligibility_text": eligibility,
        "application_channel_text": None,
        "additional_benefit_text": None,
        "source_region_text": source_region,
        "application_period_text": application_period,
    }
    selected_evidence = RegionalPolicyEvidence(
        **values,
        field_locators=tuple(
            (field_name, f"fixture:detail:{field_name}")
            for field_name, value in values.items()
            if value is not None
        ),
        provenance=SCOPED_PROVENANCE,
        source_scope=scope,
    )
    return selected_policy, selected_evidence


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

    def test_source_scope_plus_one_policy_region_field_is_accepted(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(),
            organization="경상북도 청년정책과",
            eligibility="만 19세 이상 청년",
        )

        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertTrue(decision.accepted)
        self.assertIn("source_scope_region_confirmed", decision.reason_codes)
        self.assertIn(
            "source_scope_operator_confirmed", decision.reason_codes
        )
        self.assertIn("implementing_region_confirmed", decision.reason_codes)

    def test_source_scope_alone_cannot_create_policy_region(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(),
            organization="청년지원센터",
            eligibility="만 19세 이상",
        )

        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertIs(
            RegionalityStatus.REGIONAL_REVIEW_REQUIRED,
            decision.regionality,
        )
        self.assertFalse(decision.accepted)

    def test_mismatched_source_scope_cannot_confirm_region(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(
                jurisdiction_text="부산광역시",
                operator_text="부산광역시 청년정책과",
            ),
            organization="경상북도 청년정책과",
            eligibility="만 19세 이상 청년",
        )

        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertFalse(decision.accepted)

    def test_current_list_scope_can_fill_only_missing_application_state(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(application_scope_text="현재 접수중 정책"),
            organization="경상북도 청년정책과",
            eligibility="경상북도 거주 청년",
            application_period=None,
        )

        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertTrue(decision.accepted)
        self.assertIs(ApplicationAvailability.OPEN, decision.application)
        self.assertIn("source_scope_application_open", decision.reason_codes)

    def test_explicit_closed_item_overrides_current_list_scope(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(application_scope_text="현재 접수중 정책"),
            organization="경상북도 청년정책과",
            eligibility="경상북도 거주 청년",
            application_period="2026-06-01 ~ 2026-06-30",
        )

        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        self.assertFalse(decision.accepted)
        self.assertIs(ApplicationAvailability.CLOSED, decision.application)

    def test_youth_scope_needs_item_marker_or_explicit_age(self) -> None:
        case = self.fixture["cases"][0]
        selected_policy, selected_evidence = scoped_policy_and_evidence(
            case,
            scope=source_scope(),
            organization="경상북도 청년정책과",
            eligibility="경상북도 거주자",
            title="주거비 지원사업",
        )
        decision = evaluate_regional_policy(
            selected_policy,
            selected_evidence,
            expected_region_text="경상북도",
            as_of=date(2026, 8, 11),
        )

        unconfirmed = enforce_youth_target(selected_policy, decision)
        self.assertFalse(unconfirmed.accepted)
        self.assertIn("youth_target_unconfirmed", unconfirmed.reason_codes)

        aged_policy = replace(selected_policy, age_text="만 19세 ~ 만 39세")
        confirmed = enforce_youth_target(aged_policy, decision)
        self.assertTrue(confirmed.accepted)
        self.assertIn(
            "youth_target_confirmed_by_scope_and_age",
            confirmed.reason_codes,
        )

    def test_source_scope_requires_list_response_provenance(self) -> None:
        with self.assertRaisesRegex(ValueError, "list_response provenance"):
            RegionalSourceScopeEvidence(
                jurisdiction_text="경상북도",
                operator_text="경상북도 청년정책과",
                youth_policy_scope_text=None,
                application_scope_text=None,
                field_locators=(
                    ("jurisdiction_text", "fixture:jurisdiction"),
                    ("operator_text", "fixture:operator"),
                ),
                provenance=PROVENANCE,
            )

    def test_source_scope_requires_jurisdiction_and_operator(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "requires jurisdiction and operator"
        ):
            RegionalSourceScopeEvidence(
                jurisdiction_text=None,  # type: ignore[arg-type]
                operator_text="경상북도 청년정책과",
                youth_policy_scope_text=None,
                application_scope_text=None,
                field_locators=(("operator_text", "fixture:operator"),),
                provenance=(LIST_PROVENANCE,),
            )


if __name__ == "__main__":
    unittest.main()
