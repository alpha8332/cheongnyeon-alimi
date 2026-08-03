from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from collectors.extracted import ExtractedPolicy, SourceProvenance
from collectors.normalized import (
    ApplicationSchedule,
    ApplicationStatus,
    Category,
    CoverageScope,
    DataQualityStatus,
    NormalizedProgram,
    NormalizedProgramValidationError,
    RegionRelation,
    RegionResolutionStatus,
)
from collectors.normalizer import Normalizer, normalize_text
from collectors.raw import RawDocumentRole
from collectors.validation import NormalizedProgramValidator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data/schema/normalized_program.schema.json"
FIXTURE_ROOT = ROOT / "tests/fixtures/normalized"
COLLECTED_AT = datetime(2026, 7, 26, 7, 30, tzinfo=timezone.utc)


def extracted_policy(
    *,
    title: str | None = "<b>청년 &amp; 정책</b>",
    category_text: str | None = "주거,일자리",
    application_period_text: str | None = (
        "2026. 7. 1. ~ 2026. 7. 31."
    ),
    region_text: str | None = "서울시, 경북, 포항",
    age_text: str | None = "만 19세 이상 34세 이하",
    eligibility_text: str | None = "  청년\n\n대상  ",
    support_content: str | None = "<p>월 10만원</p><script>x</script>",
) -> ExtractedPolicy:
    provenance = (
        SourceProvenance(
            raw_document_id="1" * 32,
            document_role=RawDocumentRole.LIST_RESPONSE,
            content_hash=f"sha256:{'a' * 64}",
            collected_at=COLLECTED_AT,
            source_url="https://example.test/api/policies",
        ),
        SourceProvenance(
            raw_document_id="2" * 32,
            document_role=RawDocumentRole.LIST_ITEM,
            content_hash=f"sha256:{'b' * 64}",
            collected_at=COLLECTED_AT,
            source_url="https://example.test/api/policies",
        ),
    )
    return ExtractedPolicy(
        source_id="test-source",
        source_name="테스트 정책 API",
        external_id="POLICY-1",
        title=title,
        organization=" 테스트 기관 ",
        category_text=category_text,
        application_period_text=application_period_text,
        region_text=region_text,
        age_text=age_text,
        eligibility_text=eligibility_text,
        support_content=support_content,
        application_method="<div>온라인</div>",
        source_url="https://example.test/policies/1",
        collected_at=COLLECTED_AT,
        provenance=provenance,
        extra={"source_fields": {}},
    )


class TextAndFieldNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = Normalizer()

    def test_valid_fixture_normalizes_text_dates_age_region_category(
        self,
    ) -> None:
        result = self.normalizer.normalize(extracted_policy())

        self.assertEqual(DataQualityStatus.VALID, result.status)
        self.assertEqual((), result.issues)
        self.assertIsNotNone(result.program)
        program = result.program
        assert program is not None
        self.assertEqual("청년 & 정책", program.title)
        self.assertEqual("테스트 기관", program.organization)
        self.assertEqual("청년 대상", program.eligibility_text)
        self.assertEqual("월 10만원", program.support_content)
        self.assertEqual("온라인", program.application_method)
        self.assertEqual(
            (Category.HOUSING, Category.EMPLOYMENT),
            program.categories,
        )
        self.assertEqual("2026-07-01", str(program.application_start))
        self.assertEqual("2026-07-31", str(program.application_end))
        self.assertEqual(
            ApplicationSchedule.FIXED_PERIOD,
            program.application_schedule,
        )
        self.assertEqual(
            ApplicationStatus.OPEN,
            program.application_status,
        )
        self.assertEqual(19, program.age_min)
        self.assertEqual(34, program.age_max)
        self.assertEqual(
            ("서울특별시", "경상북도", "포항시"),
            program.regions,
        )
        self.assertEqual(2, len(program.provenance))
        self.assertEqual("1.1.0", program.SCHEMA_VERSION)
        self.assertEqual((), program.keywords)
        self.assertEqual((), program.life_stages)
        self.assertEqual((), program.target_groups)
        self.assertEqual(CoverageScope.UNKNOWN, program.coverage_scope)
        self.assertEqual((), program.region_rules)

    def test_actual_compact_date_and_multiple_category_are_supported(
        self,
    ) -> None:
        result = self.normalizer.normalize(
            extracted_policy(
                category_text="금융･복지･문화",
                application_period_text="20260119 ~ 20261218",
                region_text="전국",
                age_text="연령 제한 없음",
            )
        )

        self.assertEqual(DataQualityStatus.VALID, result.status)
        program = result.program
        assert program is not None
        self.assertEqual(
            (Category.FINANCE, Category.WELFARE),
            program.categories,
        )
        self.assertEqual("2026-01-19", str(program.application_start))
        self.assertEqual("2026-12-18", str(program.application_end))
        self.assertIsNone(program.age_min)
        self.assertIsNone(program.age_max)
        self.assertEqual(("전국",), program.regions)
        self.assertEqual(CoverageScope.UNKNOWN, program.coverage_scope)

    def test_schedule_and_status_have_separate_meanings(self) -> None:
        always = self.normalizer.normalize(
            extracted_policy(
                application_period_text="상시",
                region_text="전국",
                age_text="19세 이상",
            )
        ).program
        future = self.normalizer.normalize(
            extracted_policy(
                application_period_text="2027-01-01 ~ 2027-01-31",
                region_text="전국",
                age_text="34세 이하",
            )
        ).program

        assert always is not None
        assert future is not None
        self.assertEqual(
            ApplicationSchedule.ALWAYS,
            always.application_schedule,
        )
        self.assertEqual(ApplicationStatus.OPEN, always.application_status)
        self.assertEqual(19, always.age_min)
        self.assertEqual(
            ApplicationStatus.SCHEDULED,
            future.application_status,
        )
        self.assertEqual(34, future.age_max)

    def test_partial_fixture_keeps_text_and_reports_field_locations(
        self,
    ) -> None:
        result = self.normalizer.normalize(
            extracted_policy(
                category_text="참여･기반",
                application_period_text="2026-02-30",
                region_text="11110,28155",
                age_text="나이 200세 이상",
            )
        )

        self.assertEqual(DataQualityStatus.PARTIAL, result.status)
        self.assertIsNotNone(result.program)
        paths = {issue.path for issue in result.issues}
        codes = {issue.code for issue in result.issues}
        self.assertIn("$.categories", paths)
        self.assertIn("$.application_period_text", paths)
        self.assertIn("$.regions", paths)
        self.assertIn("$.age_condition_text", paths)
        self.assertIn("unmapped_category", codes)
        self.assertIn("invalid_application_date", codes)
        self.assertIn("unmapped_region_code", codes)
        self.assertIn("invalid_age_range", codes)
        program = result.program
        assert program is not None
        self.assertEqual((Category.OTHER,), program.categories)
        self.assertEqual((), program.regions)
        self.assertEqual("2026-02-30", program.application_period_text)
        self.assertEqual("나이 200세 이상", program.age_condition_text)

    def test_missing_search_fields_are_partial_not_invented_values(
        self,
    ) -> None:
        result = self.normalizer.normalize(
            extracted_policy(
                category_text=None,
                application_period_text=None,
                region_text=None,
                age_text=None,
            )
        )

        self.assertEqual(DataQualityStatus.PARTIAL, result.status)
        program = result.program
        assert program is not None
        self.assertEqual((), program.categories)
        self.assertEqual((), program.regions)
        self.assertIsNone(program.application_status)
        self.assertIsNone(program.age_min)
        codes = {issue.code for issue in result.issues}
        self.assertIn("missing_categories", codes)
        self.assertIn("missing_regions", codes)
        self.assertIn("missing_age_condition", codes)
        self.assertIn("missing_application_period", codes)

    def test_missing_required_title_is_invalid_and_rejected(self) -> None:
        result = self.normalizer.normalize(
            extracted_policy(title="<br>")
        )

        self.assertEqual(DataQualityStatus.INVALID, result.status)
        self.assertIsNone(result.program)
        self.assertTrue(
            any(
                issue.path == "$.title"
                and issue.code == "schema_type"
                for issue in result.issues
            )
        )

    def test_text_normalizer_removes_hidden_and_whitespace_content(
        self,
    ) -> None:
        self.assertEqual(
            "첫 줄 둘째 줄",
            normalize_text(
                " <p>첫&nbsp;줄</p><style>hide</style><br>둘째 줄 "
            ),
        )
        self.assertIsNone(normalize_text(" <br><script>x</script> "))


class SchemaAndValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = NormalizedProgramValidator()
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.valid_result = Normalizer(cls.validator).normalize(
            extracted_policy()
        )

    def test_python_and_json_schema_fields_and_version_match(self) -> None:
        self.assertEqual(
            NormalizedProgram.FIELD_NAMES,
            frozenset(self.schema["required"]),
        )
        self.assertEqual(
            NormalizedProgram.FIELD_NAMES,
            frozenset(self.schema["properties"]),
        )
        self.assertEqual(
            NormalizedProgram.SCHEMA_VERSION,
            self.schema["properties"]["schema_version"]["const"],
        )

    def test_python_model_round_trip_passes_json_schema(self) -> None:
        program = self.valid_result.program
        assert program is not None
        serialized = program.to_dict()

        self.assertEqual((), self.validator.schema_issues(serialized))
        self.assertEqual(
            program,
            NormalizedProgram.from_dict(serialized),
        )

    def test_legacy_1_0_input_is_upgraded_without_region_inference(
        self,
    ) -> None:
        program = self.valid_result.program
        assert program is not None
        legacy = program.to_dict()
        legacy["schema_version"] = "1.0.0"
        for field in NormalizedProgram.SEARCH_FIELD_NAMES:
            legacy.pop(field)

        result = self.validator.validate(legacy)

        self.assertEqual(DataQualityStatus.VALID, result.status)
        self.assertIsNotNone(result.program)
        self.assertEqual("1.1.0", result.candidate["schema_version"])
        self.assertEqual([], result.candidate["keywords"])
        self.assertEqual([], result.candidate["life_stages"])
        self.assertEqual([], result.candidate["target_groups"])
        self.assertEqual("unknown", result.candidate["coverage_scope"])
        self.assertEqual([], result.candidate["region_rules"])
        upgraded = result.program
        assert upgraded is not None
        self.assertEqual(CoverageScope.UNKNOWN, upgraded.coverage_scope)
        self.assertEqual((), upgraded.region_rules)

    def test_valid_partial_invalid_json_fixtures_are_classified(
        self,
    ) -> None:
        results = {}
        for name in ("valid", "partial", "invalid"):
            candidate = json.loads(
                (FIXTURE_ROOT / f"{name}.json").read_text(
                    encoding="utf-8"
                )
            )
            results[name] = self.validator.validate(candidate)

        self.assertEqual(DataQualityStatus.VALID, results["valid"].status)
        self.assertIsNotNone(results["valid"].program)
        self.assertEqual(
            DataQualityStatus.PARTIAL,
            results["partial"].status,
        )
        self.assertIsNotNone(results["partial"].program)
        self.assertEqual(
            DataQualityStatus.INVALID,
            results["invalid"].status,
        )
        self.assertIsNone(results["invalid"].program)
        self.assertTrue(
            any(
                issue.path == "$.title"
                for issue in results["invalid"].issues
            )
        )

    def test_schema_failure_reports_exact_array_and_enum_paths(self) -> None:
        program = self.valid_result.program
        assert program is not None
        invalid = program.to_dict()
        invalid["categories"] = None
        invalid["keywords"] = None
        invalid["application_status"] = "always"
        invalid["coverage_scope"] = "everywhere"
        invalid["data_quality_status"] = "invalid"

        result = self.validator.validate(invalid)

        self.assertEqual(DataQualityStatus.INVALID, result.status)
        self.assertIsNone(result.program)
        errors = {(issue.path, issue.code) for issue in result.issues}
        self.assertIn(("$.categories", "schema_type"), errors)
        self.assertIn(("$.keywords", "schema_type"), errors)
        self.assertIn(("$.application_status", "schema_enum"), errors)
        self.assertIn(("$.coverage_scope", "schema_enum"), errors)

        wrong_python_array = program.to_dict()
        wrong_python_array["regions"] = "서울특별시"
        with self.assertRaises(NormalizedProgramValidationError):
            NormalizedProgram.from_dict(wrong_python_array)

    def test_region_rule_scope_and_include_exclude_invariants(self) -> None:
        program = self.valid_result.program
        assert program is not None
        base = program.to_dict()
        include = {
            "relation": RegionRelation.INCLUDE.value,
            "resolution_status": RegionResolutionStatus.MATCHED.value,
            "region_scheme": "fixture-kr-2026",
            "region_code": "province-chungnam",
            "source_code": "44",
            "source_text": "충청남도",
        }

        regional = dict(base)
        regional["coverage_scope"] = CoverageScope.REGIONAL.value
        regional["region_rules"] = [include]
        regional_result = self.validator.validate(regional)
        self.assertEqual(DataQualityStatus.VALID, regional_result.status)

        conflict = dict(regional)
        conflict["region_rules"] = [
            include,
            {**include, "relation": RegionRelation.EXCLUDE.value},
        ]
        conflict["data_quality_status"] = "invalid"
        conflict_result = self.validator.validate(conflict)
        conflict_errors = {
            (issue.path, issue.code)
            for issue in conflict_result.issues
        }
        self.assertEqual(DataQualityStatus.INVALID, conflict_result.status)
        self.assertIn(
            ("$.region_rules", "region_include_exclude_conflict"),
            conflict_errors,
        )

        unresolved = dict(base)
        unresolved["coverage_scope"] = CoverageScope.UNKNOWN.value
        unresolved["region_rules"] = [
            {
                **include,
                "resolution_status": (
                    RegionResolutionStatus.AMBIGUOUS.value
                ),
            }
        ]
        unresolved["data_quality_status"] = "invalid"
        unresolved_result = self.validator.validate(unresolved)
        self.assertEqual(
            DataQualityStatus.INVALID,
            unresolved_result.status,
        )
        self.assertTrue(
            any(
                issue.code == "unresolved_canonical_region"
                for issue in unresolved_result.issues
            )
        )

    def test_semantic_order_and_quality_label_mismatch_are_invalid(
        self,
    ) -> None:
        program = self.valid_result.program
        assert program is not None
        invalid = program.to_dict()
        invalid["age_min"] = 40
        invalid["age_max"] = 20
        invalid["data_quality_status"] = "valid"

        result = self.validator.validate(invalid)

        self.assertEqual(DataQualityStatus.INVALID, result.status)
        errors = {(issue.path, issue.code) for issue in result.issues}
        self.assertIn(("$.age_max", "age_order"), errors)
        self.assertIn(
            ("$.data_quality_status", "quality_status_mismatch"),
            errors,
        )

    def test_results_are_partitioned_into_valid_partial_invalid(self) -> None:
        normalizer = Normalizer(self.validator)
        partition = normalizer.normalize_many(
            (
                extracted_policy(),
                extracted_policy(
                    category_text=None,
                    application_period_text=None,
                    region_text=None,
                    age_text=None,
                ),
                extracted_policy(title=None),
            )
        )

        self.assertEqual(1, len(partition.valid))
        self.assertEqual(1, len(partition.partial))
        self.assertEqual(1, len(partition.invalid))


if __name__ == "__main__":
    unittest.main()
