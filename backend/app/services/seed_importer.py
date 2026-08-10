import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, func, literal_column, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.policy import Policy, utc_now
from app.services.policy_search_projection import (
    synchronize_policy_search_storage,
)
from collectors.normalized import DataQualityStatus
from collectors.validation import NormalizedProgramValidator, ValidationIssue


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
COLLECTION_METADATA_FIELDS = frozenset({"collected_at", "provenance"})
BUSINESS_MUTABLE_FIELDS = tuple(
    field for field in MUTABLE_FIELDS if field not in COLLECTION_METADATA_FIELDS
)


@dataclass(frozen=True)
class ImportIssue:
    index: int
    source_id: str | None
    external_id: str | None
    code: str
    stage: str | None = None
    path: str | None = None
    error_type: str | None = None


@dataclass(frozen=True)
class ImportResult:
    total: int
    validated: int = 0
    accepted: int = 0
    partial: int = 0
    invalid: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    duplicate: int = 0
    skipped: int = 0
    rejected: int = 0
    failed: int = 0
    committed: bool = False
    dry_run: bool = False
    issues: tuple[ImportIssue, ...] = ()


def parse_date(date_str: Any) -> date | None:
    if date_str is None:
        return None
    if not isinstance(date_str, str):
        raise TypeError("date value must be a string or null")
    return date.fromisoformat(date_str)


def parse_datetime(dt_str: Any) -> datetime:
    if not isinstance(dt_str, str):
        raise TypeError("datetime value must be a string")
    parsed = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("datetime value must include a timezone")
    return parsed


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
            stage="validate",
            path=f"$[{index}].source_id",
        )
    if external_id is None and source_id in EXTERNAL_ID_REQUIRED_SOURCES:
        return ImportIssue(
            index=index,
            source_id=source_id,
            external_id=None,
            code="missing_external_id",
            stage="validate",
            path=f"$[{index}].external_id",
        )
    if external_id is None:
        return ImportIssue(
            index=index,
            source_id=source_id,
            external_id=None,
            code="unsupported_null_external_id",
            stage="validate",
            path=f"$[{index}].external_id",
        )
    return None


def _policy_values(item: Mapping[str, Any]) -> dict[str, Any]:
    write_instant = utc_now()
    return {
        "schema_version": item["schema_version"],
        "source_id": _nonempty_string(item.get("source_id")),
        "source_name": item["source_name"],
        "external_id": _nonempty_string(item.get("external_id")),
        "title": item["title"],
        "organization": item.get("organization"),
        "summary": item.get("summary"),
        "category_text": item.get("category_text"),
        "categories": item["categories"],
        "keywords": item["keywords"],
        "life_stages": item["life_stages"],
        "target_groups": item["target_groups"],
        "application_period_text": item.get("application_period_text"),
        "application_start": parse_date(item.get("application_start")),
        "application_end": parse_date(item.get("application_end")),
        "application_schedule": item.get("application_schedule"),
        "application_status": item.get("application_status"),
        "region_text": item.get("region_text"),
        "regions": item["regions"],
        "coverage_scope": item["coverage_scope"],
        "age_min": item.get("age_min"),
        "age_max": item.get("age_max"),
        "age_condition_text": item.get("age_condition_text"),
        "eligibility_text": item.get("eligibility_text"),
        "support_content": item.get("support_content"),
        "application_method": item.get("application_method"),
        "education_statuses": item["education_statuses"],
        "employment_statuses": item["employment_statuses"],
        "required_conditions": item["required_conditions"],
        "preferred_conditions": item["preferred_conditions"],
        "excluded_conditions": item["excluded_conditions"],
        "source_url": item["source_url"],
        "collected_at": parse_datetime(item["collected_at"]),
        "provenance": item["provenance"],
        "data_quality_status": item["data_quality_status"],
        "created_at": write_instant,
        "updated_at": write_instant,
    }


