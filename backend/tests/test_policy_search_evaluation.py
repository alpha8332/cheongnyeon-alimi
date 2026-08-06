from types import SimpleNamespace

import pytest

from app.models.administrative_region import (
    AdministrativeRegion,
    AdministrativeRegionAlias,
)
from app.models.policy import Policy, utc_now
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument
from app.services.policy_search_evaluation import (
    AgeDecisionReason,
    MatchState,
    PolicySearchEvaluationService,
    ProjectionField,
    ProjectionFieldMatch,
    RegionDecisionReason,
    RegionResolutionState,
    StatusDecisionReason,
    evaluate_age_condition,
    evaluate_application_status,
    match_projection_fields,
)


SCHEME = "kr-bjd-20260803"


def _policy(external_id: str, **overrides) -> Policy:
    values = {
        "schema_version": "1.1.0",
        "source_id": "psf6-test",
        "source_name": "PSF6 test",
        "external_id": external_id,
        "title": external_id,
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
        "source_url": f"https://fixture.invalid/{external_id}",
        "collected_at": utc_now(),
        "provenance": [],
        "data_quality_status": "valid",
    }
    values.update(overrides)
    return Policy(**values)


def _region(code: str, name: str, level: str, **overrides):
    values = {
        "scheme": SCHEME,
        "code": code,
        "name": name,
        "full_name": name,
        "level": level,
        "status": "active",
        "external_codes": {},
    }
    values.update(overrides)
    return AdministrativeRegion(**values)


def _rule(policy_id: int, code: str, relation: str = "include"):
    return PolicyRegionRule(
        policy_id=policy_id,
        relation=relation,
        resolution_status="matched",
        region_scheme=SCHEME,
        region_code=code,
    )


def test_age_and_application_status_use_three_value_decisions():
    assert evaluate_age_condition(
        requested_age=27,
        age_min=19,
        age_max=34,
        age_condition_text=None,
    ).state is MatchState.MATCH
    assert evaluate_age_condition(
        requested_age=35,
        age_min=19,
        age_max=34,
        age_condition_text=None,
    ).reason is AgeDecisionReason.ABOVE_MAXIMUM
    assert evaluate_age_condition(
        requested_age=27,
        age_min=None,
        age_max=None,
        age_condition_text="연령 제한 없음",
    ).reason is AgeDecisionReason.UNRESTRICTED
    assert evaluate_age_condition(
        requested_age=27,
        age_min=None,
        age_max=None,
        age_condition_text="세부 공고 확인",
    ).state is MatchState.UNKNOWN

    assert evaluate_application_status(
        requested_status="open",
        policy_status="open",
    ).reason is StatusDecisionReason.EQUAL
    assert evaluate_application_status(
        requested_status="open",
        policy_status="closed",
    ).state is MatchState.MISMATCH
    assert evaluate_application_status(
        requested_status="open",
        policy_status=None,
    ).state is MatchState.UNKNOWN

    with pytest.raises(ValueError):
        evaluate_age_condition(
            requested_age=True,
            age_min=None,
            age_max=None,
            age_condition_text=None,
        )
    with pytest.raises(ValueError):
        evaluate_application_status(
            requested_status="any",
            policy_status="open",
        )


def test_projection_match_preserves_field_specific_evidence():
    document = SimpleNamespace(
        title_text="청년 월세 지원",
        keyword_text="주거 월세",
        summary_text="주거비를 지원합니다",
        eligibility_text="천안 거주 19세 이상",
        support_text="월 20만원",
    )

    evidence = match_projection_fields(
        document=document,
        terms=["청년월세", "천안   거주", "없는 조건", "천안 거주"],
    )

    assert evidence.fields == (
        ProjectionFieldMatch(
            ProjectionField.TITLE,
            ("청년월세",),
        ),
        ProjectionFieldMatch(
            ProjectionField.ELIGIBILITY,
            ("천안 거주",),
        ),
    )
    assert evidence.unmatched_terms == ("없는 조건",)


