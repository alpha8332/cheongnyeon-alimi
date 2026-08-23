import os

import pytest
from sqlalchemy.engine import make_url

from app.core.database import create_db_engine, create_session_factory
from app.services.source_collection_lock import source_collection_lock


def _test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL", "")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def test_postgresql_source_advisory_lock_is_singleton():
    engine = create_db_engine(_test_database_url())
    factory = create_session_factory(engine)
    try:
        with source_collection_lock("queue-lock-test", factory) as first:
            with source_collection_lock("queue-lock-test", factory) as second:
                assert first is True
                assert second is False
        with source_collection_lock("queue-lock-test", factory) as reacquired:
            assert reacquired is True
    finally:
        engine.dispose()