def _postgresql_upsert(
    db: Session,
    values: Mapping[str, Any],
) -> tuple[str, int]:
    statement = postgresql_insert(Policy).values(**values)
    changed = or_(
        *(
            Policy.__table__.c[field].is_distinct_from(
                getattr(statement.excluded, field)
            )
            for field in BUSINESS_MUTABLE_FIELDS
        )
    )
    update_values = {
        field: getattr(statement.excluded, field)
        for field in MUTABLE_FIELDS
    }
    update_values["updated_at"] = func.greatest(
        Policy.updated_at,
        statement.excluded.updated_at,
    )

    statement = (
        statement.on_conflict_do_update(
            constraint="uq_policies_source_external",
            set_=update_values,
            where=changed,
        )
        .returning(
            Policy.id,
            literal_column(
                "xmax = 0",
                type_=Boolean,
            ).label("inserted")
        )
    )
    row = db.execute(statement).first()
    if row is None:
        policy_id = db.scalar(
            select(Policy.id).where(
                Policy.source_id == values["source_id"],
                Policy.external_id == values["external_id"],
            )
        )
        if policy_id is None:
            raise RuntimeError("upserted policy identity was not found")
        return "unchanged", policy_id
    return ("inserted" if row.inserted else "updated"), row.id


def _normalized_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _values_equal(current: Any, incoming: Any) -> bool:
    if isinstance(current, datetime) and isinstance(incoming, datetime):
        return _normalized_datetime(current) == _normalized_datetime(incoming)
    return current == incoming


def _nondecreasing_datetime(
    current: datetime,
    incoming: datetime,
) -> datetime:
    if _normalized_datetime(incoming) < _normalized_datetime(current):
        return current
    return incoming