def test_region_service_handles_hierarchy_ambiguity_and_exclusion(db):
    country = _region("0000000000", "대한민국", "country")
    chungnam = _region(
        "4400000000",
        "충청남도",
        "province",
        parent_code=country.code,
    )
    cheonan = _region(
        "4413000000",
        "천안시",
        "district",
        parent_code=chungnam.code,
    )
    dongnam = _region(
        "4413100000",
        "동남구",
        "district",
        parent_code=chungnam.code,
        aggregate_parent_code=cheonan.code,
    )
    asan = _region(
        "4420000000",
        "아산시",
        "district",
        parent_code=chungnam.code,
    )
    seoul_junggu = _region(
        "1114000000",
        "중구",
        "district",
        parent_code=country.code,
    )
    busan_junggu = _region(
        "2611000000",
        "중구",
        "district",
        parent_code=country.code,
    )
    db.add_all(
        [
            country,
            chungnam,
            cheonan,
            dongnam,
            asan,
            seoul_junggu,
            busan_junggu,
        ]
    )
    db.flush()
    db.add_all(
        [
            AdministrativeRegionAlias(
                scheme=SCHEME,
                alias="천안",
                region_code=cheonan.code,
                kind="curated",
            ),
            AdministrativeRegionAlias(
                scheme=SCHEME,
                alias="중구",
                region_code=seoul_junggu.code,
                kind="official_short",
            ),
            AdministrativeRegionAlias(
                scheme=SCHEME,
                alias="천안시 동남구",
                region_code=dongnam.code,
                kind="official_full",
            ),
            AdministrativeRegionAlias(
                scheme=SCHEME,
                alias="중구",
                region_code=busan_junggu.code,
                kind="official_short",
            ),
        ]
    )
    policies = {
        "nationwide": _policy("nationwide", coverage_scope="nationwide"),
        "unknown": _policy("unknown", coverage_scope="unknown"),
        "exact": _policy("exact", coverage_scope="regional"),
        "ancestor": _policy("ancestor", coverage_scope="regional"),
        "other": _policy("other", coverage_scope="regional"),
        "excluded": _policy("excluded", coverage_scope="regional"),
        "unresolved": _policy("unresolved", coverage_scope="regional"),
    }
    db.add_all(policies.values())
    db.flush()
    db.add_all(
        [
            _rule(policies["exact"].id, cheonan.code),
            _rule(policies["ancestor"].id, chungnam.code),
            _rule(policies["other"].id, asan.code),
            _rule(policies["excluded"].id, chungnam.code),
            _rule(policies["excluded"].id, cheonan.code, "exclude"),
            PolicyRegionRule(
                policy_id=policies["unresolved"].id,
                relation="include",
                resolution_status="ambiguous",
                source_text="중구",
            ),
        ]
    )
    db.add(
        PolicySearchDocument(
            policy_id=policies["exact"].id,
            title_text="청년 월세 지원",
            keyword_text="주거 월세",
            summary_text="",
            eligibility_text="천안 거주",
            support_text="월 20만원",
            search_text="청년 월세 지원 주거 월세 천안 거주 월 20만원",
            projection_version="1.0.0",
        )
    )
    db.commit()

    service = PolicySearchEvaluationService(db)
    cheonan_query = service.resolve_region_alias("  천안 ")
    dongnam_query = service.resolve_region_alias("천안시 동남구")
    ambiguous_query = service.resolve_region_alias("중구")
    unmapped_query = service.resolve_region_alias("없는 지역")

    assert cheonan_query.status is RegionResolutionState.MATCHED
    assert ambiguous_query.status is RegionResolutionState.AMBIGUOUS
    assert len(ambiguous_query.candidates) == 2
    assert unmapped_query.status is RegionResolutionState.UNMAPPED
    assert service.evaluate_policy_region(
        policies["exact"].id, cheonan_query
    ).reason is RegionDecisionReason.EXACT
    assert service.evaluate_policy_region(
        policies["exact"].id, dongnam_query
    ).reason is RegionDecisionReason.ANCESTOR
    assert service.evaluate_policy_region(
        policies["ancestor"].id, cheonan_query
    ).reason is RegionDecisionReason.ANCESTOR
    assert service.evaluate_policy_region(
        policies["nationwide"].id, ambiguous_query
    ).reason is RegionDecisionReason.NATIONWIDE
    assert service.evaluate_policy_region(
        policies["other"].id, cheonan_query
    ).reason is RegionDecisionReason.OTHER_REGION
    assert service.evaluate_policy_region(
        policies["unknown"].id, cheonan_query
    ).reason is RegionDecisionReason.POLICY_UNKNOWN
    excluded = service.evaluate_policy_region(
        policies["excluded"].id, cheonan_query
    )
    assert excluded.reason is RegionDecisionReason.EXCLUDE
    assert excluded.evidence.match_distance == 0
    assert service.evaluate_policy_region(
        policies["unresolved"].id, cheonan_query
    ).reason is RegionDecisionReason.UNRESOLVED_RULE
    assert service.evaluate_policy_region(
        policies["exact"].id, ambiguous_query
    ).reason is RegionDecisionReason.QUERY_AMBIGUOUS
    assert service.evaluate_policy_region(
        policies["exact"].id, unmapped_query
    ).reason is RegionDecisionReason.QUERY_UNMAPPED

    projection = service.match_policy_projection(
        policies["exact"].id,
        ["청년월세", "천안"],
    )
    assert {item.field for item in projection.fields} == {
        ProjectionField.TITLE,
        ProjectionField.ELIGIBILITY,
    }
