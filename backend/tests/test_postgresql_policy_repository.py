import json
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.repositories.policy import PolicyRepository
from app.services.policy import PolicyListRequest, PolicyService
from app.services.seed_importer import import_programs


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = BACKEND_ROOT.parent / "data" / "seeds" / "initial_programs.json"


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


def test_postgresql_repository_jsonb_filters_and_quality_policy():
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
            imported = import_programs(db, programs)
            assert imported.inserted == 4

            repository = PolicyRepository(db)
            service = PolicyService(repository)
            default_page = service.list(
                PolicyListRequest(page=1, limit=10)
            )
            finance = service.list(
                PolicyListRequest(
                    page=1,
                    limit=10,
                    category="finance",
                    include_partial=True,
                )
            )
            category_prefix = repository.list(
                quality_statuses=("valid", "partial"),
                page=1,
                limit=10,
                category="fin",
            )
            seoul = service.list(
                PolicyListRequest(
                    page=1,
                    limit=10,
                    region="서울특별시",
                )
            )
            region_prefix = service.list(
                PolicyListRequest(
                    page=1,
                    limit=10,
                    region="서울",
                )
            )
            page_one = service.list(
                PolicyListRequest(
                    page=1,
                    limit=1,
                    include_partial=True,
                )
            )
            page_two = service.list(
                PolicyListRequest(
                    page=2,
                    limit=1,
                    include_partial=True,
                )
            )
            partial_policy = next(
                policy
                for policy in finance.items
                if policy.data_quality_status == "partial"
            )
            hidden_partial = service.get(
                partial_policy.id,
                include_partial=False,
            )
            visible_partial = service.get(
                partial_policy.id,
                include_partial=True,
            )

        assert default_page.total == 2
        assert finance.total == 2
        assert category_prefix.total == 0
        assert seoul.total == 1
        assert region_prefix.total == 0
        assert page_one.total == 4
        assert page_two.total == 4
        assert page_one.items[0].id != page_two.items[0].id
        assert hidden_partial is None
        assert visible_partial is not None
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
