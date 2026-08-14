from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from collectors.regional_sources import RegionalSourceInventoryValidator
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
        cls.schema_validator = JsonSchemaValidator(SCHEMA_PATH)
        cls.domain_validator = RegionalSourceInventoryValidator(
            SCHEMA_PATH,
            require_decisions=True,
        )
        cls.regions = RegionReference.from_seed_files(
            REGION_SEED, ALIAS_SEED
        )

    def test_inventory_matches_schema_and_domain_contract(self) -> None:
        self.assertEqual(
            (), self.schema_validator.schema_issues(self.inventory)
        )
        self.assertEqual((), self.domain_validator.issues(self.inventory))
        self.assertEqual("1.2.0", self.inventory["schema_version"])
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

    def test_home_urls_are_unique_public_https(self) -> None:
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

    def test_ryp1_has_a_decision_for_every_source(self) -> None:
        statuses: dict[str, int] = {}
        for source in self.inventory["sources"]:
            status = source["status"]
            statuses[status] = statuses.get(status, 0) + 1
            self.assertNotEqual("candidate", status)
            self.assertTrue(source["decision_reason"])
            self.assertNotEqual(
                "unchecked", source["preflight"]["operator"]
            )
            self.assertNotEqual(
                "unchecked", source["preflight"]["browser_access"]
            )
            self.assertIsNotNone(
                source["preflight"]["last_checked_at"]
            )
        self.assertEqual(
            {"approved": 13, "blocked": 3, "rejected": 1},
            statuses,
        )

    def test_browser_discovery_reaches_details_for_all_sources(self) -> None:
        discovery_statuses: dict[str, int] = {}
        modes: dict[str, int] = {}
        for source in self.inventory["sources"]:
            discovery = source["discovery"]
            discovery_statuses[discovery["status"]] = (
                discovery_statuses.get(discovery["status"], 0) + 1
            )
            modes[discovery["collection_mode"]] = (
                modes.get(discovery["collection_mode"], 0) + 1
            )
            self.assertEqual("goto", discovery["actions"][0]["kind"])

        self.assertEqual(
            {"extraction_ready": 17},
            discovery_statuses,
        )
        self.assertEqual(
            {"http_html": 8, "http_json": 1, "browser": 4, "none": 4},
            modes,
        )

        gyeongbuk = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "gyeongbuk"
        )
        self.assertEqual("approved", gyeongbuk["status"])
        self.assertEqual("allowed", gyeongbuk["preflight"]["robots"])
        self.assertEqual(
            "extraction_ready", gyeongbuk["discovery"]["status"]
        )
        self.assertEqual(
            "http_json", gyeongbuk["discovery"]["collection_mode"]
        )
        self.assertEqual(
            "1098", gyeongbuk["discovery"]["sample_external_id"]
        )
        self.assertEqual(
            ["https://gbyouth.go.kr/policy/list.json"],
            gyeongbuk["approved_list_urls"],
        )
        self.assertEqual(
            [
                "POST https://gbyouth.go.kr/policy/detail.modal "
                "(no={positive_integer})"
            ],
            gyeongbuk["approved_detail_url_patterns"],
        )
        self.assertEqual(243, gyeongbuk["discovery"]["observed_list_count"])
        self.assertIsNone(gyeongbuk["discovery"]["failure_reason"])

    def test_gyeongnam_approves_the_detail_page_and_backing_json(self) -> None:
        gyeongnam = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "gyeongnam"
        )

        self.assertEqual(
            [
                "https://youth.gyeongnam.go.kr/youth/"
                "youthPolicySearchViewNew.es?mid=a10101020000"
                "&policy_no={positive_integer}",
                "GET https://youth.gyeongnam.go.kr/youth/"
                "youthPolicyInfoNew.es?policy_no={positive_integer}",
            ],
            gyeongnam["approved_detail_url_patterns"],
        )

    def test_ryp6_has_one_final_implementation_status_per_region(self) -> None:
        statuses: dict[str, int] = {}
        for source in self.inventory["sources"]:
            status = source["implementation_status"]
            statuses[status] = statuses.get(status, 0) + 1
        self.assertEqual(
            {
                "implemented_http": 2,
                "implemented_browser": 11,
                "blocked": 3,
                "rejected": 1,
            },
            statuses,
        )

    def test_approved_sources_have_execution_boundaries(self) -> None:
        approved = [
            source
            for source in self.inventory["sources"]
            if source["status"] == "approved"
        ]
        self.assertEqual(13, len(approved))
        self.assertEqual(
            len(approved), len({source["source_id"] for source in approved})
        )
        for source in approved:
            with self.subTest(source=source["jurisdiction_key"]):
                self.assertTrue(source["source_id"])
                self.assertTrue(source["approved_list_urls"])
                self.assertTrue(source["approved_detail_url_patterns"])
                self.assertEqual(
                    {
                        "max_list_requests": 1,
                        "max_detail_requests": 3,
                        "minimum_interval_seconds": 2.0,
                    },
                    source["request_budget"],
                )
                discovery = source["discovery"]
                self.assertEqual("extraction_ready", discovery["status"])
                self.assertNotEqual("none", discovery["collection_mode"])
                self.assertEqual(
                    "available", source["preflight"]["browser_access"]
                )
                self.assertTrue(discovery["sample_external_id"])
                self.assertTrue(discovery["sample_title"])
                self.assertIn(
                    "observe_detail",
                    {action["kind"] for action in discovery["actions"]},
                )
                if discovery["collection_mode"] != "browser":
                    self.assertEqual(
                        "available",
                        source["preflight"]["technical_access"],
                    )

    def test_browser_mode_can_approve_a_http_blocked_source(self) -> None:
        seoul = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "seoul"
        )
        self.assertEqual("approved", seoul["status"])
        self.assertEqual("blocked", seoul["preflight"]["technical_access"])
        self.assertEqual("available", seoul["preflight"]["browser_access"])
        self.assertEqual("browser", seoul["discovery"]["collection_mode"])

    def test_robots_blocked_sources_preserve_discovery_evidence(self) -> None:
        blocked = {
            source["jurisdiction_key"]: source
            for source in self.inventory["sources"]
            if source["status"] == "blocked"
        }
        self.assertEqual(
            {"sejong", "gyeonggi", "chungnam"},
            set(blocked),
        )
        for key in {"sejong", "gyeonggi", "chungnam"}:
            self.assertEqual(
                "extraction_ready", blocked[key]["discovery"]["status"]
            )
            self.assertEqual("disallowed", blocked[key]["preflight"]["robots"])

    def test_inactive_sources_have_no_execution_boundary(self) -> None:
        inactive = [
            source
            for source in self.inventory["sources"]
            if source["status"] in {"blocked", "rejected"}
        ]
        self.assertEqual(4, len(inactive))
        for source in inactive:
            with self.subTest(source=source["jurisdiction_key"]):
                self.assertIsNone(source["source_id"])
                self.assertEqual([], source["approved_list_urls"])
                self.assertEqual(
                    [], source["approved_detail_url_patterns"]
                )
                self.assertIsNone(source["request_budget"])
                self.assertEqual(
                    "none", source["discovery"]["collection_mode"]
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

        self.assertEqual({"전남"}, review_required)
        gwangju = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "gwangju"
        )
        self.assertEqual(
            "1200000000", gwangju["region_reference"]["active_code"]
        )

    def test_busan_detail_page_remains_only_a_discovery_seed(self) -> None:
        busan = next(
            source
            for source in self.inventory["sources"]
            if source["jurisdiction_key"] == "busan"
        )
        self.assertEqual("approved", busan["status"])
        self.assertEqual(1, len(busan["discovery_seeds"]))
        seed = busan["discovery_seeds"][0]
        self.assertEqual("detail_candidate", seed["kind"])
        self.assertEqual(32, seed["input_reference"]["row"])
        self.assertEqual("candidate", seed["status"])
        self.assertNotIn(seed["url"], busan["approved_list_urls"])

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
                self.assertTrue(
                    self.schema_validator.schema_issues(candidate)
                )

    def test_domain_rejects_invalid_cross_field_combinations(self) -> None:
        approved_index = next(
            index
            for index, source in enumerate(self.inventory["sources"])
            if source["status"] == "approved"
        )
        blocked_index = next(
            index
            for index, source in enumerate(self.inventory["sources"])
            if source["status"] == "blocked"
        )
        cases = []

        missing_source_id = copy.deepcopy(self.inventory)
        missing_source_id["sources"][approved_index]["source_id"] = None
        cases.append(missing_source_id)

        robots_disallowed = copy.deepcopy(self.inventory)
        robots_disallowed["sources"][approved_index]["preflight"][
            "robots"
        ] = "disallowed"
        cases.append(robots_disallowed)

        unsafe_budget = copy.deepcopy(self.inventory)
        unsafe_budget["sources"][approved_index]["request_budget"][
            "minimum_interval_seconds"
        ] = 0
        cases.append(unsafe_budget)

        inactive_budget = copy.deepcopy(self.inventory)
        inactive_budget["sources"][blocked_index]["request_budget"] = {
            "max_list_requests": 1,
            "max_detail_requests": 1,
            "minimum_interval_seconds": 2,
        }
        cases.append(inactive_budget)

        inactive_collection = copy.deepcopy(self.inventory)
        inactive_collection["sources"][blocked_index]["discovery"][
            "collection_mode"
        ] = "browser"
        cases.append(inactive_collection)

        missing_sample = copy.deepcopy(self.inventory)
        missing_sample["sources"][approved_index]["discovery"][
            "sample_external_id"
        ] = None
        cases.append(missing_sample)

        missing_detail_evidence = copy.deepcopy(self.inventory)
        actions = missing_detail_evidence["sources"][approved_index][
            "discovery"
        ]["actions"]
        missing_detail_evidence["sources"][approved_index]["discovery"][
            "actions"
        ] = [
            action for action in actions if action["kind"] != "observe_detail"
        ]
        cases.append(missing_detail_evidence)

        browser_unavailable = copy.deepcopy(self.inventory)
        browser_unavailable["sources"][approved_index]["preflight"][
            "browser_access"
        ] = "blocked"
        cases.append(browser_unavailable)

        http_index = next(
            index
            for index, source in enumerate(self.inventory["sources"])
            if source["discovery"]["collection_mode"] == "http_html"
        )
        http_unavailable = copy.deepcopy(self.inventory)
        http_unavailable["sources"][http_index]["preflight"][
            "technical_access"
        ] = "blocked"
        cases.append(http_unavailable)

        invalid_mapping = copy.deepcopy(self.inventory)
        invalid_mapping["sources"][approved_index]["region_reference"][
            "active_code"
        ] = None
        cases.append(invalid_mapping)

        undecided = copy.deepcopy(self.inventory)
        undecided["sources"][blocked_index]["status"] = "candidate"
        cases.append(undecided)

        for candidate in cases:
            with self.subTest():
                self.assertTrue(self.domain_validator.issues(candidate))


if __name__ == "__main__":
    unittest.main()
