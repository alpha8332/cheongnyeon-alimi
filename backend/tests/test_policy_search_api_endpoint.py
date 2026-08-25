from datetime import datetime, timezone
import pytest
from app.models.administrative_region import AdministrativeRegion, AdministrativeRegionAlias
from app.models.policy import Policy
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument


def test_search_api_basic_200_ok(client, db, activate_all_policies):
    now = datetime.now(timezone.utc)
    # DB 테스트 데이터 준비
    p = Policy(
        source_id="test_search_1",
        external_id="SEARCH-1",
        source_name="온통청년",
        title="서울 청년 월세 특별지원",
        summary="서울 청년 월세 지원금",
        categories=["housing"],
        application_status="open",
        region_text="서울특별시",
        regions=["1100000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/search1",
        collected_at=now,
    )
    db.add(p)
    db.flush()

    reg = AdministrativeRegion(
        scheme="kr-bjd-20260803",
        code="1100000000",
        name="서울특별시",
        full_name="서울특별시",
        level="province",
        status="active",
    )
    alias = AdministrativeRegionAlias(
        scheme="kr-bjd-20260803",
        region_code="1100000000",
        alias="서울특별시",
        kind="curated",
    )
    rule = PolicyRegionRule(
        policy_id=p.id,
        relation="include",
        resolution_status="matched",
        region_scheme="kr-bjd-20260803",
        region_code="1100000000",
        source_code="1100000000",
        source_text="서울특별시",
    )
    doc = PolicySearchDocument(
        policy_id=p.id,
        title_text="서울 청년 월세 특별지원",
        keyword_text="월세 주거 지원금 청년",
        summary_text="서울 청년 월세 지원금",
        eligibility_text="19세~39세 청년",
        support_text="월 20만원 지원",
        search_text="서울 청년 월세 특별지원 월세 주거 지원금 청년",
        projection_version="1.1.0",
        updated_at=now,
    )
    db.add_all([reg, alias, rule, doc])
    db.commit()
    activate_all_policies()

    # GET /api/v1/policies/search 요청
    response = client.get("/api/v1/policies/search?q=서울 24세 월세 모집중")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "interpreted_conditions" in data
    assert "items" in data
    assert data["total"] >= 1

    top_item = data["items"][0]
    assert top_item["policy"]["id"] == p.id
    assert top_item["verdicts"]["status"] == "match"
    assert top_item["verdicts"]["age"] == "match"
    assert top_item["verdicts"]["region"] == "match"


def test_search_api_resolves_compound_local_region(
    client,
    db,
    activate_all_policies,
):
    now = datetime.now(timezone.utc)
    policy = Policy(
        source_id="test_search_yangsan",
        external_id="SEARCH-YANGSAN-1",
        source_name="온통청년",
        title="양산 청년 취업 지원",
        summary="양산시 거주 청년 취업 지원",
        categories=["employment"],
        application_status="open",
        region_text="경상남도 양산시",
        regions=["4833000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/yangsan-search",
        collected_at=now,
    )
    gyeongnam = AdministrativeRegion(
        scheme="kr-bjd-20260803",
        code="4800000000",
        name="경상남도",
        full_name="경상남도",
        level="province",
        status="active",
    )
    yangsan = AdministrativeRegion(
        scheme="kr-bjd-20260803",
        code="4833000000",
        name="양산시",
        full_name="경상남도 양산시",
        level="district",
        status="active",
        parent_code=gyeongnam.code,
    )
    db.add_all([policy, gyeongnam, yangsan])
    db.flush()
    db.add_all(
        [
            PolicyRegionRule(
                policy_id=policy.id,
                relation="include",
                resolution_status="matched",
                region_scheme="kr-bjd-20260803",
                region_code=yangsan.code,
                source_code=yangsan.code,
                source_text=yangsan.full_name,
            ),
            PolicySearchDocument(
                policy_id=policy.id,
                title_text="양산 청년 취업 지원",
                keyword_text="양산 청년 취업 일자리",
                summary_text="양산시 거주 청년 취업 지원",
                eligibility_text="19세~39세 양산시 거주 청년",
                support_text="취업 상담 지원",
                search_text="양산 청년 취업 일자리 지원",
                projection_version="1.1.0",
                updated_at=now,
            ),
        ]
    )
    db.commit()
    activate_all_policies()

    response = client.get(
        "/api/v1/policies/search?q=경상남도 양산시 청년 취업"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["policy"]["id"] == policy.id
    region = next(
        condition
        for condition in data["interpreted_conditions"]["conditions"]
        if condition["dimension"] == "region"
    )
    assert region["value"] == "경상남도 양산시"
    assert region["resolution"] == "resolved"
    assert "양산시" not in data["interpreted_conditions"][
        "uninterpreted_terms"
    ]


def test_search_api_empty_q_422(client):
    response = client.get("/api/v1/policies/search?q=   ")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_search_api_filler_only_q_400(client):
    response = client.get("/api/v1/policies/search?q=찾아줘 받을 수 있나?")

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["message"] == (
        "유효한 검색어 또는 구조화 조건이 제공되지 않았습니다."
    )


def test_search_api_explicit_region_unmapped_400(client):
    response = client.get("/api/v1/policies/search?q=청년지원&region=무지개시 이상구")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["details"]["field"] == "region"
    assert data["error"]["details"]["resolution"] == "unmapped"


def test_search_api_no_matching_results_200_ok(client, db):
    response = client.get("/api/v1/policies/search?q=존재하지않는특수키워드검색어12345")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_api_profile_preferences_rank_without_excluding(
    client,
    db,
    activate_all_policies,
):
    now = datetime.now(timezone.utc)
    housing = Policy(
        source_id="test_profile_rank",
        external_id="PROFILE-HOUSING",
        source_name="테스트",
        title="공통프로필검색 청년 지원",
        summary="공통프로필검색 대상 정책",
        categories=["housing"],
        application_status="open",
        coverage_scope="nationwide",
        data_quality_status="valid",
        source_url="https://example.com/profile-housing",
        collected_at=now,
    )
    finance = Policy(
        source_id="test_profile_rank",
        external_id="PROFILE-FINANCE",
        source_name="테스트",
        title="공통프로필검색 청년 지원",
        summary="공통프로필검색 대상 정책",
        categories=["finance"],
        application_status="open",
        coverage_scope="nationwide",
        data_quality_status="valid",
        source_url="https://example.com/profile-finance",
        collected_at=now,
    )
    db.add_all([housing, finance])
    db.flush()
    db.add_all(
        [
            PolicySearchDocument(
                policy_id=policy.id,
                title_text="공통프로필검색 청년 지원",
                keyword_text="공통프로필검색",
                summary_text="공통프로필검색 대상 정책",
                eligibility_text="",
                support_text="",
                search_text="공통프로필검색 청년 지원 대상 정책",
                projection_version="1.1.0",
                updated_at=now,
            )
            for policy in (housing, finance)
        ]
    )
    db.commit()
    activate_all_policies()

    response = client.post(
        "/api/v1/policies/search",
        json={
            "q": "공통프로필검색",
            "preferences": {"categories": ["finance"]},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [item["policy"]["id"] for item in data["items"]] == [
        finance.id,
        housing.id,
    ]
    assert "PROFILE_CATEGORY_MATCH" in data["items"][0]["reason_codes"]
    assert "PROFILE_CATEGORY_MATCH" not in data["items"][1]["reason_codes"]
