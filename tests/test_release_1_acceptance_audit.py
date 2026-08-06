from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_release_1 import (
    AcceptanceAuditError,
    build_report,
    evaluate_scenario,
    load_contract,
    normalize_base_url,
)


def passing_payload() -> dict:
    return {
        "total": 1,
        "interpreted_conditions": {
            "q_raw": "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?",
            "conditions": [
                {
                    "dimension": "age",
                    "value": 27,
                    "resolution": "resolved",
                    "candidates": [],
                },
                {
                    "dimension": "region",
                    "value": "충청남도 천안시",
                    "resolution": "resolved",
                    "candidates": ["충청남도 천안시"],
                },
            ],
        },
        "items": [
            {
                "policy": {
                    "source_id": "youthcenter-api",
                    "external_id": "20260430005400212969",
                    "title": "청년단기숙소 지원사업",
                    "data_quality_status": "valid",
                    "application_status": "open",
                    "application_schedule": "always",
                    "categories": ["housing"],
                },
                "score": 20.0,
                "unknown_count": 0,
                "verdicts": {
                    "region": "match",
                    "age": "match",
                    "status": None,
                    "category": None,
                },
            }
        ],
    }


class Release1AcceptanceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        contract, digest = load_contract(
            Path("data/release_1_acceptance.json")
        )
        cls.contract = contract
        cls.digest = digest
        cls.golden = contract["scenarios"][0]

    def test_contract_locks_approved_open_short_stay_policy(self) -> None:
        expected = self.golden["expected_policy"]

        self.assertEqual("v0.1.0", self.contract["release"])
        self.assertEqual("youthcenter-api", expected["source_id"])
        self.assertEqual("20260430005400212969", expected["external_id"])
        self.assertEqual(20, self.golden["maximum_rank"])
        self.assertEqual(2000, self.golden["maximum_elapsed_ms"])
        self.assertEqual(64, len(self.digest))

    def test_passing_payload_satisfies_golden_scenario(self) -> None:
        result = evaluate_scenario(
            self.golden,
            passing_payload(),
            elapsed_ms=12.5,
        )

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(1, result["target"]["rank"])

    def test_expected_policy_below_first_page_blocks_release(self) -> None:
        payload = passing_payload()
        filler = copy.deepcopy(payload["items"][0])
        filler["policy"]["external_id"] = "other"
        filler["policy"]["title"] = "다른 정책"
        payload["items"] = [copy.deepcopy(filler) for _ in range(20)] + payload["items"]

        result = evaluate_scenario(
            self.golden,
            payload,
            elapsed_ms=50.0,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "EXPECTED_POLICY_RANK_TOO_LOW",
            {blocker["code"] for blocker in result["blockers"]},
        )
        self.assertEqual(21, result["target"]["rank"])

    def test_unknown_or_closed_expected_policy_blocks_release(self) -> None:
        payload = passing_payload()
        payload["items"][0]["unknown_count"] = 1
        payload["items"][0]["policy"]["application_status"] = "closed"

        result = evaluate_scenario(
            self.golden,
            payload,
            elapsed_ms=10.0,
        )
        codes = {blocker["code"] for blocker in result["blockers"]}

        self.assertIn("EXPECTED_POLICY_UNKNOWN_CONDITIONS", codes)
        self.assertIn("EXPECTED_POLICY_FIELD_MISMATCH", codes)

    def test_response_time_over_budget_blocks_release(self) -> None:
        result = evaluate_scenario(
            self.golden,
            passing_payload(),
            elapsed_ms=2000.01,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "RESPONSE_TIME_BUDGET_EXCEEDED",
            {blocker["code"] for blocker in result["blockers"]},
        )

    def test_technical_pass_still_requires_manual_evidence(self) -> None:
        scenario_result = evaluate_scenario(
            self.golden,
            passing_payload(),
            elapsed_ms=10.0,
        )
        report = build_report(
            contract=self.contract,
            contract_sha256=self.digest,
            base_url="http://127.0.0.1:8000",
            results=[scenario_result],
        )

        self.assertEqual("pass", report["technical_verdict"])
        self.assertEqual("blocked", report["gate_verdict"])
        self.assertEqual(
            "technical-pass-evidence-pending",
            report["gate_readiness"],
        )
        self.assertEqual(
            ["qa", "usability-review"],
            report["required_manual_evidence"],
        )
        self.assertEqual(
            "lightweight-team-review",
            report["manual_review_policy"]["mode"],
        )

    def test_base_url_rejects_credentials(self) -> None:
        self.assertEqual(
            "http://127.0.0.1:8000",
            normalize_base_url("http://127.0.0.1:8000/"),
        )
        with self.assertRaises(AcceptanceAuditError):
            normalize_base_url("http://user:secret@127.0.0.1:8000")

    def test_contract_rejects_invalid_release_limit(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["scenarios"][0]["maximum_rank"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(
                json.dumps(contract, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(AcceptanceAuditError):
                load_contract(path)


if __name__ == "__main__":
    unittest.main()
