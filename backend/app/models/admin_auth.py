from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, SmallInteger, String, text

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdminAuthState(Base):
    """Singleton state for the local administrator credential and sessions."""

    __tablename__ = "admin_auth_state"

    id = Column(SmallInteger, primary_key=True, default=1)
    pin_hash = Column(String(255), nullable=False)
    session_generation = Column(Integer, nullable=False, default=1, server_default="1")
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_admin_auth_state_singleton"),
        CheckConstraint(
            "length(pin_hash) BETWEEN 64 AND 255",
            name="ck_admin_auth_state_pin_hash_length",
        ),
        CheckConstraint(
            "session_generation > 0",
            name="ck_admin_auth_state_session_generation_positive",
        ),
    )
