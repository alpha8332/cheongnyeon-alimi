from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
import sys

for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.models.collection_run import CollectionRun  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.models.policy_search import PolicyRegionRule  # noqa: E402
from scripts.apply_review_admission import main  # noqa: E402


def test_review_admission_manifest_rolls_back_on_scratch_postgresql() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    manifest = os.getenv("REVIEW_ADMISSION_MANIFEST")
    if not database_url or not manifest:
        pytest.skip(
            "TEST_DATABASE_URL and REVIEW_ADMISSION_MANIFEST are required"
        )
    parsed = make_url(database_url)
    if parsed.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not (parsed.database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end in _test")

    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            before = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
        exit_code = main(
            [
                "--manifest",
                manifest,
                "--database-url",
                database_url,
                "--dry-run",
            ]
        )
        with Session(engine) as session:
            after = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
    finally:
        engine.dispose()
    assert exit_code == 0
    assert after == before


def test_review_admission_manifest_is_idempotent_on_scratch_postgresql(
    capsys,
) -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    manifest_path = os.getenv("REVIEW_ADMISSION_MANIFEST")
    if (
        not database_url
        or not manifest_path
        or os.getenv("REVIEW_ADMISSION_IDEMPOTENCY_TEST") != "1"
    ):
        pytest.skip("explicit scratch idempotency test opt-in is required")
    parsed = make_url(database_url)
    if parsed.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not (parsed.database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end in _test")

    expected_manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )
    engine = create_engine(database_url)
    identities = {
        (value["source_id"], value["external_id"])
        for value in expected_manifest["decisions"]
        if value["outcome"] == "promote_partial"
    }
    original_run_ids = set()
    created_run_ids = set()
    before = -1
    try:
        with Session(engine) as session:
            before = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
            original_run_ids = set(session.scalars(select(CollectionRun.run_id)))
        first_exit = main(
            [
                "--manifest",
                manifest_path,
                "--database-url",
                database_url,
                "--test-apply",
            ]
        )
        first_output = capsys.readouterr().out
        second_exit = main(
            [
                "--manifest",
                manifest_path,
                "--database-url",
                database_url,
                "--test-apply",
            ]
        )
        second_output = capsys.readouterr().out
        assert first_exit == 0
        assert (
            f"inserted={len(identities)} updated=0 unchanged=0"
            in first_output
        )
        assert second_exit == 0
        assert (
            f"inserted=0 updated=0 unchanged={len(identities)}"
            in second_output
        )
        with Session(engine) as verification:
            admitted = verification.scalars(
                select(Policy).where(
                    Policy.source_id.in_({source for source, _ in identities}),
                    Policy.external_id.in_(
                        {external_id for _, external_id in identities}
                    ),
                )
            ).all()
            assert {
                (policy.source_id, policy.external_id) for policy in admitted
            } == identities
            assert all(policy.coverage_scope == "regional" for policy in admitted)
            assert all(policy.regions for policy in admitted)
            region_rule_count = int(
                verification.scalar(
                    select(func.count())
                    .select_from(PolicyRegionRule)
                    .where(
                        PolicyRegionRule.policy_id.in_(
                            {policy.id for policy in admitted}
                        )
                    )
                )
                or 0
            )
            assert region_rule_count >= len(admitted)
            created_runs = verification.scalars(
                select(CollectionRun).where(
                    CollectionRun.run_id.not_in(original_run_ids)
                )
            ).all()
            created_run_ids = {run.run_id for run in created_runs}
            assert len(created_runs) == 6
            assert all(run.status == "succeeded" for run in created_runs)
            assert sum(run.inserted_count for run in created_runs) == len(
                identities
            )
            assert sum(run.unchanged_count for run in created_runs) == len(
                identities
            )
            assert {
                run.source_id for run in created_runs
            } == {
                "regional-daegu-youth-platform",
                "regional-gangwon-youth-platform",
                "regional-gyeongnam-youth-platform",
            }
    finally:
        with Session(engine) as cleanup:
            if identities:
                for source_id, external_id in sorted(identities):
                    cleanup.execute(
                        delete(Policy).where(
                            Policy.source_id == source_id,
                            Policy.external_id == external_id,
                        )
                    )
            if created_run_ids:
                cleanup.execute(
                    delete(CollectionRun).where(
                        CollectionRun.run_id.in_(created_run_ids)
                    )
                )
            cleanup.commit()
        if before >= 0:
            with Session(engine) as verification:
                after = int(
                    verification.scalar(
                        select(func.count()).select_from(Policy)
                    )
                    or 0
                )
                assert after == before
        engine.dispose()
