from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from datetime import date

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
import sys

for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.models.policy import Policy  # noqa: E402
from app.services.seed_importer import import_programs  # noqa: E402
from scripts.apply_review_admission import main  # noqa: E402
from scripts.audit_review_admission import build_manifest  # noqa: E402


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


def test_review_admission_manifest_is_idempotent_on_scratch_postgresql() -> None:
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

    expected_manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    engine = create_engine(database_url)
    identities: set[tuple[str, str]] = set()
    before = -1
    try:
        with Session(engine) as session:
            before = int(
                session.scalar(select(func.count()).select_from(Policy)) or 0
            )
            rebuilt, programs = build_manifest(
                session,
                as_of=date.fromisoformat(expected_manifest["as_of"]),
                raw_root=ROOT / "runtime/raw",
                checkpoint_root=ROOT / "runtime/decisions/regional-checkpoints",
                decision_root=ROOT / "runtime/decisions",
            )
            assert rebuilt == expected_manifest
            identities = set(programs)
            first = import_programs(
                session,
                [programs[identity] for identity in sorted(identities)],
            )
            second = import_programs(
                session,
                [programs[identity] for identity in sorted(identities)],
            )
            assert first.inserted == len(identities)
            assert first.updated == 0
            assert second.inserted == 0
            assert second.updated == 0
            assert second.unchanged == len(identities)
    finally:
        if identities:
            with Session(engine) as cleanup:
                for source_id, external_id in sorted(identities):
                    cleanup.execute(
                        delete(Policy).where(
                            Policy.source_id == source_id,
                            Policy.external_id == external_id,
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
