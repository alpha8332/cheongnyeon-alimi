from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


class DatabaseConfigurationError(RuntimeError):
    """Raised when SQLAlchemy cannot construct the configured database engine."""


def redact_database_url(database_url: str) -> str:
    """Return a log-safe URL without exposing credentials."""
    try:
        return make_url(database_url).render_as_string(hide_password=True)
    except Exception:
        return "<invalid-database-url>"


def create_db_engine(
    database_url: str,
    *,
    sql_echo: bool = False,
) -> Engine:
    """Construct an engine for the explicitly supplied URL without probing it."""
    engine_options = {
        "pool_pre_ping": True,
        "echo": sql_echo,
        "hide_parameters": True,
    }

    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}

    try:
        return create_engine(database_url, **engine_options)
    except Exception as exc:
        safe_url = redact_database_url(database_url)
        raise DatabaseConfigurationError(
            f"Could not configure database engine for {safe_url} "
            f"({type(exc).__name__})"
        ) from None


def create_session_factory(db_engine: Engine):
    """Create a session factory bound to an explicitly selected engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


def _create_db_engine() -> Engine:
    return create_db_engine(
        settings.DATABASE_URL,
        sql_echo=settings.SQL_ECHO,
    )


engine = _create_db_engine()
SessionLocal = create_session_factory(engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(db_engine: Engine | None = None) -> bool:
    """Probe the selected engine and report its current connection state."""
    selected_engine = db_engine if db_engine is not None else engine
    try:
        with selected_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
