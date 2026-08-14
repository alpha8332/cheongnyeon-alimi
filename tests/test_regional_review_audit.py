from __future__ import annotations

import unittest
from datetime import date

from collectors.regional_review_audit import (
    RegionalReviewAuditError,
    RegionalReviewAuditInput,
    build_regional_review_audit,
)


def decision(
    external_id: str,
    *reasons: str,
    organization: str | None = None,
    eligibility: str | None = None,
    source_region: str | None = None,
    application_period: str | None = None,
    field_observations: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "accepted": False,
        "application": "review_required",
        "reason_codes": list(reasons),
        "evidence": {
            "implementing_organization_text": organization,
            "region_eligibility_text": eligibility,
            "application_channel_text": None,
            "additional_benefit_text": None,
            "source_region_text": source_region,
            "application_period_text": application_period,
            "source_scope": None,
            "field_observations": field_observations or {},
        },
    }


class RegionalReviewAuditTests(unittest.TestCase):
    def test_report_reconciles_reasons_routes_and_unverifiable_nulls(self) -> None:
        report = build_regional_review_audit(
            (
                RegionalReviewAuditInput(
                    source_id="regional-a",
                    checkpoint_complete=True,
                    discovered_count=4,
                    captured_count=3,
                    checkpoint_outcomes=(
                        ("1", "review"),
                        ("2", "review"),
                        ("3", "accepted"),
                        ("4", "failed"),
                    ),
                    regional_decisions=(
                        decision(
                            "1",
                            "insufficient_regional_evidence",
                            "application_period_open",
                            "youth_target_confirmed",
                            application_period="상시",
                        ),
                        decision(
                            "2",
                            "insufficient_regional_evidence",
                            "application_period_missing",
                            "youth_target_unconfirmed",
                        ),
                        {
                            **decision(
                                "3",
                                "source_region_confirmed",
                                "application_period_open",
                                "youth_target_confirmed",
                                organization="A시",
                                eligibility="A시 청년",
                                source_region="A시",
                                application_period="상시",
                            ),
                            "accepted": True,
                            "application": "open",
                        },
                    ),
                ),
            ),
            audit_date=date(2026, 8, 13),
        )

        self.assertEqual(2, report["totals"]["review"])
        self.assertEqual(1, report["totals"]["failed"])
        self.assertTrue(report["totals"]["classification_reconciled"])
        self.assertEqual(0, report["totals"]["checkpoint_decision_drift"])
        source = report["sources"][0]
        self.assertEqual(2, source["review_routes"]["regional_evidence"])
        self.assertEqual(1, source["review_routes"]["application_state"])
        self.assertEqual(1, source["review_routes"]["youth_target"])
        self.assertEqual(
            {
                "present": 1,
                "source_value_absent": 0,
                "capture_contract_gap": 0,
                "null_unverifiable": 1,
            },
            source["review_evidence_coverage"]["application_period_text"],
        )
        self.assertTrue(source["capture_evidence_gap"])

    def test_checkpoint_and_replay_identity_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            RegionalReviewAuditError, "does not match checkpoint"
        ):
            RegionalReviewAuditInput(
                source_id="regional-a",
                checkpoint_complete=True,
                discovered_count=1,
                captured_count=1,
                checkpoint_outcomes=(("1", "review"),),
                regional_decisions=(decision("2", "reason"),),
            )

    def test_report_separates_source_absence_from_capture_gap(self) -> None:
        report = build_regional_review_audit(
            (
                RegionalReviewAuditInput(
                    source_id="regional-a",
                    checkpoint_complete=True,
                    discovered_count=2,
                    captured_count=2,
                    checkpoint_outcomes=(
                        ("1", "review"),
                        ("2", "review"),
                    ),
                    regional_decisions=(
                        decision(
                            "1",
                            "application_period_missing",
                            field_observations={
                                "application_period_text": (
                                    "label_present_value_empty"
                                )
                            },
                        ),
                        decision(
                            "2",
                            "application_period_missing",
                            field_observations={
                                "application_period_text": "label_not_found"
                            },
                        ),
                    ),
                ),
            ),
            audit_date=date(2026, 8, 13),
        )

        coverage = report["sources"][0]["review_evidence_coverage"][
            "application_period_text"
        ]
        self.assertEqual(1, coverage["source_value_absent"])
        self.assertEqual(1, coverage["capture_contract_gap"])
        self.assertEqual(0, coverage["null_unverifiable"])

    def test_duplicate_that_new_gate_would_review_is_reported_not_hidden(self) -> None:
        report = build_regional_review_audit(
            (
                RegionalReviewAuditInput(
                    source_id="regional-a",
                    checkpoint_complete=True,
                    discovered_count=1,
                    captured_count=1,
                    checkpoint_outcomes=(("1", "duplicate"),),
                    regional_decisions=(
                        decision(
                            "1",
                            "application_period_open",
                            "youth_target_unconfirmed",
                        ),
                    ),
                ),
            ),
            audit_date=date(2026, 8, 13),
        )

        self.assertEqual(1, report["totals"]["checkpoint_decision_drift"])
        self.assertEqual(
            1,
            report["sources"][0]["checkpoint_decision_drift"][
                "duplicate_now_unaccepted"
            ],
        )


if __name__ == "__main__":
    unittest.main()
