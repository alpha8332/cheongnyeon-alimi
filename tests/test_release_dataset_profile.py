from __future__ import annotations

import unittest

from scripts.profile_release_dataset import (
    _contains_terms,
    _counter,
    _default_visible,
    _golden_confirmed,
)


class ReleaseDatasetProfileTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
