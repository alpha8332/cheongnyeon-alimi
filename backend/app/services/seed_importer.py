import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, literal_column, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.policy import Policy


EXTERNAL_ID_REQUIRED_SOURCES = frozenset(
    {
        "youthcenter-api",
        "bokjiro-central-welfare-api",
    }
)

IDENTITY_FIELDS = frozenset({"source_id", "external_id"})
IMMUTABLE_FIELDS = frozenset({"id", "created_at"})
POLICY_WRITE_FIELDS = tuple(
    column.name
    for column in Policy.__table__.columns
    if column.name not in IMMUTABLE_FIELDS
)
MUTABLE_FIELDS = tuple(
    field
    for field in POLICY_WRITE_FIELDS
    if field not in IDENTITY_FIELDS | {"updated_at"}
)


@dataclass(frozen=True)
class ImportIssue:
    index: int
    source_id: str | None
    external_id: str | None
    code: str
    error_type: str | None = None


@dataclass(frozen=True)
class ImportResult:
    total: int
    inserted: int
    updated: int
    unchanged: int
    skipped: int
    failed: int
    issues: tuple[ImportIssue, ...] = ()


def parse_date(date_str: Any) -> date | None:
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_datetime(dt_str: Any) -> datetime:
    if not dt_str or not isinstance(dt_str, str):
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value.strip() else None


def _identity_issue(
    item: Mapping[str, Any],
    index: int,
) -> ImportIssue | None:
    source_id = _nonempty_string(item.get("source_id"))
    external_id = _nonempty_string(item.get("external_id"))

    if source_id is None:
        return ImportIssue(
            index=index,
            source_id=None,
            external_id=external_id,
            code="missing_source_id",
        )
    if external_id is None and source_id in EXTERNAL_ID_REQUIRED_SOURCES:
        return ImportIssue(
            index=index,
            source_id=source_id,
            external_id=None,
            code="missing_external_id",
        )
    if external_id is None:
        return ImportIssue(
            index=index,
            source_id=source_id,
            external_id=None,
            code="unsupported_null_external_id",
        )
    return None


def _policy_values(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": item.get("schema_version", "1.0.0"),
        "source_id": _nonempty_string(item.get("source_id")),
        "source_name": item.get("source_name", ""),
        "external_id": _nonempty_string(item.get("external_id")),
        "title": item.get("title", ""),
        "organization": item.get("organization"),
        "summary": item.get("summary"),
        "category_text": item.get("category_text"),
        "categories": item.get("categories", []),
        "application_period_text": item.get("application_period_text"),
        "application_start": parse_date(item.get("application_start")),
        "application_end": parse_date(item.get("application_end")),
        "application_schedule": item.get("application_schedule"),
        "application_status": item.get("application_status"),
        "region_text": item.get("region_text"),
        "regions": item.get("regions", []),
        "age_min": item.get("age_min"),
        "age_max": item.get("age_max"),
        "age_condition_text": item.get("age_condition_text"),
        "eligibility_text": item.get("eligibility_text"),
        "support_content": item.get("support_content"),
        "application_method": item.get("application_method"),
        "education_statuses": item.get("education_statuses", []),
        "employment_statuses": item.get("employment_statuses", []),
        "required_conditions": item.get("required_conditions", []),
        "preferred_conditions": item.get("preferred_conditions", []),
        "excluded_conditions": item.get("excluded_conditions", []),
        "source_url": item.get("source_url", ""),
        "collected_at": parse_datetime(item.get("collected_at")),
        "provenance": item.get("provenance", []),
        "data_quality_status": item.get("data_quality_status", "valid"),
        "updated_at": datetime.now(timezone.utc),
    }


def _postgresql_upsert(db: Session, values: Mapping[str, Any]) -> str:
    statement = postgresql_insert(Policy).values(**values)
    changed = or_(
        *(
            Policy.__table__.c[field].is_distinct_from(
                getattr(statement.excluded, field)
            )
            for field in MUTABLE_FIELDS
        )
    )
    update_values = {
        field: getattr(statement.excluded, field)
        for field in MUTABLE_FIELDS
    }
    update_values["updated_at"] = values["updated_at"]

    statement = (
        statement.on_conflict_do_update(
            constraint="uq_policies_source_external",
            set_=update_values,
            where=changed,
        )
        .returning(
            literal_column(
                "xmax = 0",
                type_=Boolean,
            ).label("inserted")
        )
    )
    row = db.execute(statement).first()
    if row is None:
        return "unchanged"
    return "inserted" if row.inserted else "updated"


def _normalized_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _values_equal(current: Any, incoming: Any) -> bool:
    if isinstance(current, datetime) and isinstance(incoming, datetime):
        return _normalized_datetime(current) == _normalized_datetime(incoming)
    return current == incoming


def _portable_upsert(db: Session, values: Mapping[str, Any]) -> str:
    existing = db.execute(
        select(Policy).where(
            Policy.source_id == values["source_id"],
            Policy.external_id == values["external_id"],
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(Policy(**values))
        return "inserted"

    if all(
        _values_equal(getattr(existing, field), values[field])
        for field in MUTABLE_FIELDS
    ):
        return "unchanged"

    for field in MUTABLE_FIELDS:
        setattr(existing, field, values[field])
    existing.updated_at = values["updated_at"]
    return "updated"


def import_programs(
    db: Session,
    programs: Iterable[Mapping[str, Any]],
) -> ImportResult:
    items = list(programs)
    counts = {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "skipped": 0,
        "failed": 0,
    }
    issues: list[ImportIssue] = []
    use_postgresql = db.get_bind().dialect.name == "postgresql"

    for index, item in enumerate(items):
        identity_issue = _identity_issue(item, index)
        if identity_issue is not None:
            counts["skipped"] += 1
            issues.append(identity_issue)
            continue

        values = _policy_values(item)
        try:
            with db.begin_nested():
                if use_postgresql:
                    outcome = _postgresql_upsert(db, values)
                else:
                    outcome = _portable_upsert(db, values)
            counts[outcome] += 1
        except SQLAlchemyError as exc:
            counts["failed"] += 1
            issues.append(
                ImportIssue(
                    index=index,
                    source_id=values["source_id"],
                    external_id=values["external_id"],
                    code="database_write_failed",
                    error_type=type(exc).__name__,
                )
            )

    db.commit()
    return ImportResult(
        total=len(items),
        issues=tuple(issues),
        **counts,
    )


def import_seed_data(
    db: Session,
    seed_file_path: Path,
) -> ImportResult:
    if not seed_file_path.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_file_path}")

    with seed_file_path.open("r", encoding="utf-8") as seed_file:
        seed_data = json.load(seed_file)
    if not isinstance(seed_data, list):
        raise ValueError("Seed root must be a JSON array")
    return import_programs(db, seed_data)
