from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from collectors.regions import RegionReference, RegionStatus
from collectors.validation import JsonSchemaValidator


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = (
    ROOT / "data/reference/regional_youth_policy_sources.json"
)
SCHEMA_PATH = (
    ROOT
    / "data/schema/regional_youth_policy_source_inventory.schema.json"
)
REGION_SEED = ROOT / "data/seeds/administrative_regions.json"
ALIAS_SEED = ROOT / "data/seeds/administrative_region_aliases.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class RegionalSourceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = load_json(INVENTORY_PATH)
        cls.validator = JsonSchemaValidator(SCHEMA_PATH)
        cls.regions = RegionReference.from_seed_files(
            REGION_SEED, ALIAS_SEED
        )

    def test_inventory_matches_schema(self) -> None:
        self.assertEqual(
            (), self.validator.schema_issues(self.inventory)
        )
        self.assertEqual("1.0.0", self.inventory["schema_version"])
        self.assertEqual(
            "kr-bjd-20260803",
            self.inventory["region_reference_scheme"],
        )

    def test_inventory_contains_each_legacy_portal_label_once(self) -> None:
        sources = self.inventory["sources"]
        expected_labels = {
            "서울",
            "부산",
            "대구",
            "인천",
            "광주",
            "대전",
            "울산",
            "세종",
            "경기",
            "강원",
            "충북",
            "충남",
            "전북",
            "전남",
            "경북",
            "경남",
            "제주",
        }
        self.assertEqual(17, len(sources))
        self.assertEqual(
            expected_labels,
            {source["jurisdiction_label"] for source in sources},
        )
        self.assertEqual(
            len(sources),
            len({source["jurisdiction_key"] for source in sources}),
        )

    def test_candidate_urls_are_unique_public_https(self) -> None:
        sources = self.inventory["sources"]
        urls = [source["home_url"] for source in sources]
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual("https", parsed.scheme)
                self.assertTrue(parsed.hostname)
                self.assertIsNone(parsed.username)
                self.assertIsNone(parsed.password)

    def test_initial_inventory_does_not_claim_source_approval(self) -> None:
        for source in self.inventory["sources"]:
            with self.subTest(source=source["jurisdiction_key"]):
                self.assertEqual("candidate", source["status"])
                self.assertIsNone(source["source_id"])
                self.assertEqual([], source["approved_list_urls"])
                self.assertEqual(
                    [], source["approved_detail_url_patterns"]
                )
                self.assertIsNone(source["request_budget"])
                self.assertEqual(
                    {
                        "operator": "unchecked",
                        "robots": "unchecked",
                        "terms": "unchecked",
                        "license": "unchecked",
                        "technical_access": "unchecked",
                        "last_checked_at": None,
                    },
                    source["preflight"],
                )

    def test_region_mappings_preserve_active_and_retired_codes(self) -> None:
        review_required = set()
        for source in self.inventory["sources"]:
            mapping = source["region_reference"]
            if mapping["mapping_status"] == "matched_active":
                region = self.regions.get(mapping["active_code"])
                self.assertIsNotNone(region)
                assert region is not None
                self.assertEqual(RegionStatus.ACTIVE, region.status)
                self.assertEqual([], mapping["historical_codes"])
                continue

            review_required.add(source["jurisdiction_label"])
            self.assertIsNone(mapping["active_code"])
            self.assertTrue(mapping["historical_codes"])
            for code in mapping["historical_codes"]:
                region = self.regions.get(code)
                self.assertIsNotNone(region)
                assert region is not None
                self.assertEqual(RegionStatus.RETIRED, region.status)

        self.assertEqual({"광주", "전남"}, review_required)
        active_integrated = self.regions.get("1200000000")
        self.assertIsNotNone(active_integrated)
        assert active_integrated is not None
        self.assertEqual(RegionStatus.ACTIVE, active_integrated.status)

    def test_busan_detail_page_is_only_a_discovery_seed(self) -> None:
        busan = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "busan"
        )
        self.assertEqual("candidate", busan["status"])
        self.assertEqual(1, len(busan["discovery_seeds"]))
        seed = busan["discovery_seeds"][0]
        self.assertEqual("detail_candidate", seed["kind"])
        self.assertEqual(32, seed["input_reference"]["row"])
        self.assertEqual("candidate", seed["status"])

    def test_schema_rejects_missing_insecure_and_unknown_values(self) -> None:
        cases = []

        missing = copy.deepcopy(self.inventory)
        del missing["sources"][0]["home_url"]
        cases.append(missing)

        insecure = copy.deepcopy(self.inventory)
        insecure["sources"][0]["home_url"] = "http://example.test/"
        cases.append(insecure)

        unknown_status = copy.deepcopy(self.inventory)
        unknown_status["sources"][0]["status"] = "implemented"
        cases.append(unknown_status)

        for candidate in cases:
            with self.subTest():
                self.assertTrue(self.validator.schema_issues(candidate))


if __name__ == "__main__":
    unittest.main()
