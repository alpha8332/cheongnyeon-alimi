import pytest
from datetime import date, datetime, timedelta, timezone
from app.models.policy import Policy
from app.models.policy_search import PolicySearchDocument
from app.repositories.policy_search import (
    PolicySearchRepository,
    _candidate_search_terms,
    _region_match_sort_key,
)
from app.services.policy_search_parser import parse_search_query


@pytest.fixture
def sample_policies(db, activate_all_policies):
    """테스트용 정책 DB 샘플 생성"""
    now = datetime.now(timezone.utc)

    # 1. 서울 24세 지원 가능 open 정책 (housing)
    p1 = Policy(
        source_id="test_1",
        external_id="TEST-1",
        source_name="온통청년",
        title="서울 청년 월세 특별지원",
        summary="서울 청년 대상 월세 지원금",
        categories=["housing"],
        application_status="open",
        region_text="서울특별시",
        regions=["1100000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/1",
        collected_at=now,
    )
    # 2. 전국 30세 지원 가능 scheduled 정책 (finance)
    p2 = Policy(
        source_id="test_2",
        external_id="TEST-2",
        source_name="복지로",
        title="청년 도약 계좌 적금",
        summary="전국 청년 자산 형성 대출 적금 지원",
        categories=["finance"],
        application_status="scheduled",
        region_text="전국",
        regions=[],
        age_min=19,
        age_max=34,
        coverage_scope="nationwide",
        data_quality_status="valid",
        source_url="https://example.com/2",
        collected_at=now,
    )
    # 3. 마감된 정책 (closed)
    p3 = Policy(
        source_id="test_3",
        external_id="TEST-3",
        source_name="온통청년",
        title="마감된 서울 주거 지원",
        categories=["housing"],
        application_status="closed",
        region_text="서울특별시",
        regions=["1100000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/3",
        collected_at=now,
    )

    db.add_all([p1, p2, p3])
    db.flush()

    # AdministrativeRegion 생성
    from app.models.administrative_region import AdministrativeRegion, AdministrativeRegionAlias
    reg1 = AdministrativeRegion(
        scheme="kr-bjd-20260803",
        code="1100000000",
        name="서울특별시",
        full_name="서울특별시",
        level="province",
        status="active",
    )
    alias1 = AdministrativeRegionAlias(
        scheme="kr-bjd-20260803",
        region_code="1100000000",
        alias="서울특별시",
        kind="curated",
    )
    db.add_all([reg1, alias1])

    # PolicyRegionRule 생성
    from app.models.policy_search import PolicyRegionRule
    r1 = PolicyRegionRule(
        policy_id=p1.id,
        relation="include",
        resolution_status="matched",
        region_scheme="kr-bjd-20260803",
        region_code="1100000000",
        source_code="1100000000",
        source_text="서울특별시",
    )
    db.add(r1)

    # Search document 생성
    d1 = PolicySearchDocument(
        policy_id=p1.id,
        title_text="서울 청년 월세 특별지원",
        keyword_text="월세 주거 지원금 청년",
        summary_text="서울 청년 대상 월세 지원금",
        eligibility_text="19세~39세 청년",
        support_text="월 20만원 지원",
        search_text="서울 청년 월세 특별지원 월세 주거 지원금 청년 서울 청년 대상 월세 지원금 19세~39세 청년 월 20만원 지원",
        projection_version="1.1.0",
        updated_at=now,
    )
    d2 = PolicySearchDocument(
        policy_id=p2.id,
        title_text="청년 도약 계좌 적금",
        keyword_text="도약 적금 자산 금융 대출",
        summary_text="전국 청년 자산 형성 대출 적금 지원",
        eligibility_text="19세~34세 청년",
        support_text="자산 형성 지원",
        search_text="청년 도약 계좌 적금 도약 적금 자산 금융 대출 전국 청년 자산 형성 대출 적금 지원 19세~34세 청년 자산 형성 지원",
        projection_version="1.1.0",
        updated_at=now,
    )

    db.add_all([d1, d2])
    db.commit()
    activate_all_policies()

    return [p1, p2, p3]


def test_repository_search_policies_basic(db, sample_policies):
    repo = PolicySearchRepository(db)

    # 1. 서울 24세 월세 검색어 파싱
    interpreted = parse_search_query(q="서울 24세 월세 모집중", db=db)
    items, total = repo.search_policies(interpreted, include_partial=True, page=1, limit=10)

    # 결과 검증: closed 정책(p3)은 제외되어 p1이 1위여야 함
    assert total >= 1
    top_item = items[0]
    assert top_item.policy.id == sample_policies[0].id
    assert top_item.verdicts.status == "match"
    assert top_item.verdicts.age == "match"
    assert top_item.verdicts.category == "match"
    assert top_item.unknown_count == 0


def test_repository_search_policies_status_closed_filter(db, sample_policies):
    repo = PolicySearchRepository(db)

    # status="closed" 명시적 검색
    interpreted = parse_search_query(q="서울 주거 지원", status="closed", db=db)
    items, total = repo.search_policies(interpreted, page=1, limit=10)

    assert total == 1
    assert items[0].policy.id == sample_policies[2].id
    assert items[0].verdicts.status == "match"


@pytest.mark.parametrize("lifecycle_state", ["inactive", "expired"])
def test_repository_search_excludes_nonpublic_lifecycle_rows(
    db,
    sample_policies,
    lifecycle_state,
):
    policy = sample_policies[0]
    if lifecycle_state == "inactive":
        policy.inactive_at = datetime.now(timezone.utc)
    else:
        policy.application_end = date.today() - timedelta(days=1)
    db.commit()

    interpreted = parse_search_query(q="서울 24세 월세 모집중", db=db)
    items, total = PolicySearchRepository(db).search_policies(
        interpreted,
        include_partial=True,
        page=1,
        limit=10,
    )

    assert total == 0
    assert items == []


def test_repository_search_policies_deterministic_sorting(db, sample_policies):
    repo = PolicySearchRepository(db)

    # 자연어 키워드 검색
    interpreted = parse_search_query(q="청년 적금", db=db)
    items, total = repo.search_policies(interpreted, page=1, limit=10)

    assert total >= 1
    # p2 (청년 도약 계좌 적금)가 적금 키워드 매칭으로 상위에 위치
    assert items[0].policy.id == sample_policies[1].id


def test_repository_search_policies_unmatched_term_returns_zero(db, sample_policies):
    repo = PolicySearchRepository(db)

    # 일치하는 검색어가 하나도 없는 경우 0건 반환 검증 (Blocker 1 해결)
    interpreted = parse_search_query(q="존재하지않는특수키워드검색어12345", db=db)
    items, total = repo.search_policies(interpreted, page=1, limit=10)

    assert total == 0
    assert items == []


def test_specific_anchor_excludes_generic_terms_from_candidate_expansion():
    terms, require_all = _candidate_search_terms(
        ["청년", "지원", "단기숙소"],
        None,
    )

    assert terms == ["단기숙소"]
    assert require_all is True


def test_generic_only_query_preserves_discovery_fallback():
    terms, require_all = _candidate_search_terms(["청년", "지원"], None)

    assert terms == ["청년", "지원"]
    assert require_all is False


def test_repository_generic_only_query_keeps_or_discovery(db, sample_policies):
    repo = PolicySearchRepository(db)
    interpreted = parse_search_query(q="청년 지원", db=db)

    items, total = repo.search_policies(interpreted, page=1, limit=10)

    assert total == 2
    assert {item.policy.id for item in items} == {
        sample_policies[0].id,
        sample_policies[1].id,
    }


def test_region_match_sort_prioritizes_narrow_direct_scope():
    local = _region_match_sort_key(
        has_region_condition=True,
        verdict="match",
        reason="exact",
        region_count=1,
    )
    broad = _region_match_sort_key(
        has_region_condition=True,
        verdict="match",
        reason="exact",
        region_count=254,
    )
    nationwide = _region_match_sort_key(
        has_region_condition=True,
        verdict="match",
        reason="nationwide",
        region_count=0,
    )
    unknown = _region_match_sort_key(
        has_region_condition=True,
        verdict="unknown",
        reason=None,
        region_count=0,
    )

    assert local < broad < nationwide < unknown


def test_explicit_generic_keyword_is_still_a_required_anchor():
    terms, require_all = _candidate_search_terms(["청년"], "지원")

    assert terms == ["지원"]
    assert require_all is True
