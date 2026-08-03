from datetime import datetime, timezone

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import JSON

from app.models.administrative_region import (
    AdministrativeRegion,
    AdministrativeRegionAlias,
)
from app.models.policy import Policy, utc_now
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument


def policy_values(**overrides):
    values = {
        "schema_version": "1.1.0",
        "source_id": "test-source",
        "source_name": "테스트 소스",
        "external_id": "TEST-001",
        "title": "테스트 정책",
        "categories": [],
        "keywords": [],
        "life_stages": [],
        "target_groups": [],
        "regions": [],
        "coverage_scope": "unknown",
        "education_statuses": [],
        "employment_statuses": [],
        "required_conditions": [],
        "preferred_conditions": [],
        "excluded_conditions": [],
        "source_url": "https://fixture.invalid/policies/TEST-001",
        "collected_at": utc_now(),
        "provenance": [],
        "data_quality_status": "valid",
    }
    values.update(overrides)
    return values


def test_policy_search_storage_table_contracts_are_registered():
    assert set(AdministrativeRegion.__table__.columns.keys()) == {
        "scheme",
        "code",
        "name",
        "full_name",
        "level",
        "status",
        "parent_code",
        "aggregate_parent_code",
        "source_parent_code",
        "valid_from",
        "valid_to",
        "external_codes",
    }
    assert set(AdministrativeRegionAlias.__table__.columns.keys()) == {
        "scheme",
        "alias",
        "region_code",
        "kind",
    }
    assert set(PolicyRegionRule.__table__.columns.keys()) == {
        "id",
        "policy_id",
        "relation",
        "resolution_status",
        "region_scheme",
        "region_code",
        "source_code",
        "source_text",
    }
    assert set(PolicySearchDocument.__table__.columns.keys()) == {
        "policy_id",
        "title_text",
        "keyword_text",
        "summary_text",
        "eligibility_text",
        "support_text",
        "search_text",
        "projection_version",
        "updated_at",
    }


def test_region_external_codes_use_jsonb_only_on_postgresql():
    column_type = AdministrativeRegion.__table__.c.external_codes.type

    assert isinstance(
        column_type.dialect_impl(postgresql.dialect()),
        JSONB,
    )
    assert isinstance(column_type.dialect_impl(sqlite.dialect()), JSON)


def test_rule_resolution_and_canonical_conflict_constraints_are_stable():
    check_names = {
        constraint.name
        for constraint in PolicyRegionRule.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_names = {
        constraint.name
        for constraint in PolicyRegionRule.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert check_names == {
        "ck_policy_region_rules_resolution_identity",
        "ck_policy_region_rules_source_code_nonempty",
        "ck_policy_region_rules_source_text_nonempty",
        "policy_region_relation",
        "policy_region_resolution_status",
    }
    assert unique_names == {"uq_policy_region_rules_canonical_region"}


def test_policy_rule_and_projection_round_trip_in_sqlite_boundary(db):
    region = AdministrativeRegion(
        scheme="test-kr",
        code="4400000000",
        name="충청남도",
        full_name="충청남도",
        level="province",
        status="active",
        external_codes={"test-prefix": "44"},
    )
    policy = Policy(
        **policy_values(
            external_id="SEARCH-001",
            schema_version="1.1.0",
            keywords=["월세"],
            life_stages=["청년"],
            target_groups=["청년가구"],
            coverage_scope="regional",
        )
    )
    db.add_all([region, policy])
    db.flush()
    rule = PolicyRegionRule(
        policy_id=policy.id,
        relation="include",
        resolution_status="matched",
        region_scheme=region.scheme,
        region_code=region.code,
        source_code="44000",
        source_text="충청남도",
    )
    document = PolicySearchDocument(
        policy_id=policy.id,
        title_text="청년 월세 지원",
        keyword_text="월세 청년",
        summary_text="",
        eligibility_text="",
        support_text="월 20만원",
        search_text="청년 월세 지원 월 20만원",
        projection_version="1.0.0",
        updated_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
    )
    db.add_all([rule, document])
    db.commit()

    assert policy.keywords == ["월세"]
    assert rule.region_code == "4400000000"
    assert document.search_text == "청년 월세 지원 월 20만원"


def test_unmapped_rule_requires_source_evidence_in_sqlite_boundary(db):
    policy = Policy(
        **policy_values(
            external_id="SEARCH-INVALID",
            schema_version="1.1.0",
            coverage_scope="unknown",
        )
    )
    db.add(policy)
    db.flush()
    db.add(
        PolicyRegionRule(
            policy_id=policy.id,
            relation="include",
            resolution_status="unmapped",
        )
    )

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
