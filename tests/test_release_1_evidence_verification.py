from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.audit_release_1 import load_contract
from scripts.verify_release_1_evidence import (
    REQUIRED_CHECKS,
    build_verification_report,
)


class Release1EvidenceVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract, cls.digest = load_contract(
            Path("data/release_1_acceptance.json")
        )
        cls.template = json.loads(
            Path("docs/contest/release_1_evidence_template.json").read_text(
                encoding="utf-8"
            )
        )

    def technical_evidence(self) -> dict:
        return {
            "evidence_version": "1.0.0",
            "generated_at": "2026-08-06T03:34:01+00:00",
            "release": self.contract["release"],
            "gate": self.contract["gate"],
            "contract_sha256": self.digest,
            "dataset_baseline": self.contract["dataset_baseline"],
            "technical_verdict": "pass",
            "gate_verdict": "blocked",
            "gate_readiness": "technical-pass-evidence-pending",
            "required_manual_evidence": self.contract[
                "required_manual_evidence"
            ],
            "manual_review_policy": self.contract[
                "manual_review_policy"
            ],
            "scenarios": [
                {
                    "id": scenario["id"],
                    "status": "pass",
                    "elapsed_ms": 10.0,
                    "query": scenario["params"]["q"],
                    "target": {
                        "rank": 1,
                        "unknown_count": 0,
                        "verdicts": scenario["required_verdicts"],
                        "categories": scenario["expected_policy"][
                            "required_categories"
                        ],
                        **scenario["expected_policy"]["required_fields"],
                        **{
                            field: scenario["expected_policy"][field]
                            for field in ("source_id", "external_id", "title")
                        },
                    },
                }
                for scenario in self.contract["scenarios"]
            ],
        }

    def completed_manual_evidence(self) -> dict:
        evidence = copy.deepcopy(self.template)
        for review in evidence["reviews"]:
            review["reviewer"] = f"{review['role']}-reviewer"
            review["performed_at"] = "2026-08-06T15:00:00+09:00"
            review["independence_confirmed"] = True
            review["verdict"] = "pass"
            for check in review["checks"]:
                check["status"] = "pass"
                check["notes"] = "승인 기준과 실제 관찰 결과가 일치함."
                check["evidence_refs"] = [
                    "docs/contest/release_1_technical_evidence.json"
                ]
        return evidence

    def build(self, manual: dict, technical: dict | None = None) -> dict:
        return build_verification_report(
            contract=self.contract,
            contract_sha256=self.digest,
            technical_evidence=technical or self.technical_evidence(),
            manual_evidence=manual,
        )

    def test_template_is_bound_to_current_contract_and_required_checks(self) -> None:
        self.assertEqual(self.digest, self.template["contract_sha256"])
        self.assertEqual(
            self.contract["dataset_baseline"],
            self.template["dataset_baseline"],
        )
        self.assertEqual(
            list(REQUIRED_CHECKS),
            [review["role"] for review in self.template["reviews"]],
        )
        for review in self.template["reviews"]:
            self.assertEqual(
                list(REQUIRED_CHECKS[review["role"]]),
                [check["id"] for check in review["checks"]],
            )

    def test_pending_template_cannot_reach_team_leader_decision(self) -> None:
        report = self.build(copy.deepcopy(self.template))

        self.assertEqual("manual-evidence-pending", report["gate_readiness"])
        self.assertEqual("blocked", report["gate_verdict"])
        self.assertIn("REVIEW_PENDING", report["blocker_codes"])

    def test_complete_manual_reviews_are_ready_but_do_not_pass_gate(self) -> None:
        report = self.build(self.completed_manual_evidence())

        self.assertEqual(
            "ready-for-team-leader-decision",
            report["gate_readiness"],
        )
        self.assertEqual("blocked", report["gate_verdict"])
        self.assertEqual([], report["blockers"])

    def test_lightweight_review_does_not_require_role_independence(self) -> None:
        manual = self.completed_manual_evidence()
        for review in manual["reviews"]:
            review["independence_confirmed"] = False

        report = self.build(manual)

        self.assertEqual(
            "ready-for-team-leader-decision",
            report["gate_readiness"],
        )
        self.assertEqual([], report["blockers"])

    def test_contract_hash_mismatch_is_rejected(self) -> None:
        manual = self.completed_manual_evidence()
        manual["contract_sha256"] = "0" * 64

        report = self.build(manual)

        self.assertEqual("manual-evidence-pending", report["gate_readiness"])
        self.assertIn("EVIDENCE_IDENTITY_MISMATCH", report["blocker_codes"])

    def test_blocked_qa_check_blocks_readiness(self) -> None:
        manual = self.completed_manual_evidence()
        qa = manual["reviews"][0]
        qa["verdict"] = "blocked"
        qa["checks"][0]["status"] = "blocked"
        qa["checks"][0]["notes"] = "첫 결과가 기대 정책과 다름."

        report = self.build(manual)

        self.assertEqual(
            "manual-evidence-blocked",
            report["gate_readiness"],
        )
        self.assertEqual("blocked", report["gate_verdict"])

    def test_technical_query_drift_blocks_manual_evidence(self) -> None:
        technical = self.technical_evidence()
        technical["scenarios"][0]["query"] = "변경된 검색어"

        report = self.build(self.completed_manual_evidence(), technical)

        self.assertEqual("technical-evidence-invalid", report["gate_readiness"])
        self.assertIn("TECHNICAL_QUERY_MISMATCH", report["blocker_codes"])

    def test_tampered_technical_rank_blocks_manual_evidence(self) -> None:
        technical = self.technical_evidence()
        technical["scenarios"][1]["target"]["rank"] = 2

        report = self.build(self.completed_manual_evidence(), technical)

        self.assertEqual("technical-evidence-invalid", report["gate_readiness"])
        self.assertIn("TECHNICAL_TARGET_RANK_INVALID", report["blocker_codes"])

    def test_technical_evidence_cannot_claim_gate_pass(self) -> None:
        technical = self.technical_evidence()
        technical["gate_verdict"] = "pass"

        report = self.build(self.completed_manual_evidence(), technical)

        self.assertEqual("technical-evidence-invalid", report["gate_readiness"])
        self.assertIn("TECHNICAL_GATE_VERDICT_INVALID", report["blocker_codes"])

    def test_missing_evidence_reference_blocks_readiness(self) -> None:
        manual = self.completed_manual_evidence()
        manual["reviews"][0]["checks"][0]["evidence_refs"] = [
            "docs/contest/missing-evidence.png"
        ]

        report = self.build(manual)

        self.assertEqual("manual-evidence-pending", report["gate_readiness"])
        self.assertIn("CHECK_EVIDENCE_MISSING", report["blocker_codes"])


if __name__ == "__main__":
    unittest.main()
