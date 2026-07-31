import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import create_db_engine  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.runtime_importer import import_runtime_raw  # noqa: E402


RAW_ROOT = ROOT / "data" / "fixtures" / "raw"
SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
SYSTEM_FIELDS = frozenset({"id", "created_at", "updated_at"})
ROLLBACK_FUNCTION = "reject_d4_runtime_policy"
ROLLBACK_EXTERNAL_ID = "SYN-YOUTH-002"


def _require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def _migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    return config


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _serialized_policy(policy: Policy) -> dict[str, Any]:
    return {
        column.name: _json_value(getattr(policy, column.name))
        for column in Policy.__table__.columns
        if column.name not in SYSTEM_FIELDS
    }


def _normalized_seed(program: dict[str, Any]) -> dict[str, Any]:
    selected = dict(program)
    selected["collected_at"] = (
        datetime.fromisoformat(
            selected["collected_at"].replace("Z", "+00:00")
        )
        .astimezone(timezone.utc)
        .isoformat()
    )
    return selected


def _policy_count(db) -> int:
    return int(
        db.scalar(sa.select(sa.func.count()).select_from(Policy)) or 0
    )


def test_runtime_raw_replay_to_postgresql_is_atomic_and_idempotent():
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    try:
        command.upgrade(config, "head")

        with session_factory() as db:
            dry_run = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="youthcenter-api",
                limit=100,
                dry_run=True,
            )
            dry_run_count = _policy_count(db)

        assert dry_run.replay.raw_document_count == 4
        assert dry_run.replay.extracted_count == 3
        assert dry_run.replay.valid_count == 2
        assert dry_run.replay.invalid_count == 1
        assert dry_run.replay.accepted_count == 2
        assert dry_run.database.inserted == 2
        assert dry_run.database.dry_run is True
        assert dry_run.database.committed is False
        assert dry_run_count == 0

        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    f"""
                    CREATE FUNCTION {ROLLBACK_FUNCTION}()
                    RETURNS trigger AS $$
                    BEGIN
                        IF NEW.external_id = '{ROLLBACK_EXTERNAL_ID}' THEN
                            RAISE EXCEPTION 'D4 forced write failure';
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                    """
                )
            )
            connection.execute(
                sa.text(
                    f"""
                    CREATE TRIGGER {ROLLBACK_FUNCTION}_trigger
                    BEFORE INSERT OR UPDATE ON policies
                    FOR EACH ROW EXECUTE FUNCTION {ROLLBACK_FUNCTION}()
                    """
                )
            )

        with session_factory() as db:
            failed = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="youthcenter-api",
                limit=100,
            )
            failed_count = _policy_count(db)

        assert failed.replay.invalid_count == 1
        assert failed.replay.accepted_count == 2
        assert failed.database.failed == 1
        assert failed.database.inserted == 0
        assert failed.database.committed is False
        assert failed.database.issues[0].code == "database_write_failed"
        assert failed_count == 0

        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    f"DROP FUNCTION IF EXISTS "
                    f"{ROLLBACK_FUNCTION}() CASCADE"
                )
            )

        with session_factory() as db:
            youth = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="youthcenter-api",
                limit=100,
            )
        with session_factory() as db:
            bokjiro = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="bokjiro-central-welfare-api",
                limit=100,
            )
            first_count = _policy_count(db)

        assert youth.database.inserted == 2
        assert youth.replay.invalid_count == 1
        assert bokjiro.database.inserted == 2
        assert bokjiro.replay.partial_count == 2
        assert first_count == (
            youth.replay.accepted_count
            + bokjiro.replay.accepted_count
        ) == 4

        with session_factory() as db:
            youth_rerun = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="youthcenter-api",
                limit=100,
            )
        with session_factory() as db:
            bokjiro_rerun = import_runtime_raw(
                db,
                raw_root=RAW_ROOT,
                source_id="bokjiro-central-welfare-api",
                limit=100,
            )
            policies = db.scalars(
                sa.select(Policy).order_by(Policy.id)
            ).all()

        assert youth_rerun.database.inserted == 0
        assert youth_rerun.database.updated == 0
        assert youth_rerun.database.unchanged == 2
        assert youth_rerun.replay.invalid_count == 1
        assert bokjiro_rerun.database.inserted == 0
        assert bokjiro_rerun.database.updated == 0
        assert bokjiro_rerun.database.unchanged == 2
        assert len(policies) == 4
        assert all(
            policy.external_id != "SYN-YOUTH-REJECTED"
            for policy in policies
        )

        stored_by_identity = {
            (policy.source_id, policy.external_id): _serialized_policy(policy)
            for policy in policies
        }
        for program in seed:
            identity = (program["source_id"], program["external_id"])
            assert stored_by_identity[identity] == _normalized_seed(program)
    finally:
        try:
            with db_engine.begin() as connection:
                connection.execute(
                    sa.text(
                        f"DROP FUNCTION IF EXISTS "
                        f"{ROLLBACK_FUNCTION}() CASCADE"
                    )
                )
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