def _portable_upsert(
    db: Session,
    values: Mapping[str, Any],
) -> tuple[str, int]:
    existing = db.execute(
        select(Policy).where(
            Policy.source_id == values["source_id"],
            Policy.external_id == values["external_id"],
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Policy(**values)
        db.add(existing)
        db.flush()
        return "inserted", existing.id

    if all(
        _values_equal(getattr(existing, field), values[field])
        for field in BUSINESS_MUTABLE_FIELDS
    ):
        return "unchanged", existing.id

    for field in MUTABLE_FIELDS:
        setattr(existing, field, values[field])
    existing.updated_at = _nondecreasing_datetime(
        existing.updated_at,
        values["updated_at"],
    )
    return "updated", existing.id


class _DryRunRollback(Exception):
    """Internal control flow used to roll back a successful dry run."""


def _item_path(index: int, path: str) -> str:
    if path == "$":
        return f"$[{index}]"
    if path.startswith("$."):
        return f"$[{index}]{path[1:]}"
    return f"$[{index}].{path}"


def _preflight_programs(
    items: list[Any],
    validator: NormalizedProgramValidator,
    normalization_issues: Sequence[Sequence[ValidationIssue]],
) -> tuple[
    list[tuple[int, Mapping[str, Any]]],
    int,
    int,
    int,
    int,
    int,
    int,
    list[ImportIssue],
]:
    accepted: list[tuple[int, Mapping[str, Any]]] = []
    issues: list[ImportIssue] = []
    validated = 0
    partial = 0
    invalid = 0
    skipped = 0
    rejected = 0
    duplicate = 0
    seen_identities: set[tuple[str, str]] = set()

    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            invalid += 1
            rejected += 1
            issues.append(
                ImportIssue(
                    index=index,
                    source_id=None,
                    external_id=None,
                    code="item_not_object",
                    stage="validate",
                    path=f"$[{index}]",
                )
            )
            continue

        validated += 1
        validation = validator.validate(
            item,
            normalization_issues[index],
        )
        if (
            validation.status is DataQualityStatus.INVALID
            or validation.program is None
        ):
            invalid += 1
            rejected += 1
            error_issues = tuple(
                issue
                for issue in validation.issues
                if issue.severity == "error"
            )
            for issue in error_issues:
                issues.append(
                    ImportIssue(
                        index=index,
                        source_id=_nonempty_string(item.get("source_id")),
                        external_id=_nonempty_string(
                            item.get("external_id")
                        ),
                        code=issue.code,
                        stage="validate",
                        path=_item_path(index, issue.path),
                    )
                )
            if not error_issues:
                issues.append(
                    ImportIssue(
                        index=index,
                        source_id=_nonempty_string(item.get("source_id")),
                        external_id=_nonempty_string(
                            item.get("external_id")
                        ),
                        code="normalized_program_invalid",
                        stage="validate",
                        path=f"$[{index}]",
                    )
                )
            continue

        candidate = validation.program.to_dict()
        identity_issue = _identity_issue(candidate, index)
        if identity_issue is not None:
            rejected += 1
            issues.append(identity_issue)
            continue
        identity = (candidate["source_id"], candidate["external_id"])
        if identity in seen_identities:
            duplicate += 1
            issues.append(
                ImportIssue(
                    index=index,
                    source_id=identity[0],
                    external_id=identity[1],
                    code="duplicate_identity",
                    stage="validate",
                    path=f"$[{index}]",
                )
            )
            continue
        seen_identities.add(identity)
        accepted.append((index, candidate))
        if validation.status is DataQualityStatus.PARTIAL:
            partial += 1

    return (
        accepted,
        validated,
        partial,
        invalid,
        skipped,
        rejected,
        duplicate,
        issues,
    )


def import_programs(
    db: Session,
    programs: Iterable[Any],
    *,
    dry_run: bool = False,
    validator: NormalizedProgramValidator | None = None,
    normalization_issues: Sequence[Sequence[ValidationIssue]] | None = None,
) -> ImportResult:
    items = list(programs)
    selected_validator = validator or NormalizedProgramValidator()
    selected_normalization_issues = (
        tuple(() for _ in items)
        if normalization_issues is None
        else tuple(tuple(issues) for issues in normalization_issues)
    )
    if len(selected_normalization_issues) != len(items):
        raise ValueError(
            "normalization_issues must align with programs"
        )
    (
        accepted,
        validated,
        partial,
        invalid,
        skipped,
        rejected,
        duplicate,
        issues,
    ) = _preflight_programs(
        items,
        selected_validator,
        selected_normalization_issues,
    )
    if skipped or rejected:
        return ImportResult(
            total=len(items),
            validated=validated,
            accepted=len(accepted),
            partial=partial,
            invalid=invalid,
            skipped=skipped,
            rejected=rejected,
            duplicate=duplicate,
            dry_run=dry_run,
            issues=tuple(issues),
        )

    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    use_postgresql = db.get_bind().dialect.name == "postgresql"
    current_index = -1
    current_values: Mapping[str, Any] = {}
    try:
        with db.begin():
            for current_index, item in accepted:
                current_values = _policy_values(item)
                if use_postgresql:
                    outcome, policy_id = _postgresql_upsert(
                        db,
                        current_values,
                    )
                else:
                    outcome, policy_id = _portable_upsert(
                        db,
                        current_values,
                    )
                db.flush()
                search_sync = synchronize_policy_search_storage(
                    db,
                    policy_id=policy_id,
                    policy=item,
                    updated_at=current_values["updated_at"],
                )
                if outcome == "unchanged" and search_sync.changed:
                    policy = db.get(Policy, policy_id)
                    if policy is None:
                        raise RuntimeError(
                            "search storage policy was not found"
                        )
                    policy.updated_at = _nondecreasing_datetime(
                        policy.updated_at,
                        current_values["updated_at"],
                    )
                    outcome = "updated"
                db.flush()
                counts[outcome] += 1
            if dry_run:
                raise _DryRunRollback
    except _DryRunRollback:
        pass
    except SQLAlchemyError as exc:
        return ImportResult(
            total=len(items),
            validated=validated,
            accepted=len(accepted),
            partial=partial,
            invalid=invalid,
            failed=1,
            duplicate=duplicate,
            dry_run=dry_run,
            issues=(
                ImportIssue(
                    index=current_index,
                    source_id=_nonempty_string(
                        current_values.get("source_id")
                    ),
                    external_id=_nonempty_string(
                        current_values.get("external_id")
                    ),
                    code="database_write_failed",
                    stage="persist",
                    path=(
                        f"$[{current_index}]"
                        if current_index >= 0
                        else "$"
                    ),
                    error_type=type(exc).__name__,
                ),
            ),
        )

    return ImportResult(
        total=len(items),
        validated=validated,
        accepted=len(accepted),
        partial=partial,
        invalid=invalid,
        committed=not dry_run,
        dry_run=dry_run,
        issues=tuple(issues),
        duplicate=duplicate,
        **counts,
    )


def import_seed_data(
    db: Session,
    seed_file_path: Path,
    *,
    dry_run: bool = False,
    validator: NormalizedProgramValidator | None = None,
) -> ImportResult:
    if not seed_file_path.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_file_path}")

    with seed_file_path.open("r", encoding="utf-8") as seed_file:
        seed_data = json.load(seed_file)
    if not isinstance(seed_data, list):
        return ImportResult(
            total=0,
            invalid=1,
            rejected=1,
            dry_run=dry_run,
            issues=(
                ImportIssue(
                    index=-1,
                    source_id=None,
                    external_id=None,
                    code="seed_root_not_array",
                    stage="validate",
                    path="$",
                ),
            ),
        )
    return import_programs(
        db,
        seed_data,
        dry_run=dry_run,
        validator=validator,
    )
