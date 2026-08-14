from __future__ import annotations

from collectors.regional_ryp9_audit import build_regional_ryp9_audit


def _decision(external_id: str, outcome: str) -> dict[str, str]:
    return {"external_id": external_id, "outcome": outcome}


def _regional(external_id: str, *, closed: bool) -> dict[str, object]:
    return {
        "external_id": external_id,
        "accepted": False,
        "application": "closed" if closed else "open",
        "reason_codes": [
            "application_period_ended" if closed else "youth_target_unconfirmed"
        ],
        "evidence": {
            "provenance": [
                {"document_role": "list_response"},
                {"document_role": "list_item"},
                {"document_role": "detail_response"},
            ]
        },
    }


def test_ryp9_audit_accepts_evidenced_closed_and_duplicate_review_delta() -> None:
    report = build_regional_ryp9_audit(
        checkpoints={
            "source": {
                "decisions": [
                    _decision("closed", "review"),
                    _decision("youth", "duplicate"),
                    _decision("failed", "failed"),
                    _decision("accepted", "accepted"),
                ]
            }
        },
        replays={
            "source": {
                "regional_decisions": [
                    _regional("closed", closed=True),
                    _regional("youth", closed=False),
                    _regional("accepted", closed=False) | {"accepted": True},
                ],
                "duplicate_decisions": [],
            }
        },
    )

    assert report["ready_for_redecision"] is True
    assert report["transition_counts"] == {
        "duplicate->review": 1,
        "review->closed": 1,
    }
    assert report["criteria"]["existing_accepted_preserved"] is True
    assert report["criteria"]["failed_identity_preserved"] is True


def test_ryp9_audit_blocks_closed_without_complete_provenance() -> None:
    regional = _regional("closed", closed=True)
    regional["evidence"]["provenance"] = [{"document_role": "detail_response"}]
    report = build_regional_ryp9_audit(
        checkpoints={"source": {"decisions": [_decision("closed", "review")]}},
        replays={
            "source": {
                "regional_decisions": [regional],
                "duplicate_decisions": [],
            }
        },
    )

    assert report["ready_for_redecision"] is False
    assert report["blockers"] == ["closed_evidence_complete"]
