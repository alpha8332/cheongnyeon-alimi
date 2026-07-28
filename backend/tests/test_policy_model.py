import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.types import JSON

from app.models.policy import Policy, utc_now


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "schema"
    / "normalized_program.schema.json"
)
JSON_COLUMNS = {
    "categories",
    "regions",
    "education_statuses",
    "employment_statuses",
    "required_conditions",
    "preferred_conditions",
    "excluded_conditions",
    "provenance",
}


def policy_values(**overrides):
    values = {
        "schema_version": "1.0.0",
        "source_id": "test-source",
        "source_name": "테스트 소스",
        "external_id": "TEST-001",
        "title": "테스트 정책",
        "categories": [],
        "regions": [],
        "education_statuses": [],
        "employment_statuses": [],
        "required_conditions": [],
        "preferred_conditions": [],
        "excluded_conditions": [],
        "source_url": "https://fixture.invalid/policies/TEST-001",
        "collected_at": utc_now(),
        "provenance": [
            {
                "raw_document_id": "a" * 32,
                "document_role": "list_item",
                "content_hash": f"sha256:{'b' * 64}",
                "collected_at": "2026-07-28T00:00:00+00:00",
                "source_url": "https://fixture.invalid/api",
            }
        ],
        "data_quality_status": "valid",
    }
    values.update(overrides)
    return values


def test_policy_columns_cover_normalized_program_contract():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    model_columns = set(Policy.__table__.columns.keys()) - {
        "id",
        "created_at",
        "updated_at",
    }

    assert len(schema["required"]) == 31
    assert model_columns == set(schema["properties"])


def test_json_columns_use_jsonb_only_for_postgresql():
    for column_name in JSON_COLUMNS:
        column_type = Policy.__table__.c[column_name].type

        assert isinstance(
            column_type.dialect_impl(postgresql.dialect()),
            JSONB,
        )
        assert isinstance(
            column_type.dialect_impl(sqlite.dialect()),
            JSON,
        )


def test_timestamp_columns_are_timezone_aware():
    for column_name in ("collected_at", "created_at", "updated_at"):
        assert Policy.__table__.c[column_name].type.timezone is True

    assert utc_now().utcoffset() == timedelta(0)


def test_json_arrays_and_provenance_round_trip_in_sqlite_unit_boundary(db):
    values = policy_values(
        categories=["housing", "welfare"],
        regions=["서울특별시"],
        education_statuses=["대학생"],
        employment_statuses=["미취업"],
        required_conditions=["독립 거주"],
        preferred_conditions=["신규 신청자"],
        excluded_conditions=["중복 수혜자"],
        application_schedule="always",
        application_status="open",
    )
    policy = Policy(**values)
    db.add(policy)
    db.commit()
    db.refresh(policy)

    assert policy.categories == ["housing", "welfare"]
    assert policy.regions == ["서울특별시"]
    assert policy.education_statuses == ["대학생"]
    assert policy.employment_statuses == ["미취업"]
    assert policy.required_conditions == ["독립 거주"]
    assert policy.preferred_conditions == ["신규 신청자"]
    assert policy.excluded_conditions == ["중복 수혜자"]
    assert policy.provenance == values["provenance"]


def test_policy_constraint_and_index_names_are_stable():
    check_names = {
        constraint.name
        for constraint in Policy.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    index_names = {index.name for index in Policy.__table__.indexes}

    assert check_names == {
        "ck_policies_age_min_range",
        "ck_policies_age_max_range",
        "ck_policies_age_order",
        "ck_policies_application_date_order",
        "policy_application_schedule",
        "policy_application_status",
        "policy_data_quality_status",
    }
    assert index_names == {
        "ix_policies_source_id",
        "ix_policies_external_id",
        "ix_policies_data_quality_status",
        "ix_policies_categories_gin",
        "ix_policies_regions_gin",
    }


@pytest.mark.parametrize(
    "invalid_values",
    [
        {"age_min": -1},
        {"age_max": 151},
        {"age_min": 30, "age_max": 20},
        {
            "application_start": date(2026, 8, 2),
            "application_end": date(2026, 8, 1),
        },
    ],
)
def test_sqlite_unit_boundary_enforces_portable_checks(db, invalid_values):
    db.add(Policy(**policy_values(**invalid_values)))

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()


def test_enum_values_are_validated_before_database_write(db):
    db.add(Policy(**policy_values(data_quality_status="unknown")))

    with pytest.raises(StatementError):
        db.flush()

    db.rollback()
