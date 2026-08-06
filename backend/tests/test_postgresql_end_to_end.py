import copy
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import (
    check_db_connection,
    create_db_engine,
    get_db,
)
from app.main import app
from app.models.policy import Policy
from app.services.seed_importer import import_programs
from collectors.normalized import NormalizedProgram


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = BACKEND_ROOT.parent / "data" / "seeds" / "initial_programs.json"
SYSTEM_FIELDS = frozenset({"id", "created_at", "updated_at"})


def require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "alembic"),
    )
    config.attributes["database_url"] = database_url
    return config


def serialized_policy(policy: Policy) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in Policy.__table__.columns:
        if column.name in SYSTEM_FIELDS:
            continue
        value = getattr(policy, column.name)
        if isinstance(value, datetime):
            value = value.astimezone(timezone.utc).isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        values[column.name] = value
    return values


def current_storage_program(program: dict[str, Any]) -> dict[str, Any]:
    selected = copy.deepcopy(program)
    selected.pop("region_rules")
    return selected


def test_postgresql_seed_repository_api_end_to_end():
    database_url = require_test_database_url()
    config = migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    programs = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    try:
        command.upgrade(config, "head")
        with session_factory() as db:
            first = import_programs(db, programs)
            first_timestamps = {
                (policy.source_id, policy.external_id): policy.updated_at
                for policy in db.scalars(
                    sa.select(Policy).order_by(Policy.id)
                )
            }
            db.commit()
            second = import_programs(db, programs)
            policies = db.scalars(
                sa.select(Policy).order_by(Policy.id)
            ).all()
            second_timestamps = {
                (policy.source_id, policy.external_id): policy.updated_at
                for policy in policies
            }

        assert first.inserted == 4
        assert first.committed is True
        assert second.unchanged == 4
        assert second.inserted == 0
        assert second.updated == 0
        assert len(policies) == 4
        assert first_timestamps == second_timestamps

        stored_by_identity = {
            (policy.source_id, policy.external_id): serialized_policy(
                policy
            )
            for policy in policies
        }
        for program in programs:
            identity = (program["source_id"], program["external_id"])
            assert stored_by_identity[identity] == current_storage_program(
                program
            )
            assert program["region_rules"] == []

        rejected_batch = copy.deepcopy(programs[:2])
        rejected_batch[1].pop("regions")
        with session_factory() as db:
            rejected = import_programs(db, rejected_batch)
            count_after_rejection = db.scalar(
                sa.select(sa.func.count()).select_from(Policy)
            )

        assert rejected.rejected == 1
        assert rejected.inserted == 0
        assert rejected.committed is False
        assert count_after_rejection == 4

        partial_policy = next(
            policy
            for policy in policies
            if policy.data_quality_status == "partial"
        )

        def override_get_db():
            with session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as client:
                valid_list = client.get("/api/v1/policies")
                public_list = client.get(
                    "/api/v1/policies",
                    params={"include_partial": "true"},
                )
                finance = client.get(
                    "/api/v1/policies",
                    params={
                        "include_partial": "true",
                        "category": "finance",
                    },
                )
                hidden_partial = client.get(
                    f"/api/v1/policies/{partial_policy.id}"
                )
                visible_partial = client.get(
                    f"/api/v1/policies/{partial_policy.id}",
                    params={"include_partial": "true"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert valid_list.status_code == 200
        assert valid_list.json()["total"] == 2
        assert public_list.status_code == 200
        assert public_list.json()["total"] == 4
        assert finance.status_code == 200
        assert finance.json()["total"] == 2
        assert hidden_partial.status_code == 404
        assert visible_partial.status_code == 200
        assert "provenance" not in visible_partial.json()

        api_item = next(
            item
            for item in public_list.json()["items"]
            if item["external_id"] == programs[1]["external_id"]
        )
        assert api_item["categories"] == programs[1]["categories"]
        assert api_item["regions"] == programs[1]["regions"]
        assert api_item["application_start"] is None
        assert api_item["application_end"] is None
        assert api_item["application_method"] is None
        assert api_item["education_statuses"] == []
        assert api_item["employment_statuses"] == []
        assert datetime.fromisoformat(
            api_item["collected_at"].replace("Z", "+00:00")
        ) == datetime.fromisoformat(programs[1]["collected_at"])
        assert "provenance" not in api_item
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()


def test_postgresql_connection_failure_does_not_fallback():
    unavailable_engine = create_db_engine(
        "postgresql://postgres@127.0.0.1:1/"
        "cheongnyeon_alimi_test?connect_timeout=1",
    )
    try:
        assert check_db_connection(unavailable_engine) is False
        assert unavailable_engine.url.get_backend_name() == "postgresql"
    finally:
        unavailable_engine.dispose()
