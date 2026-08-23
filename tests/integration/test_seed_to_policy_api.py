import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.api.v1.endpoints.policies import get_policy_service  # noqa: E402
from app.core.database import create_db_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.services.seed_importer import import_programs  # noqa: E402
from collectors.normalized import NormalizedProgram  # noqa: E402


SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
SYSTEM_FIELDS = frozenset({"id", "created_at", "updated_at"})
EXPIRED_EXTERNAL_ID = "SYN-YOUTH-001"


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


def _parse_datetime(value: str) -> datetime:
    selected = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert selected.tzinfo is not None
    assert selected.utcoffset() is not None
    return selected


def _normalize_evidence_datetimes(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                _parse_datetime(item)
                if key == "collected_at"
                else _normalize_evidence_datetimes(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_evidence_datetimes(item) for item in value]
    return value


def _assert_public_program(
    response_item: dict[str, Any],
    seed_program: dict[str, Any],
    *,
    include_eligibility: bool = False,
) -> None:
    expected_fields = (
        set(seed_program)
        - {"provenance"}
        - NormalizedProgram.SEARCH_FIELD_NAMES
    )
    if not include_eligibility:
        expected_fields.remove("eligibility_summary")
    assert set(response_item) == expected_fields | SYSTEM_FIELDS
    assert "provenance" not in response_item

    for field in expected_fields:
        if field == "collected_at":
            assert _parse_datetime(response_item[field]) == _parse_datetime(
                seed_program[field]
            )
        elif field == "eligibility_summary":
            assert _normalize_evidence_datetimes(
                response_item[field]
            ) == _normalize_evidence_datetimes(seed_program[field])
        else:
            assert response_item[field] == seed_program[field]

    assert isinstance(response_item["id"], int)
    _parse_datetime(response_item["created_at"])
    _parse_datetime(response_item["updated_at"])


def test_canonical_seed_postgresql_policy_api_contract():
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
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
            imported = import_programs(db, programs)
            policy_ids = {
                policy.external_id: policy.id
                for policy in db.scalars(
                    sa.select(Policy).order_by(Policy.id)
                )
            }

        assert imported.committed is True
        assert imported.inserted == 4

        def override_get_db():
            with session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(
                app,
                raise_server_exceptions=False,
            ) as client:
                valid_list = client.get("/api/v1/policies")
                public_list = client.get(
                    "/api/v1/policies",
                    params={"include_partial": "true"},
                )
                first_page = client.get(
                    "/api/v1/policies",
                    params={
                        "include_partial": "true",
                        "page": 1,
                        "limit": 1,
                    },
                )
                second_page = client.get(
                    "/api/v1/policies",
                    params={
                        "include_partial": "true",
                        "page": 2,
                        "limit": 1,
                    },
                )
                empty_page = client.get(
                    "/api/v1/policies",
                    params={
                        "include_partial": "true",
                        "page": 99,
                        "limit": 10,
                    },
                )
                finance = client.get(
                    "/api/v1/policies",
                    params={
                        "include_partial": "true",
                        "category": "finance",
                    },
                )
                nationwide = client.get(
                    "/api/v1/policies",
                    params={"region": "전국"},
                )
                region_prefix = client.get(
                    "/api/v1/policies",
                    params={"region": "서울"},
                )
                open_status = client.get(
                    "/api/v1/policies",
                    params={"status": "open"},
                )

                expired_program = programs[0]
                valid_program = programs[1]
                partial_program = programs[2]
                expired_detail = client.get(
                    f"/api/v1/policies/"
                    f"{policy_ids[expired_program['external_id']]}"
                )
                valid_detail = client.get(
                    f"/api/v1/policies/"
                    f"{policy_ids[valid_program['external_id']]}"
                )
                hidden_partial = client.get(
                    f"/api/v1/policies/"
                    f"{policy_ids[partial_program['external_id']]}"
                )
                visible_partial = client.get(
                    f"/api/v1/policies/"
                    f"{policy_ids[partial_program['external_id']]}",
                    params={"include_partial": "true"},
                )
                missing = client.get("/api/v1/policies/999999")

                invalid_queries = (
                    client.get(
                        "/api/v1/policies",
                        params={"page": 0},
                    ),
                    client.get(
                        "/api/v1/policies",
                        params={"limit": 101},
                    ),
                    client.get(
                        "/api/v1/policies",
                        params={"category": "fin"},
                    ),
                    client.get(
                        "/api/v1/policies",
                        params={"status": "unknown"},
                    ),
                    client.get(
                        "/api/v1/policies",
                        params={"region": ""},
                    ),
                    client.get(
                        "/api/v1/policies",
                        params={"include_partial": "sometimes"},
                    ),
                    client.get("/api/v1/policies/not-an-integer"),
                )

                def fail_policy_service():
                    raise RuntimeError("D3 internal detail must not leak")

                app.dependency_overrides[
                    get_policy_service
                ] = fail_policy_service
                try:
                    server_error = client.get("/api/v1/policies")
                finally:
                    app.dependency_overrides.pop(
                        get_policy_service,
                        None,
                    )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert valid_list.status_code == 200
        assert valid_list.json()["total"] == 1
        assert {
            item["data_quality_status"]
            for item in valid_list.json()["items"]
        } == {"valid"}

        assert public_list.status_code == 200
        assert public_list.json()["total"] == 3
        public_by_external_id = {
            item["external_id"]: item
            for item in public_list.json()["items"]
        }
        for program in programs:
            if program["external_id"] == EXPIRED_EXTERNAL_ID:
                continue
            _assert_public_program(
                public_by_external_id[program["external_id"]],
                program,
            )
        assert EXPIRED_EXTERNAL_ID not in public_by_external_id

        assert first_page.status_code == 200
        assert first_page.json()["total"] == 3
        assert first_page.json()["page"] == 1
        assert first_page.json()["limit"] == 1
        assert len(first_page.json()["items"]) == 1
        assert second_page.status_code == 200
        assert second_page.json()["total"] == 3
        assert len(second_page.json()["items"]) == 1
        assert (
            first_page.json()["items"][0]["id"]
            != second_page.json()["items"][0]["id"]
        )
        assert empty_page.status_code == 200
        assert empty_page.json()["total"] == 3
        assert empty_page.json()["items"] == []

        assert finance.status_code == 200
        assert finance.json()["total"] == 2
        assert {
            item["external_id"] for item in finance.json()["items"]
        } == {"SYN-YOUTH-002", "SYN-BOK-001"}
        assert nationwide.status_code == 200
        assert nationwide.json()["total"] == 1
        assert nationwide.json()["items"][0]["external_id"] == (
            "SYN-YOUTH-002"
        )
        assert region_prefix.status_code == 200
        assert region_prefix.json()["total"] == 0
        assert region_prefix.json()["items"] == []
        assert open_status.status_code == 200
        assert open_status.json()["total"] == 1
        assert open_status.json()["items"][0]["external_id"] == (
            "SYN-YOUTH-002"
        )

        assert expired_detail.status_code == 404
        assert expired_detail.json() == {"detail": "Policy not found"}
        assert valid_detail.status_code == 200
        _assert_public_program(
            valid_detail.json(),
            valid_program,
            include_eligibility=True,
        )
        assert hidden_partial.status_code == 404
        assert hidden_partial.json() == {"detail": "Policy not found"}
        assert visible_partial.status_code == 200
        _assert_public_program(
            visible_partial.json(),
            partial_program,
            include_eligibility=True,
        )
        assert missing.status_code == 404
        assert missing.json() == {"detail": "Policy not found"}

        assert all(response.status_code == 422 for response in invalid_queries)
        assert all(
            isinstance(response.json().get("detail"), list)
            for response in invalid_queries
        )
        assert server_error.status_code == 500
        assert server_error.json() == {
            "error": {
                "message": "Internal Server Error",
                "details": {},
            }
        }
        assert "D3 internal detail" not in server_error.text
    finally:
        try:
            app.dependency_overrides.pop(get_policy_service, None)
            app.dependency_overrides.pop(get_db, None)
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
