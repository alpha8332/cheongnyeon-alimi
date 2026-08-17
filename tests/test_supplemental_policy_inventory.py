from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from collectors.supplemental_inventory import SupplementalInventoryValidator
from collectors.validation import JsonSchemaValidator


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = (
    ROOT / "data/reference/supplemental_official_policy_inventory.json"
)
INVENTORY_SCHEMA = (
    ROOT / "data/schema/supplemental_official_policy_inventory.schema.json"
)
AUDIT_PATH = (
    ROOT
    / "data/reference/supplemental_official_policy_duplicate_audit.json"
)
AUDIT_SCHEMA = (
    ROOT
    / "data/schema/supplemental_official_policy_duplicate_audit.schema.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class SupplementalPolicyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = load_json(INVENTORY_PATH)
        cls.audit = load_json(AUDIT_PATH)
        cls.inventory_schema = JsonSchemaValidator(INVENTORY_SCHEMA)
        cls.audit_schema = JsonSchemaValidator(AUDIT_SCHEMA)
        cls.domain_validator = SupplementalInventoryValidator(INVENTORY_SCHEMA)

    def test_inventory_matches_schema_and_domain_contract(self) -> None:
        self.assertEqual((), self.inventory_schema.schema_issues(self.inventory))
        self.assertEqual((), self.domain_validator.issues(self.inventory))

    def test_xlsx_lineage_and_quality_partition_are_fixed(self) -> None:
        evidence = self.inventory["input_evidence"]
        self.assertEqual(
            "c03aa55fba844639a89a4f62ec083dc74c5397b3ea7fbfab91450fbef97f2095",
            evidence["sha256"],
        )
        self.assertEqual("A1:F71", evidence["range"])
        self.assertEqual(
            {
                "url_row_count": 64,
                "candidate_identity_count": 60,
                "collapsed_exact_duplicate_rows": 4,
                "same_url_title_conflict_count": 3,
                "direct_aggregator_row_count": 11,
                "inventory_status_counts": {
                    "candidate": 55,
                    "data_error": 4,
                    "discovery_reference": 1,
                },
            },
            self.inventory["quality_summary"],
        )
        covered_rows = [
            row
            for candidate in self.inventory["policy_candidates"]
            for row in candidate["input_rows"]
        ]
        self.assertEqual(64, len(covered_rows))
        self.assertEqual(64, len(set(covered_rows)))

    def test_exact_repeats_and_title_url_conflicts_are_quarantined(
        self,
    ) -> None:
        candidates = self.inventory["policy_candidates"]
        repeated_rows = {
            tuple(candidate["input_rows"])
            for candidate in candidates
            if len(candidate["input_rows"]) == 2
        }
        self.assertEqual(
            {(54, 58), (55, 65), (56, 66), (57, 69)},
            repeated_rows,
        )
        conflicts = self.inventory["same_url_title_conflicts"]
        self.assertEqual(
            {(12, 13), (15, 16), (54, 58, 59)},
            {tuple(conflict["input_rows"]) for conflict in conflicts},
        )
        by_row = {
            row: candidate
            for candidate in candidates
            for row in candidate["input_rows"]
        }
        for row in (13, 16, 54, 58, 59):
            self.assertEqual("data_error", by_row[row]["inventory_status"])

    def test_unverified_workbook_text_is_hashed_not_imported(self) -> None:
        for candidate in self.inventory["policy_candidates"]:
            untrusted = candidate["untrusted_input"]
            self.assertEqual(
                {
                    "collection_method_sha256",
                    "note_sha256",
                    "note_present",
                },
                set(untrusted),
            )
            self.assertTrue(
                untrusted["collection_method_sha256"].startswith("sha256:")
            )
            self.assertEqual(
                untrusted["note_present"],
                untrusted["note_sha256"] is not None,
            )

    def test_sop2_has_five_approved_sources_and_one_robots_block(self) -> None:
        groups = {
            group["source_group_id"]: group
            for group in self.inventory["source_groups"]
        }
        approved = {
            group_id
            for group_id, group in groups.items()
            if group["status"] == "approved"
        }
        self.assertEqual(
            {
                "work24-policy",
                "lh-housing-announcements",
                "kosaf-scholarships",
                "kinfa-financial-products",
                "kpass-transit-refund",
            },
            approved,
        )
        for group_id in approved:
            group = groups[group_id]
            self.assertEqual("implemented_http", group["implementation_status"])
            self.assertTrue(group["source_id"])
            self.assertTrue(group["approved_list_urls"])
            self.assertTrue(group["approved_detail_url_patterns"])
            self.assertEqual(
                {
                    "max_list_requests": 1,
                    "max_detail_requests": 3,
                    "minimum_interval_seconds": 2,
                },
                group["request_budget"],
            )
        k_startup = groups["k-startup-announcements"]
        self.assertEqual("blocked", k_startup["status"])
        self.assertEqual("disallowed", k_startup["preflight"]["robots"]["status"])
        self.assertEqual([], k_startup["approved_list_urls"])

    def test_actual_duplicate_audit_matches_schema_and_inventory_hash(self) -> None:
        self.assertEqual((), self.audit_schema.schema_issues(self.audit))
        self.assertEqual(
            hashlib.sha256(INVENTORY_PATH.read_bytes()).hexdigest(),
            self.audit["inventory_sha256"],
        )
        self.assertEqual(
            {
                "candidate_identity_count": 60,
                "exact_duplicate": 26,
                "review_required": 11,
                "potentially_new": 19,
                "not_assessed": 4,
            },
            self.audit["summary"],
        )
        descriptors = {
            descriptor["source_id"]: descriptor
            for descriptor in self.audit["baseline"]["descriptors"]
        }
        self.assertEqual(
            461,
            descriptors["bokjiro-central-welfare-api"][
                "database_policy_count"
            ],
        )
        self.assertEqual(2698, descriptors["youthcenter-api"]["database_policy_count"])

    def test_all_direct_aggregator_rows_are_exact_duplicates(self) -> None:
        inventory_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in self.inventory["policy_candidates"]
        }
        direct = [
            decision
            for decision in self.audit["decisions"]
            if inventory_by_id[decision["candidate_id"]]["source_group"]
            == "approved-aggregator-comparison"
        ]
        self.assertEqual(11, sum(len(item["input_rows"]) for item in direct))
        self.assertEqual(
            {"exact_duplicate"},
            {item["duplicate_outcome"] for item in direct},
        )
        self.assertEqual(
            10,
            len(
                {
                    (
                        item["matched_policies"][0]["source_id"],
                        item["matched_policies"][0]["external_id"],
                    )
                    for item in direct
                }
            ),
        )

    def test_audit_decisions_cover_inventory_once_and_reconcile_summary(
        self,
    ) -> None:
        inventory_ids = {
            candidate["candidate_id"]
            for candidate in self.inventory["policy_candidates"]
        }
        audit_ids = [
            decision["candidate_id"]
            for decision in self.audit["decisions"]
        ]
        self.assertEqual(inventory_ids, set(audit_ids))
        self.assertEqual(len(audit_ids), len(set(audit_ids)))
        counts = {
            outcome: sum(
                decision["duplicate_outcome"] == outcome
                for decision in self.audit["decisions"]
            )
            for outcome in (
                "exact_duplicate",
                "review_required",
                "potentially_new",
                "not_assessed",
            )
        }
        self.assertEqual(
            {
                key: value
                for key, value in self.audit["summary"].items()
                if key != "candidate_identity_count"
            },
            counts,
        )
        for decision in self.audit["decisions"]:
            with self.subTest(candidate=decision["candidate_id"]):
                if decision["duplicate_outcome"] in {
                    "potentially_new",
                    "not_assessed",
                }:
                    self.assertEqual([], decision["matched_policies"])

    def test_domain_validator_rejects_unsafe_lifecycle_mutations(self) -> None:
        cases = []
        missing_row = copy.deepcopy(self.inventory)
        missing_row["policy_candidates"][0]["input_rows"] = []
        cases.append(missing_row)

        approved = copy.deepcopy(self.inventory)
        index = next(
            i
            for i, group in enumerate(approved["source_groups"])
            if group["status"] == "approved"
        )
        approved["source_groups"][index]["approved_list_urls"] = []
        cases.append(approved)

        blocked = copy.deepcopy(self.inventory)
        index = next(
            i
            for i, group in enumerate(blocked["source_groups"])
            if group["status"] == "blocked"
        )
        blocked["source_groups"][index]["source_id"] = "unsafe-source"
        cases.append(blocked)

        for candidate in cases:
            with self.subTest():
                self.assertTrue(self.domain_validator.issues(candidate))


if __name__ == "__main__":
    unittest.main()
