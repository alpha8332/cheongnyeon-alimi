from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from collectors.eligibility import (
    EligibilityContractError,
    EligibilitySummary,
)
from collectors.eligibility_mapping import (
    map_bokjiro_eligibility,
    map_youthcenter_eligibility,
)
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.raw import RawPolicyDocument
from collectors.validation import JsonSchemaValidator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data/schema/eligibility_summary.schema.json"
FIXTURE_PATH = (
    ROOT / "data/fixtures/contracts/eligibility_evidence_cases.json"
)
RAW_ROOT = ROOT / "data/fixtures/raw"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class EligibilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.fixture = load_json(FIXTURE_PATH)
        cls.validator = JsonSchemaValidator(SCHEMA_PATH)

    def test_schema_and_python_field_sets_are_equal(self) -> None:
        self.assertEqual(
            "urn:cheongnyeon-alimi:schema:eligibility-summary:1.0.0",
            self.schema["$id"],
        )
        self.assertEqual(
            EligibilitySummary.FIELD_NAMES,
            frozenset(self.schema["properties"]),
        )
        self.assertEqual(
            EligibilitySummary.FIELD_NAMES,
            frozenset(self.schema["required"]),
        )

    def test_normal_boundary_long_missing_and_conflict_cases_are_valid(self) -> None:
        self.assertEqual("1.0.0", self.fixture["contract_version"])
        profiles = set()
        for case in self.fixture["cases"]:
            profiles.add(case["profile"])
            summary = case["summary"]
            self.assertEqual((), self.validator.schema_issues(summary))
            self.assertEqual(
                summary,
                EligibilitySummary.from_dict(summary).to_dict(),
            )
        self.assertEqual(
            {"normal", "boundary", "long", "missing", "conflict"},
            profiles,
        )

    def test_arrays_are_required_and_never_nullable(self) -> None:
        summary = copy.deepcopy(self.fixture["cases"][0]["summary"])
        summary["documents"] = None
        issues = self.validator.schema_issues(summary)
        self.assertTrue(any(issue.path == "$.documents" for issue in issues))
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(summary)

    def test_every_item_requires_source_evidence(self) -> None:
        summary = copy.deepcopy(self.fixture["cases"][0]["summary"])
        summary["requirements"][0]["evidence"] = []
        issues = self.validator.schema_issues(summary)
        self.assertTrue(
            any(issue.code == "schema_minItems" for issue in issues)
        )
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(summary)

    def test_personal_mobile_and_email_contacts_are_rejected(self) -> None:
        summary = copy.deepcopy(self.fixture["cases"][1]["summary"])
        summary["institutional_contacts"][0]["value"] = "010-1234-5678"
        self.assertTrue(self.validator.schema_issues(summary))
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(summary)

        summary["institutional_contacts"][0]["kind"] = "official_channel"
        summary["institutional_contacts"][0]["value"] = "문의 010-1234-5678"
        self.assertTrue(self.validator.schema_issues(summary))
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(summary)

        summary["institutional_contacts"][0]["value"] = "person@example.test"
        self.assertTrue(self.validator.schema_issues(summary))
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(summary)

    def test_complete_and_unknown_coverage_semantics_are_enforced(self) -> None:
        complete = copy.deepcopy(self.fixture["cases"][0]["summary"])
        complete["unknowns"] = copy.deepcopy(
            self.fixture["cases"][3]["summary"]["unknowns"]
        )
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(complete)

        unknown = copy.deepcopy(self.fixture["cases"][2]["summary"])
        unknown["documents"] = copy.deepcopy(
            self.fixture["cases"][1]["summary"]["documents"]
        )
        with self.assertRaises(EligibilityContractError):
            EligibilitySummary.from_dict(unknown)

    def test_api_source_mappers_preserve_field_locators(self) -> None:
        youth_documents = tuple(
            RawPolicyDocument.from_dict(load_json(path))
            for path in sorted((RAW_ROOT / "youthcenter-api").glob("*.json"))
        )
        youth = YouthCenterExtractor().extract(youth_documents)[0]
        youth_summary = map_youthcenter_eligibility(youth)
        self.assertEqual("partial", youth_summary.coverage.value)
        self.assertIn(
            "sprtTrgtAgeLmtYn",
            {
                evidence.locator
                for item in youth_summary.requirements
                for evidence in item.evidence
            },
        )

        bokjiro_documents = tuple(
            RawPolicyDocument.from_dict(load_json(path))
            for path in sorted(
                (RAW_ROOT / "bokjiro-central-welfare-api").glob("*.json")
            )
        )
        bokjiro = BokjiroExtractor().extract(bokjiro_documents)[0]
        bokjiro_summary = map_bokjiro_eligibility(bokjiro)
        self.assertEqual(
            ["tgtrDtlCn"],
            [item.evidence[0].locator for item in bokjiro_summary.requirements],
        )
        self.assertEqual(
            ["slctCritCn"],
            [item.evidence[0].locator for item in bokjiro_summary.unknowns],
        )
