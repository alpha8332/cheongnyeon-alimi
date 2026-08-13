from __future__ import annotations

from collectors.regional_ryp8_audit import build_regional_ryp8_audit


def _closed_decision(external_id: str) -> dict[str, object]:
    return {
        "external_id": external_id,
        "application": "closed",
        "reason_codes": ["application_explicitly_closed"],
        "evidence": {
            "provenance": [
                {"document_role": "list_response"},
                {"document_role": "list_item"},
                {"document_role": "detail_response"},
            ]
        },
    }


def _review_source(source_id: str, *, review: int, legacy: int = 0) -> dict[str, object]:
    return {
        "source_id": source_id,
        "checkpoint_counts": {"review": review},
        "review_evidence_coverage": {
            "application_period": {
                "present": review - legacy,
                "source_value_absent": 0,
                "capture_contract_gap": 0,
                "null_unverifiable": legacy,
            }
        },
    }


def _inputs(*, legacy: int = 0) -> dict[str, object]:
    gyeongnam = "regional-gyeongnam-youth-platform"
    jeju = "regional-jeju-youth-platform"
    gangwon = "regional-gangwon-youth-platform"
    discovered = [f"gangwon-{index}" for index in range(13)]
    return {
        "review_audit": {
            "totals": {
                "accepted": 0,
                "duplicate": 0,
                "review": 1,
                "closed": 2,
                "failed": 1,
            },
            "sources": [
                _review_source(gyeongnam, review=0),
                _review_source(jeju, review=0),
                _review_source(gangwon, review=1, legacy=legacy),
            ],
        },
        "checkpoints": {
            gyeongnam: {
                "discovered_ids": ["gyeongnam-closed"],
                "decisions": [
                    {"external_id": "gyeongnam-closed", "outcome": "closed"}
                ],
            },
            jeju: {
                "discovered_ids": ["jeju-closed"],
                "decisions": [
                    {"external_id": "jeju-closed", "outcome": "closed"}
                ],
            },
            gangwon: {
                "discovered_ids": discovered,
                "decisions": [
                    {"external_id": "gangwon-12", "outcome": "failed"}
                ],
            },
        },
        "closed_replays": {
            gyeongnam: [_closed_decision("gyeongnam-closed")],
            jeju: [_closed_decision("jeju-closed")],
        },
        "expected_outcomes": {
            "accepted": 0,
            "duplicate": 0,
            "review": 1,
            "closed": 2,
            "failed": 1,
        },
    }


def test_audit_reconciles_closed_history_and_classifies_failed_identity() -> None:
    report = build_regional_ryp8_audit(
        **_inputs(),
        max_legacy_null_slots=0,
    )

    assert report["data_ready"] is True
    assert report["blockers"] == []
    assert report["failure_classification"]["categories"] == {
        "detail_click_or_post_contract": 1
    }
    assert report["failure_classification"]["unclassified_count"] == 0
    assert all(item["complete"] for item in report["closed_history"])


def test_audit_does_not_invent_an_undefined_legacy_null_target() -> None:
    report = build_regional_ryp8_audit(
        **_inputs(),
        max_legacy_null_slots=None,
    )

    assert report["criteria"]["legacy_null_within_target"] is None
    assert report["data_ready"] is False
    assert report["blockers"] == ["legacy_null_within_target"]


def test_audit_blocks_when_legacy_null_exceeds_target() -> None:
    report = build_regional_ryp8_audit(
        **_inputs(legacy=1),
        max_legacy_null_slots=0,
    )

    assert report["legacy_null_slots"] == 1
    assert report["criteria"]["legacy_null_within_target"] is False
    assert report["data_ready"] is False


def test_audit_blocks_when_an_approved_checkpoint_has_no_field_audit() -> None:
    inputs = _inputs()
    inputs["checkpoints"]["regional-unreconciled-youth-platform"] = {
        "discovered_ids": [],
        "decisions": [],
    }

    report = build_regional_ryp8_audit(
        **inputs,
        max_legacy_null_slots=0,
    )

    assert report["criteria"]["approved_sources_complete"] is False
    assert report["data_ready"] is False
