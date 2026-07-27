from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

def _create_db_engine():
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            eng = create_engine(db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
        else:
            eng = create_engine(db_url, pool_pre_ping=True, echo=(settings.ENVIRONMENT == "development"))
            # Test connection
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
        return eng
    except Exception:
        # Fallback to local SQLite DB for dev testing when PostgreSQL is not running
        fallback_url = "sqlite:///./cheongnyeon_alimi.db"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})

engine = _create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    """
    PostgreSQL 데이터베이스 실효 연결 검증 함수
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
