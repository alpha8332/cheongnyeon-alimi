from unittest.mock import MagicMock, patch

import pytest

from app.core.database import (
    DatabaseConfigurationError,
    check_db_connection,
    create_db_engine,
    create_session_factory,
    redact_database_url,
)


def test_create_db_engine_uses_only_the_explicit_database_url():
    configured_url = "postgresql://service:secret@database:5432/policies"
    sentinel_engine = MagicMock()

    with patch("app.core.database.create_engine", return_value=sentinel_engine) as mocked:
        result = create_db_engine(configured_url, environment="development")

    assert result is sentinel_engine
    mocked.assert_called_once_with(
        configured_url,
        pool_pre_ping=True,
        echo=True,
    )


def test_create_db_engine_allows_explicit_sqlite_for_tests():
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:", environment="test")
    try:
        assert db_engine.url.get_backend_name() == "sqlite"
    finally:
        db_engine.dispose()


def test_configuration_error_masks_database_password():
    configured_url = "postgresql://service:super-secret@database:5432/policies"

    with patch(
        "app.core.database.create_engine",
        side_effect=ValueError(f"failed for {configured_url}"),
    ):
        with pytest.raises(DatabaseConfigurationError) as captured:
            create_db_engine(configured_url)

    message = str(captured.value)
    assert "super-secret" not in message
    assert configured_url not in message
    assert "service:***@database:5432/policies" in message


def test_redact_database_url_handles_an_invalid_url():
    assert redact_database_url("not a database url") == "<invalid-database-url>"


def test_session_factory_binds_the_injected_engine():
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:", environment="test")
    try:
        session_factory = create_session_factory(db_engine)
        assert session_factory.kw["bind"] is db_engine
    finally:
        db_engine.dispose()


def test_check_db_connection_uses_the_injected_engine():
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:", environment="test")
    try:
        assert check_db_connection(db_engine) is True
    finally:
        db_engine.dispose()


def test_check_db_connection_reports_failure_without_switching_engines():
    unavailable_engine = MagicMock()
    unavailable_engine.connect.side_effect = ConnectionError("database unavailable")

    assert check_db_connection(unavailable_engine) is False
    unavailable_engine.connect.assert_called_once_with()
