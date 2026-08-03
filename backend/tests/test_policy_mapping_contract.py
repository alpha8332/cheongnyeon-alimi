import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from app.models.policy import Policy
from app.schemas.policy import PolicyRead
from app.services.seed_importer import (
    EXTERNAL_ID_REQUIRED_SOURCES,
    PENDING_SEARCH_STORAGE_FIELDS,
    _policy_values,
)
from collectors.normalized import NormalizedProgram


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "data" / "schema" / "normalized_program.schema.json"
SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
SYSTEM_FIELDS = frozenset({"id", "created_at", "updated_at"})
DATE_FIELDS = frozenset({"application_start", "application_end"})
JSON_ARRAY_FIELDS = frozenset(
    {
        "categories",
        "keywords",
        "life_stages",
        "target_groups",
        "regions",
        "education_statuses",
        "employment_statuses",
        "required_conditions",
        "preferred_conditions",
        "excluded_conditions",
        "provenance",
    }
)
NULLABLE_FIELDS = frozenset(
    {
        "external_id",
        "organization",
        "summary",
        "category_text",
        "application_period_text",
        "application_start",
        "application_end",
        "application_schedule",
        "application_status",
        "region_text",
        "age_min",
        "age_max",
        "age_condition_text",
        "eligibility_text",
        "support_content",
        "application_method",
    }
)


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_seed() -> list[dict]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def test_normalized_importer_orm_and_api_field_sets_are_explicit():
    schema = load_schema()
    normalized_fields = frozenset(schema["properties"])
    orm_fields = (
        frozenset(Policy.__table__.columns.keys()) - SYSTEM_FIELDS
    )
    importer_fields = (
        frozenset(_policy_values(load_seed()[0])) - SYSTEM_FIELDS
    )
    public_api_fields = frozenset(PolicyRead.model_fields)

    storage_candidate_fields = normalized_fields - {"region_rules"}

    assert len(normalized_fields) == 36
    assert frozenset(schema["required"]) == normalized_fields
    assert NormalizedProgram.FIELD_NAMES == normalized_fields
    assert PENDING_SEARCH_STORAGE_FIELDS == {"region_rules"}
    assert orm_fields == storage_candidate_fields
    assert importer_fields == storage_candidate_fields
    assert public_api_fields == (
        normalized_fields
        - NormalizedProgram.SEARCH_FIELD_NAMES
        - {"provenance"}
        | SYSTEM_FIELDS
    )


def test_nullable_and_jsonb_columns_match_the_normalized_contract():
    normalized_columns = [
        column
        for column in Policy.__table__.columns
        if column.name not in SYSTEM_FIELDS
    ]
    actual_nullable = frozenset(
        column.name for column in normalized_columns if column.nullable
    )

    assert actual_nullable == NULLABLE_FIELDS
    for field in JSON_ARRAY_FIELDS:
        column_type = Policy.__table__.c[field].type
        assert isinstance(
            column_type.dialect_impl(postgresql.dialect()),
            JSONB,
        )
        assert Policy.__table__.c[field].nullable is False


def test_importer_conversion_preserves_every_seed_field():
    for item in load_seed():
        values = _policy_values(item)

        for field in (
            NormalizedProgram.FIELD_NAMES - {"region_rules"}
        ):
            actual = values[field]
            expected = item[field]
            if field in DATE_FIELDS:
                assert (
                    actual.isoformat() if actual is not None else None
                ) == expected
            elif field == "collected_at":
                expected_datetime = datetime.fromisoformat(
                    expected.replace("Z", "+00:00")
                )
                assert actual.astimezone(timezone.utc) == (
                    expected_datetime.astimezone(timezone.utc)
                )
            else:
                assert actual == expected

        assert values["created_at"].tzinfo is not None
        assert values["updated_at"].tzinfo is not None
        assert values["created_at"] == values["updated_at"]
        assert item["keywords"] == []
        assert item["life_stages"] == []
        assert item["target_groups"] == []
        assert item["coverage_scope"] == "unknown"
        assert item["region_rules"] == []


def test_source_scoped_identity_and_current_source_admission_are_stable():
    identity_constraint = next(
        constraint
        for constraint in Policy.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_policies_source_external"
    )

    assert tuple(column.name for column in identity_constraint.columns) == (
        "source_id",
        "external_id",
    )
    assert EXTERNAL_ID_REQUIRED_SOURCES == {
        "youthcenter-api",
        "bokjiro-central-welfare-api",
    }
    assert all(item["external_id"] for item in load_seed())
