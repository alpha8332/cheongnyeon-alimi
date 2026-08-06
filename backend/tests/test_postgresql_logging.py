import copy
import io
import json
import logging
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.services.seed_importer import import_programs


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = (
    BACKEND_ROOT.parent / "data" / "seeds" / "initial_programs.json"
)


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


def test_postgresql_statement_logging_hides_sensitive_unicode_parameters(
    capsys,
):
    database_url = require_test_database_url()
    config = migration_config(database_url)
    command.upgrade(config, "head")

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
        "R2_POLICY_BODY_MARKER",
        "R2_PROVENANCE_MARKER",
        "R2_CREDENTIAL_MARKER",
        "🚀",
    )

    try:
        db_engine = create_db_engine(database_url, sql_echo=True)
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=db_engine,
        )
        program = copy.deepcopy(
            json.loads(SEED_PATH.read_text(encoding="utf-8"))[0]
        )
        program["external_id"] = "PG-R2-LOGGING"
        program["title"] = "R2_POLICY_BODY_MARKER 🚀"
        program["source_url"] = (
            "https://fixture.invalid/policy"
            "?api_key=R2_CREDENTIAL_MARKER"
        )
        program["provenance"][0]["source_url"] = (
            "https://fixture.invalid/raw/R2_PROVENANCE_MARKER"
        )

        with session_factory() as db:
            result = import_programs(db, [program])

        handler.flush()
        cp949_stream.flush()
        log_output = byte_stream.getvalue().decode("cp949")
        captured = capsys.readouterr()

        assert result.inserted == 1
        assert "SQL parameters hidden due to hide_parameters=True" in (
            log_output
        )
        assert all(marker not in log_output for marker in markers)
        assert "UnicodeEncodeError" not in captured.err
    finally:
        if db_engine is not None:
            db_engine.dispose()
        engine_logger.handlers = original_handlers
        engine_logger.setLevel(original_level)
        engine_logger.propagate = original_propagate
        try:
            command.downgrade(config, "base")
            if db_engine is not None:
                assert not inspect(db_engine).has_table("policies")
        finally:
            if db_engine is not None:
                db_engine.dispose()
