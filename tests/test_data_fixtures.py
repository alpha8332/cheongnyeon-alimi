from __future__ import annotations

import json
import re
import socket
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.normalized import DataQualityStatus, NormalizedProgram
from collectors.normalizer import Normalizer
from collectors.raw import RawDocumentRole, RawPolicyDocument
from collectors.validation import NormalizedProgramValidator
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID
from scripts.build_data_fixtures import build_outputs, check_outputs, main


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/fixtures/raw"
EXTRACTED_PATH = ROOT / "data/fixtures/extracted/policies.json"
NORMALIZED_PATH = ROOT / "data/fixtures/normalized/programs.json"
REJECTED_PATH = ROOT / "data/fixtures/rejected/programs.json"
SEED_PATH = ROOT / "data/seeds/initial_programs.json"
SEARCH_CONTRACT_PATH = (
    ROOT / "data/fixtures/contracts/policy_search_region_cases.json"
)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_raw_documents() -> tuple[RawPolicyDocument, ...]:
    return tuple(
        RawPolicyDocument.from_dict(load_json(path))
        for path in sorted(RAW_ROOT.rglob("*.json"))
    )


class DataFixtureContractTests(unittest.TestCase):
    def test_committed_outputs_match_deterministic_generation(self) -> None:
        self.assertEqual((), check_outputs(build_outputs()))
        self.assertEqual(0, main(["--check"]))

    def test_generation_does_not_use_external_network(self) -> None:
        with patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network access is not allowed"),
        ) as connection:
            outputs = build_outputs()

        self.assertEqual(13, len(outputs))
        connection.assert_not_called()

    def test_raw_fixtures_are_synthetic_and_contract_valid(self) -> None:
        documents = load_raw_documents()
        roles = Counter(document.document_role for document in documents)

        self.assertEqual(8, len(documents))
        self.assertEqual(2, roles[RawDocumentRole.LIST_RESPONSE])
        self.assertEqual(5, roles[RawDocumentRole.LIST_ITEM])
        self.assertEqual(1, roles[RawDocumentRole.DETAIL_RESPONSE])
        self.assertEqual(8, len({document.document_id for document in documents}))
        for document in documents:
            self.assertEqual(
                RawPolicyDocument.FIELD_NAMES,
                frozenset(document.to_dict()),
            )
            self.assertEqual(
                "fixture.invalid",
                document.source_url.split("/")[2],
            )
            self.assertNotIn(b"apiKey", document.raw_bytes)
            self.assertNotIn(b"serviceKey", document.raw_bytes)

    def test_outputs_exclude_credentials_and_personal_identifiers(
        self,
    ) -> None:
        fixture_text = "\n".join(
            content.decode("utf-8")
            for content in build_outputs().values()
        )

        for credential_name in (
            "apiKeyNm",
            "openApiVlak",
            "serviceKey",
        ):
            self.assertNotIn(credential_name, fixture_text)
        self.assertIsNone(
            re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                fixture_text,
            )
        )
        self.assertIsNone(
            re.search(r"\b01[016789]-?\d{3,4}-?\d{4}\b", fixture_text)
        )
        self.assertIsNone(
            re.search(r"\b\d{6}-[1-4]\d{6}\b", fixture_text)
        )

    def test_extracted_fixture_is_reproduced_from_raw(self) -> None:
        documents = load_raw_documents()
        extracted = [
            *YouthCenterExtractor().extract(documents),
            *BokjiroExtractor().extract(documents),
        ]

        self.assertEqual(
            [policy.to_dict() for policy in extracted],
            load_json(EXTRACTED_PATH),
        )
        self.assertEqual(5, len(extracted))

    def test_committed_raw_replays_through_validation_to_seed(
        self,
    ) -> None:
        documents = load_raw_documents()
        extracted = [
            *YouthCenterExtractor().extract(documents),
            *BokjiroExtractor().extract(documents),
        ]
        results = [
            Normalizer().normalize(policy)
            for policy in extracted
        ]
        accepted = [
            result.program.to_dict()
            for result in results
            if result.program is not None
        ]
        rejected = [
            {
                "source_id": result.candidate.get("source_id"),
                "external_id": result.candidate.get("external_id"),
                "status": result.status.value,
                "candidate": result.candidate,
                "issues": [
                    issue.to_dict()
                    for issue in result.issues
                ],
            }
            for result in results
            if result.program is None
        ]

        self.assertEqual(load_json(SEED_PATH), accepted)
        self.assertEqual(load_json(REJECTED_PATH), rejected)
        self.assertEqual(
            Counter(
                {
                    DataQualityStatus.VALID: 2,
                    DataQualityStatus.PARTIAL: 2,
                    DataQualityStatus.INVALID: 1,
                }
            ),
            Counter(result.status for result in results),
        )

    def test_seed_is_schema_valid_and_excludes_invalid_results(self) -> None:
        validator = NormalizedProgramValidator()
        seed = load_json(SEED_PATH)
        assert isinstance(seed, list)
        results = [validator.validate(candidate) for candidate in seed]

        self.assertEqual(4, len(results))
        self.assertTrue(all(result.program is not None for result in results))
        self.assertEqual(
            Counter(
                {
                    DataQualityStatus.VALID: 2,
                    DataQualityStatus.PARTIAL: 2,
                }
            ),
            Counter(result.status for result in results),
        )
        self.assertEqual(
            Counter(
                {
                    YOUTHCENTER_SOURCE_ID: 2,
                    BOKJIRO_SOURCE_ID: 2,
                }
            ),
            Counter(candidate["source_id"] for candidate in seed),
        )
        self.assertTrue(
            all(
                candidate["data_quality_status"] != "invalid"
                for candidate in seed
            )
        )

    def test_seed_preserves_consumer_representations(self) -> None:
        seed = load_json(SEED_PATH)
        assert isinstance(seed, list)

        self.assertTrue(
            all(
                frozenset(candidate) == NormalizedProgram.FIELD_NAMES
                for candidate in seed
            )
        )
        self.assertTrue(
            all(candidate["schema_version"] == "1.1.0" for candidate in seed)
        )
        for candidate in seed:
            self.assertEqual([], candidate["keywords"])
            self.assertEqual([], candidate["life_stages"])
            self.assertEqual([], candidate["target_groups"])
            self.assertEqual("unknown", candidate["coverage_scope"])
            self.assertEqual([], candidate["region_rules"])
        self.assertTrue(
            any(candidate["application_start"] is None for candidate in seed)
        )
        self.assertTrue(any(candidate["regions"] == [] for candidate in seed))
        self.assertTrue(
            any(len(candidate["categories"]) > 1 for candidate in seed)
        )
        self.assertEqual(
            {"always", "fixed_period", None},
            {
                candidate["application_schedule"]
                for candidate in seed
            },
        )
        self.assertEqual(
            {"closed", "open", None},
            {candidate["application_status"] for candidate in seed},
        )
        self.assertIn(
            "2026-01-01",
            {
                candidate["application_start"]
                for candidate in seed
            },
        )
        self.assertTrue(
            any(
                item["document_role"] == "detail_response"
                for candidate in seed
                for item in candidate["provenance"]
            )
        )

    def test_normalized_fixture_and_seed_are_the_same_contract(self) -> None:
        self.assertEqual(
            NORMALIZED_PATH.read_bytes(),
            SEED_PATH.read_bytes(),
        )
        self.assertEqual([], list((ROOT / "data").rglob("*.csv")))

    def test_search_region_contract_cases_cover_approved_boundaries(
        self,
    ) -> None:
        cases = load_json(SEARCH_CONTRACT_PATH)
        assert isinstance(cases, list)
        self.assertEqual(
            {
                "nationwide",
                "regional_parent",
                "regional_exact",
                "regional_exclusion",
                "unknown",
                "ambiguous",
                "retired_code",
            },
            {case["case_id"] for case in cases},
        )

        validator = NormalizedProgramValidator()
        for case in cases:
            result = validator.validate(case["program"])
            self.assertIsNotNone(
                result.program,
                msg=(
                    case["case_id"],
                    [issue.to_dict() for issue in result.issues],
                ),
            )

        by_id = {
            case["case_id"]: case["program"]
            for case in cases
        }
        self.assertEqual(
            "nationwide",
            by_id["nationwide"]["coverage_scope"],
        )
        self.assertEqual([], by_id["nationwide"]["region_rules"])
        self.assertEqual("unknown", by_id["unknown"]["coverage_scope"])
        self.assertEqual([], by_id["unknown"]["region_rules"])
        self.assertEqual(
            "ambiguous",
            by_id["ambiguous"]["region_rules"][0][
                "resolution_status"
            ],
        )
        self.assertEqual(
            {"include", "exclude"},
            {
                rule["relation"]
                for rule in by_id["regional_exclusion"][
                    "region_rules"
                ]
            },
        )
        self.assertEqual(
            "fixture-kr-2020",
            by_id["retired_code"]["region_rules"][0][
                "region_scheme"
            ],
        )

    def test_rejected_fixture_records_exact_failure_reason(self) -> None:
        rejected = load_json(REJECTED_PATH)
        assert isinstance(rejected, list)

        self.assertEqual(1, len(rejected))
        self.assertEqual("invalid", rejected[0]["status"])
        self.assertEqual(
            [("$.title", "schema_type", "error")],
            [
                (
                    issue["path"],
                    issue["code"],
                    issue["severity"],
                )
                for issue in rejected[0]["issues"]
            ],
        )
        self.assertIsNone(rejected[0]["candidate"]["title"])
        seed_ids = {
            item["external_id"]
            for item in load_json(SEED_PATH)
        }
        self.assertNotIn(rejected[0]["external_id"], seed_ids)


if __name__ == "__main__":
    unittest.main()
