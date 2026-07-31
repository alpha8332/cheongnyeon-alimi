import io
import logging
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.database import (
    DatabaseConfigurationError,
    _create_db_engine,
    check_db_connection,
    create_db_engine,
    create_session_factory,
    redact_database_url,
)


def test_create_db_engine_defaults_to_safe_logging():
    configured_url = "postgresql://service:secret@database:5432/policies"
    sentinel_engine = MagicMock()

    with patch("app.core.database.create_engine", return_value=sentinel_engine) as mocked:
        result = create_db_engine(configured_url)

    assert result is sentinel_engine
    mocked.assert_called_once_with(
        configured_url,
        pool_pre_ping=True,
        echo=False,
        hide_parameters=True,
    )


def test_create_db_engine_allows_explicit_statement_logging():
    configured_url = "postgresql://service:secret@database:5432/policies"
    sentinel_engine = MagicMock()

    with patch(
        "app.core.database.create_engine",
        return_value=sentinel_engine,
    ) as mocked:
        result = create_db_engine(configured_url, sql_echo=True)

    assert result is sentinel_engine
    mocked.assert_called_once_with(
        configured_url,
        pool_pre_ping=True,
        echo=True,
        hide_parameters=True,
    )


def test_sql_echo_setting_is_disabled_by_default_and_requires_opt_in(
    monkeypatch,
):
    assert Settings.model_fields["SQL_ECHO"].default is False

    monkeypatch.setenv("SQL_ECHO", "true")
    assert Settings(_env_file=None).SQL_ECHO is True


def test_application_engine_uses_explicit_sql_echo_setting():
    sentinel_engine = MagicMock()

    with (
        patch.object(settings, "SQL_ECHO", True),
        patch(
            "app.core.database.create_db_engine",
            return_value=sentinel_engine,
        ) as mocked,
    ):
        result = _create_db_engine()

    assert result is sentinel_engine
    mocked.assert_called_once_with(
        settings.DATABASE_URL,
        sql_echo=True,
    )


def test_create_db_engine_allows_explicit_sqlite_for_tests():
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        assert db_engine.url.get_backend_name() == "sqlite"
    finally:
        db_engine.dispose()


def test_statement_logging_hides_sensitive_unicode_parameters(capsys):
    engine_logger = logging.getLogger("sqlalchemy.engine.Engine")
    original_handlers = list(engine_logger.handlers)
    original_level = engine_logger.level
    original_propagate = engine_logger.propagate
    byte_stream = io.BytesIO()
    cp949_stream = io.TextIOWrapper(
        byte_stream,
        encoding="cp949",
        errors="strict",
    )
    handler = logging.StreamHandler(cp949_stream)
    engine_logger.handlers = [handler]
    engine_logger.setLevel(logging.INFO)
    engine_logger.propagate = False
    db_engine = None
    markers = (
        "R2_POLICY_BODY_🚀",
        "R2_PROVENANCE_MARKER",
        "R2_CREDENTIAL_MARKER",
    )

    try:
        db_engine = create_db_engine(
            "sqlite+pysqlite:///:memory:",
            sql_echo=True,
        )
        with db_engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE logging_probe (payload TEXT NOT NULL)")
            )
            connection.execute(
                text(
                    "INSERT INTO logging_probe (payload) "
                    "VALUES (:payload)"
                ),
                {"payload": "|".join(markers)},
            )
        handler.flush()
        cp949_stream.flush()
        log_output = byte_stream.getvalue().decode("cp949")
        captured = capsys.readouterr()
    finally:
        if db_engine is not None:
            db_engine.dispose()
        engine_logger.handlers = original_handlers
        engine_logger.setLevel(original_level)
        engine_logger.propagate = original_propagate

    assert "SQL parameters hidden due to hide_parameters=True" in log_output
    assert all(marker not in log_output for marker in markers)
    assert "UnicodeEncodeError" not in captured.err


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
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        session_factory = create_session_factory(db_engine)
        assert session_factory.kw["bind"] is db_engine
    finally:
        db_engine.dispose()


def test_check_db_connection_uses_the_injected_engine():
    db_engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        assert check_db_connection(db_engine) is True
    finally:
        db_engine.dispose()


def test_check_db_connection_reports_failure_without_switching_engines():
    unavailable_engine = MagicMock()
    unavailable_engine.connect.side_effect = ConnectionError("database unavailable")

    assert check_db_connection(unavailable_engine) is False
    unavailable_engine.connect.assert_called_once_with()
