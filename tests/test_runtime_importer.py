from datetime import datetime, timezone
from pathlib import Path
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.models.policy import Policy
from app.services.runtime_importer import (
    _inactivate_missing_policies,
    _matches_redecision_audit,
)
from collectors.regional_expansion import RegionalOutcome


def _policy(source_id: str, external_id: str | None) -> Policy:
    return Policy(
        schema_version="1.2.0",
        source_id=source_id,
        source_name="Regional test",
        external_id=external_id,
        title=f"Policy {external_id}",
        categories=[],
        keywords=[],
        life_stages=[],
        target_groups=[],
        regions=[],
        education_statuses=[],
        employment_statuses=[],
        required_conditions=[],
        preferred_conditions=[],
        excluded_conditions=[],
        source_url="https://example.test/policy",
        collected_at=datetime.now(timezone.utc),
        provenance=[],
        data_quality_status="partial",
    )


def test_complete_source_soft_deactivates_only_missing_projection() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Policy.__table__.create(engine)
    with Session(engine) as db:
        db.add_all(
            [
                _policy("regional-busan-youth-platform", "accepted"),
                _policy("regional-busan-youth-platform", "review"),
                _policy("regional-busan-youth-platform", None),
                _policy("youthcenter-api", "unrelated"),
            ]
        )
        db.commit()

        inactivated = _inactivate_missing_policies(
            db,
            source_id="regional-busan-youth-platform",
            seen_external_ids={"accepted"},
        )

        assert inactivated == 2
        identities = db.execute(
            select(
                Policy.source_id,
                Policy.external_id,
                Policy.inactive_at,
            ).order_by(Policy.id)
        ).all()
        assert len(identities) == 4
        assert identities[0].inactive_at is None
        assert identities[1].inactive_at is not None
        assert identities[2].inactive_at is not None
        assert identities[3].inactive_at is None


def test_complete_empty_source_preserves_history_as_inactive() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Policy.__table__.create(engine)
    with Session(engine) as db:
        db.add(_policy("regional-jeonbuk-youth-platform", "review"))
        db.commit()

        inactivated = _inactivate_missing_policies(
            db,
            source_id="regional-jeonbuk-youth-platform",
            seen_external_ids=set(),
        )

        assert inactivated == 1
        policy = db.scalar(select(Policy))
        assert policy is not None
        assert policy.inactive_at is not None


def test_redecision_audit_must_match_the_exact_source_delta() -> None:
    existing = {"one": RegionalOutcome.REVIEW, "failed": RegionalOutcome.FAILED}
    outcomes = {"one": RegionalOutcome.CLOSED, "failed": RegionalOutcome.FAILED}
    audit = {
        "ready_for_redecision": True,
        "sources": [
            {
                "source_id": "regional-busan-youth-platform",
                "transitions": [
                    {"external_id": "one", "from": "review", "to": "closed"}
                ],
                "transition_scope_valid": True,
                "closed_evidence_complete": True,
                "existing_accepted_preserved": True,
                "failed_identity_preserved": True,
                "promotion_evidence_complete": True,
            }
        ],
    }

    assert _matches_redecision_audit(
        "regional-busan-youth-platform", existing, outcomes, audit
    )
    audit["sources"][0]["transitions"][0]["external_id"] = "other"
    assert not _matches_redecision_audit(
        "regional-busan-youth-platform", existing, outcomes, audit
    )
