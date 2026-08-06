from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.profile_release_dataset import (
    _application_period_safety,
    _contains_terms,
    _counter,
    _default_visible,
    _golden_confirmed,
    _period_status_consistent,
    build_parser,
    main,
)


class ReleaseDatasetProfileTests(unittest.TestCase):
    def test_period_safety_can_be_required_by_release_audit(self) -> None:
        args = build_parser().parse_args(["--require-period-safety"])

        self.assertTrue(args.require_period_safety)

    def test_required_period_safety_returns_failure_exit_code(self) -> None:
        with TemporaryDirectory() as directory, patch(
            "scripts.profile_release_dataset.build_report",
            return_value={"application_period_safety": {"passed": False}},
        ):
            output = Path(directory) / "report.json"

            exit_code = main(
                [
                    "--output",
                    str(output),
                    "--require-period-safety",
                ]
            )

        self.assertEqual(1, exit_code)

    def test_counter_exposes_null_as_explicit_bucket(self) -> None:
        self.assertEqual(
            {"closed": 1, "null": 2, "open": 1},
            _counter([None, "open", None, "closed"]),
        )

    def test_closed_policy_is_not_default_visible(self) -> None:
        self.assertTrue(_default_visible({"application_status": None}))
        self.assertTrue(_default_visible({"application_status": "open"}))
        self.assertTrue(
            _default_visible({"application_status": "scheduled"})
        )
        self.assertFalse(_default_visible({"application_status": "closed"}))

    def test_search_terms_use_backend_projection_fields(self) -> None:
        program = {
            "title": "청년 주거 지원",
            "category_text": None,
            "categories": ["housing"],
            "keywords": ["월세"],
            "summary": None,
            "life_stages": [],
            "target_groups": [],
            "age_condition_text": None,
            "eligibility_text": None,
            "education_statuses": [],
            "employment_statuses": [],
            "required_conditions": [],
            "preferred_conditions": [],
            "excluded_conditions": [],
            "support_content": "임차료 지원",
        }

        self.assertTrue(_contains_terms(program, ("청년", "월세", "지원")))
        self.assertFalse(_contains_terms(program, ("전세",)))

    def test_golden_confirmation_requires_open_housing_age_and_region(self) -> None:
        row = {
            "data_quality_status": "valid",
            "application_status": "open",
            "application_schedule": "always",
            "categories": ["housing"],
            "age": {"state": "match"},
            "region": {"state": "match"},
        }

        self.assertTrue(_golden_confirmed(row))
        row["application_status"] = None
        self.assertFalse(_golden_confirmed(row))

    def test_period_safety_keeps_free_text_dates_unknown(self) -> None:
        programs = (
            {
                "source_id": "bokjiro-central-welfare-api",
                "external_id": "bokjiro-1",
                "application_period_text": None,
                "application_start": None,
                "application_end": None,
                "application_schedule": None,
                "application_status": None,
                "support_content": "신청기간 2026-03-30 ~ 2026-05-29",
            },
        )

        audit = _application_period_safety(programs)

        self.assertFalse(audit["free_text_date_promotion_allowed"])
        self.assertEqual(1, audit["all"]["unknown_period_and_status"])
        self.assertEqual(
            1,
            audit["all"]["free_text_date_mentions_not_promoted"],
        )
        self.assertEqual(0, audit["all"]["unsafe_source_promotions"])

    def test_period_safety_detects_abbreviated_year_without_promotion(
        self,
    ) -> None:
        programs = (
            {
                "source_id": "bokjiro-central-welfare-api",
                "external_id": "WLF00004661",
                "application_period_text": None,
                "application_start": None,
                "application_end": None,
                "application_schedule": None,
                "application_status": None,
                "summary": "'26년 신규 신청기간: 3.30 ~ 5.29까지",
            },
        )

        audit = _application_period_safety(programs)

        self.assertEqual(
            1,
            audit["all"]["free_text_date_mentions_not_promoted"],
        )

    def test_period_safety_rejects_value_without_source_mapping(self) -> None:
        programs = (
            {
                "source_id": "bokjiro-central-welfare-api",
                "external_id": "bokjiro-1",
                "application_period_text": "상시",
                "application_start": None,
                "application_end": None,
                "application_schedule": "always",
                "application_status": "open",
            },
        )

        audit = _application_period_safety(programs)

        self.assertEqual(1, audit["all"]["unsafe_source_promotions"])

    def test_period_safety_passes_for_source_backed_golden_policy(self) -> None:
        programs = (
            {
                "source_id": "youthcenter-api",
                "external_id": "20260430005400212969",
                "application_period_text": "상시",
                "application_start": None,
                "application_end": None,
                "application_schedule": "always",
                "application_status": "open",
            },
        )

        audit = _application_period_safety(programs)

        self.assertTrue(audit["passed"])
        self.assertTrue(audit["golden_policy"]["safety_passed"])

    def test_period_status_consistency_uses_collection_date(self) -> None:
        program = {
            "application_period_text": "2026-07-01 ~ 2026-07-31",
            "application_start": "2026-07-01",
            "application_end": "2026-07-31",
            "application_schedule": "fixed_period",
            "application_status": "open",
            "collected_at": "2026-07-15T10:00:00+09:00",
        }

        self.assertTrue(_period_status_consistent(program))
        program["application_status"] = "scheduled"
        self.assertFalse(_period_status_consistent(program))


if __name__ == "__main__":
    unittest.main()
