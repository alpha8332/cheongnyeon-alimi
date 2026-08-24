from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.models.policy import Policy
from scripts.audit_review_admission import _existing_promoted_policy_count


def _policy(source_id: str, external_id: str) -> Policy:
    return Policy(
        source_id=source_id,
        source_name="Fixture source",
        external_id=external_id,
        title="Fixture policy",
        source_url="https://example.test/policies/1",
        collected_at=datetime.now(timezone.utc),
        data_quality_status="partial",
    )


def test_existing_promoted_policy_count_matches_exact_identities() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Policy.__table__.create(engine)
    try:
        with Session(engine) as session:
            session.add_all(
                [
                    _policy("regional-a", "1"),
                    _policy("regional-a", "2"),
                    _policy("regional-b", "1"),
                ]
            )
            session.commit()

            promoted = [
                {"source_id": "regional-a", "external_id": "1"},
                {"source_id": "regional-b", "external_id": "1"},
                {"source_id": "regional-c", "external_id": "1"},
            ]

            assert _existing_promoted_policy_count(session, promoted) == 2
            assert _existing_promoted_policy_count(session, []) == 0
    finally:
        engine.dispose()
