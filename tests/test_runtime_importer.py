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
from app.services.runtime_importer import _prune_regional_policies


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


def test_prune_regional_policies_keeps_only_accepted_projection() -> None:
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

        pruned = _prune_regional_policies(
            db,
            source_id="regional-busan-youth-platform",
            accepted_ids={"accepted"},
        )

        assert pruned == 2
        identities = db.execute(
            select(Policy.source_id, Policy.external_id).order_by(Policy.id)
        ).all()
        assert identities == [
            ("regional-busan-youth-platform", "accepted"),
            ("youthcenter-api", "unrelated"),
        ]


def test_prune_regional_policies_removes_source_when_none_are_accepted() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Policy.__table__.create(engine)
    with Session(engine) as db:
        db.add(_policy("regional-jeonbuk-youth-platform", "review"))
        db.commit()

        pruned = _prune_regional_policies(
            db,
            source_id="regional-jeonbuk-youth-platform",
            accepted_ids=set(),
        )

        assert pruned == 1
        assert db.scalar(select(Policy.id)) is None
