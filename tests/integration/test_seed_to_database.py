import copy
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
from app.repositories.policy import PolicyRepository  # noqa: E402
from app.services.seed_importer import import_programs  # noqa: E402
from collectors.normalized import (  # noqa: E402
    DataQualityStatus,
    NormalizedProgram,
)
from collectors.validation import NormalizedProgramValidator  # noqa: E402


SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
SYSTEM_FIELDS = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "last_seen_at",
        "last_verified_at",
        "inactive_at",
    }
)
EXPIRED_EXTERNAL_ID = "SYN-YOUTH-001"
ROLLBACK_FUNCTION = "reject_d2_test_policy"
ROLLBACK_EXTERNAL_ID = "D2-ROLLBACK-FAIL"


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
    selected = copy.deepcopy(program)
    selected.pop("region_rules")
    selected["collected_at"] = (
        datetime.fromisoformat(
            selected["collected_at"].replace("Z", "+00:00")
        )
        .astimezone(timezone.utc)
        .isoformat()
    )
    return selected


def _count_external_ids(db, external_ids: list[str]) -> int:
    return int(
        db.scalar(
            sa.select(sa.func.count())
            .select_from(Policy)
            .where(Policy.external_id.in_(external_ids))
        )
        or 0
    )


def test_canonical_seed_to_postgresql_repository_contract():
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    programs = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    validator = NormalizedProgramValidator()

    assert len(programs) == 4
    validation_results = [validator.validate(program) for program in programs]
    assert [result.status for result in validation_results].count(
        DataQualityStatus.VALID
    ) == 2
    assert [result.status for result in validation_results].count(
        DataQualityStatus.PARTIAL
    ) == 2
    assert all(result.program is not None for result in validation_results)

    try:
        command.upgrade(config, "head")

        with session_factory() as db:
            first = import_programs(db, programs)
            policies = db.scalars(
                sa.select(Policy).order_by(Policy.id)
            ).all()
            first_timestamps = {
                (policy.source_id, policy.external_id): policy.updated_at
                for policy in policies
            }
            repository_page = PolicyRepository(db).list(
                quality_statuses=("valid", "partial"),
                page=1,
                limit=10,
            )

        assert first.committed is True
        assert first.inserted == 4
        assert len(policies) == 4
        assert repository_page.total == 3
        assert len(repository_page.items) == 3
        assert EXPIRED_EXTERNAL_ID not in {
            policy.external_id for policy in repository_page.items
        }

        stored_by_identity = {
            (policy.source_id, policy.external_id): _serialized_policy(policy)
            for policy in policies
        }
        for program in programs:
            identity = (program["source_id"], program["external_id"])
            assert stored_by_identity[identity] == _normalized_seed(program)
        for policy in policies:
            source = next(
                program
                for program in programs
                if (program["source_id"], program["external_id"])
                == (policy.source_id, policy.external_id)
            )
            assert policy.last_seen_at == datetime.fromisoformat(
                source["collected_at"].replace("Z", "+00:00")
            )
            assert policy.last_verified_at is not None
            assert policy.inactive_at is None

        with session_factory() as db:
            rerun = import_programs(db, programs)
            rerun_policies = db.scalars(
                sa.select(Policy).order_by(Policy.id)
            ).all()

        assert rerun.committed is True
        assert rerun.inserted == 0
        assert rerun.updated == 0
        assert rerun.unchanged == 4
        assert len(rerun_policies) == 4
        assert first_timestamps == {
            (policy.source_id, policy.external_id): policy.updated_at
            for policy in rerun_policies
        }

        schema_batch = copy.deepcopy(programs[:2])
        schema_batch[0]["external_id"] = "D2-SCHEMA-VALID"
        schema_batch[1]["external_id"] = "D2-SCHEMA-INVALID"
        schema_batch[1].pop("regions")
        with session_factory() as db:
            schema_rejection = import_programs(db, schema_batch)
            schema_count = _count_external_ids(
                db,
                ["D2-SCHEMA-VALID", "D2-SCHEMA-INVALID"],
            )

        assert schema_rejection.committed is False
        assert schema_rejection.rejected == 1
        assert schema_rejection.inserted == 0
        assert schema_count == 0

        invalid_program = copy.deepcopy(programs[0])
        invalid_program["external_id"] = "D2-INVALID-QUALITY"
        invalid_program["data_quality_status"] = "invalid"
        with session_factory() as db:
            invalid_rejection = import_programs(db, [invalid_program])
            invalid_count = _count_external_ids(
                db,
                ["D2-INVALID-QUALITY"],
            )

        assert invalid_rejection.committed is False
        assert invalid_rejection.rejected == 1
        assert invalid_count == 0

        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    f"""
                    CREATE FUNCTION {ROLLBACK_FUNCTION}()
                    RETURNS trigger AS $$
                    BEGIN
                        IF NEW.external_id = '{ROLLBACK_EXTERNAL_ID}' THEN
                            RAISE EXCEPTION 'D2 forced write failure';
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

        rollback_batch = copy.deepcopy(programs[:2])
        rollback_batch[0]["external_id"] = "D2-ROLLBACK-OK"
        rollback_batch[1]["external_id"] = ROLLBACK_EXTERNAL_ID
        with session_factory() as db:
            failed = import_programs(db, rollback_batch)
            rollback_count = _count_external_ids(
                db,
                ["D2-ROLLBACK-OK", ROLLBACK_EXTERNAL_ID],
            )
            final_count = int(
                db.scalar(
                    sa.select(sa.func.count()).select_from(Policy)
                )
                or 0
            )

        assert failed.committed is False
        assert failed.failed == 1
        assert failed.inserted == 0
        assert failed.issues[0].code == "database_write_failed"
        assert rollback_count == 0
        assert final_count == 4
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
