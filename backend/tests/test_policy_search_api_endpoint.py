from datetime import datetime, timezone
import pytest
from app.models.administrative_region import AdministrativeRegion, AdministrativeRegionAlias
from app.models.policy import Policy
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument


def test_search_api_basic_200_ok(client, db):
    now = datetime.now(timezone.utc)
    # DB 테스트 데이터 준비
    p = Policy(
        source_id="test_search_1",
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


def test_search_api_empty_q_422(client):
    response = client.get("/api/v1/policies/search?q=   ")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


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
