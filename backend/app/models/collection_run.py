from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    text,
)

from app.core.database import Base


COLLECTION_RUN_TYPE_VALUES = (
    "seed_import",
    "runtime_import",
    "collection",
)
COLLECTION_RUN_TRIGGER_TYPE_VALUES = (
    "cli",
    "scheduler",
    "admin",
)
COLLECTION_RUN_STATUS_VALUES = (
    "running",
    "succeeded",
    "partial_failure",
    "failed",
)

COUNT_FIELDS = (
    "requested_count",
    "raw_document_count",
    "extracted_count",
    "accepted_count",
    "partial_count",
    "invalid_count",
    "duplicate_count",
    "rejected_count",
    "inserted_count",
    "updated_count",
    "unchanged_count",
    "skipped_count",
    "failed_count",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollectionRun(Base):
    """Safe execution summary for a Seed, Runtime, or collection run."""

    __tablename__ = "collection_runs"

    run_id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    source_id = Column(Text, nullable=True)
    run_type = Column(
        Enum(
            *COLLECTION_RUN_TYPE_VALUES,
            name="collection_run_type",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    trigger_type = Column(
        Enum(
            *COLLECTION_RUN_TRIGGER_TYPE_VALUES,
            name="collection_run_trigger_type",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(
            *COLLECTION_RUN_STATUS_VALUES,
            name="collection_run_status",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default="running",
        server_default="running",
    )

    requested_count = Column(Integer, nullable=False, default=0, server_default="0")
    raw_document_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    extracted_count = Column(Integer, nullable=False, default=0, server_default="0")
    accepted_count = Column(Integer, nullable=False, default=0, server_default="0")
    partial_count = Column(Integer, nullable=False, default=0, server_default="0")
    invalid_count = Column(Integer, nullable=False, default=0, server_default="0")
    duplicate_count = Column(Integer, nullable=False, default=0, server_default="0")
    rejected_count = Column(Integer, nullable=False, default=0, server_default="0")
    inserted_count = Column(Integer, nullable=False, default=0, server_default="0")
    updated_count = Column(Integer, nullable=False, default=0, server_default="0")
    unchanged_count = Column(Integer, nullable=False, default=0, server_default="0")
    skipped_count = Column(Integer, nullable=False, default=0, server_default="0")
    failed_count = Column(Integer, nullable=False, default=0, server_default="0")

    error_type = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "source_id IS NULL OR length(trim(source_id)) > 0",
            name="ck_collection_runs_source_id_nonempty",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_collection_runs_timestamp_order",
        ),
        CheckConstraint(
            "(status = 'running' AND finished_at IS NULL) OR "
            "(status <> 'running' AND finished_at IS NOT NULL)",
            name="ck_collection_runs_terminal_finished_at",
        ),
        CheckConstraint(
            " AND ".join(f"{field} >= 0" for field in COUNT_FIELDS),
            name="ck_collection_runs_counts_nonnegative",
        ),
        Index("ix_collection_runs_source_id", "source_id"),
        Index("ix_collection_runs_started_at", "started_at"),
        Index("ix_collection_runs_status", "status"),
    )
