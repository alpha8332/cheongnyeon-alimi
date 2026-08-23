from __future__ import annotations

import json
import tempfile
import unittest
import sys
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.models.policy import Policy
from collectors.normalized import NormalizedProgram
from scripts.build_public_bootstrap_dataset import (
    DEFAULT_CONTRACT,
    PublicDatasetError,
    content_safety_counts,
    enforce_content_safety,
    load_source_contract,
    policy_to_normalized_program,
    select_safe_records,
    verify_release,
    write_release,
)

FIXTURE_PATH = ROOT / "data/fixtures/normalized/programs.json"


def public_program() -> dict[str, object]:
    program = deepcopy(
        json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0]
    )
    program["source_id"] = "bokjiro-central-welfare-api"
    program["source_name"] = "한국사회보장정보원 중앙부처복지서비스"
    program["external_id"] = "TEST-PUBLIC-001"
    program["source_url"] = "https://example.invalid/public/TEST-PUBLIC-001"
    for collection_name in (
        "requirements",
        "exclusions",
        "preferences",
        "documents",
        "unknowns",
        "institutional_contacts",
    ):
        for item in program["eligibility_summary"][collection_name]:
            for evidence in item["evidence"]:
                evidence["source_id"] = program["source_id"]
                evidence["source_url"] = program["source_url"]
    for provenance in program["provenance"]:
        provenance["source_url"] = "https://example.invalid/public"
    return program


def policy_from_program(program: dict[str, object]) -> Policy:
    values = {
        field_name: program[field_name]
        for field_name in NormalizedProgram.FIELD_NAMES
        if field_name != "region_rules"
    }
    for field_name in ("application_start", "application_end"):
        if values[field_name] is not None:
            values[field_name] = date.fromisoformat(values[field_name])
    values["collected_at"] = datetime.fromisoformat(values["collected_at"])
    return Policy(id=1, **values)


class PublicBootstrapDatasetTest(unittest.TestCase):
    def test_contract_is_default_deny_and_matches_normalized_fields(self) -> None:
        contract = load_source_contract(DEFAULT_CONTRACT)

        self.assertEqual(contract["default_decision"], "exclude")
        self.assertEqual(
            [item["source_id"] for item in contract["included_sources"]],
            ["bokjiro-central-welfare-api"],
        )
        self.assertEqual(
            frozenset(contract["normalized_program"]["allowed_fields"]),
            NormalizedProgram.FIELD_NAMES,
        )

    def test_release_round_trip_has_stable_hash_and_manifest(self) -> None:
        contract = load_source_contract(DEFAULT_CONTRACT)
        record = policy_to_normalized_program(
            policy_from_program(public_program())
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            dataset_path, manifest_path, manifest = write_release(
                records=[record],
                contract=contract,
                contract_path=DEFAULT_CONTRACT,
                output_dir=output_dir,
                dataset_version="public-bootstrap-20260823-aaaaaaa",
                generated_at="2026-08-23T00:00:00+00:00",
                git_sha="a" * 40,
            )

            verified = verify_release(manifest_path)

            self.assertEqual(verified, manifest)
            self.assertEqual(manifest["artifact"]["row_count"], 1)
            self.assertEqual(manifest["sources"][0]["row_count"], 1)
            self.assertTrue(dataset_path.is_file())

    def test_verifier_rejects_modified_artifact(self) -> None:
        contract = load_source_contract(DEFAULT_CONTRACT)
        record = policy_to_normalized_program(
            policy_from_program(public_program())
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            dataset_path, manifest_path, _ = write_release(
                records=[record],
                contract=contract,
                contract_path=DEFAULT_CONTRACT,
                output_dir=Path(temporary_directory),
                dataset_version="public-bootstrap-20260823-bbbbbbb",
                generated_at="2026-08-23T00:00:00+00:00",
                git_sha="b" * 40,
            )
            dataset_path.write_bytes(dataset_path.read_bytes() + b" ")

            with self.assertRaisesRegex(
                PublicDatasetError, "dataset sha256 mismatch"
            ):
                verify_release(manifest_path)

    def test_content_safety_rejects_contacts_and_secret_query(self) -> None:
        contract = load_source_contract(DEFAULT_CONTRACT)
        record = public_program()
        record["summary"] = "contact test@example.com or 010-1234-5678"
        record["source_url"] = "https://example.invalid/?serviceKey=secret"
        record["eligibility_summary"]["institutional_contacts"] = [
            {
                "kind": "phone",
                "label": "문의",
                "value": "02-0000-0000",
                "evidence": [],
            }
        ]

        counts = content_safety_counts([record], contract)

        self.assertEqual(counts["institutional_contact_count"], 1)
        self.assertEqual(counts["email_match_count"], 1)
        self.assertEqual(counts["personal_mobile_match_count"], 1)
        self.assertEqual(counts["forbidden_query_key_match_count"], 1)
        with self.assertRaises(PublicDatasetError):
            enforce_content_safety(counts)

        selected, selection = select_safe_records(
            [public_program(), record], contract
        )
        self.assertEqual(len(selected), 1)
        self.assertEqual(selection["candidate_row_count"], 2)
        self.assertEqual(selection["published_row_count"], 1)
        self.assertEqual(selection["excluded_row_count"], 1)
        self.assertEqual(
            selection["excluded_reason_row_counts"],
            {
                "email": 1,
                "forbidden_query_key": 1,
                "institutional_contact": 1,
                "personal_mobile": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
