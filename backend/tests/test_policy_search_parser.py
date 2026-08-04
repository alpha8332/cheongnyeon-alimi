import pytest
from app.services.policy_search_parser import parse_search_query


def test_parse_search_query_basic():
    query = "서울 24세 청년 월세 지원금 모집중"
    res = parse_search_query(q=query)

    assert res.q_raw == query
    assert res.q_clean == "서울 24세 청년 월세 지원금 모집중"
    assert res.override_fields == []

    # conditions 검증
    dim_map = {cond.dimension: cond for cond in res.conditions}
    assert "region" in dim_map
    assert dim_map["region"].value == "서울특별시"
    assert dim_map["region"].source == "q"
    assert dim_map["region"].resolution == "resolved"

    assert "age" in dim_map
    assert dim_map["age"].value == 24
    assert dim_map["age"].source == "q"
    assert dim_map["age"].resolution == "resolved"

    assert "category" in dim_map
    assert dim_map["category"].value == "housing"
    assert dim_map["category"].source == "q"

    assert "status" in dim_map
    assert dim_map["status"].value == "open"
    assert dim_map["status"].source == "q"

    # uninterpreted_terms 검증 ("청년", "지원금" 등이 남아야 함)
    assert "청년" in res.uninterpreted_terms
    assert "지원금" in res.uninterpreted_terms


def test_parse_search_query_explicit_override():
    query = "서울 24세 월세 모집중"
    res = parse_search_query(
        q=query,
        age=30,
        region="경기도",
        status="closed",
        category="finance",
        keyword="특화지원",
    )

    # override_fields 검증
    assert "age" in res.override_fields
    assert "region" in res.override_fields
    assert "status" in res.override_fields
    assert "category" in res.override_fields

    dim_map = {cond.dimension: cond for cond in res.conditions}
    assert dim_map["age"].value == 30
    assert dim_map["age"].source == "explicit"

    assert dim_map["region"].value == "경기도"
    assert dim_map["region"].source == "explicit"
    assert dim_map["region"].resolution == "resolved"

    assert dim_map["status"].value == "closed"
    assert dim_map["status"].source == "explicit"

    assert dim_map["category"].value == "finance"
    assert dim_map["category"].source == "explicit"

    assert dim_map["keyword"].value == "특화지원"
    assert dim_map["keyword"].source == "explicit"


def test_parse_search_query_ambiguous_region():
    query = "중구 청년 대출"
    res = parse_search_query(q=query)

    dim_map = {cond.dimension: cond for cond in res.conditions}
    assert "region" in dim_map
    assert dim_map["region"].resolution == "ambiguous"
    assert len(dim_map["region"].candidates) > 1
    assert "서울특별시 중구" in dim_map["region"].candidates

    assert "category" in dim_map
    assert dim_map["category"].value == "finance"


def test_parse_search_query_unmapped_explicit_region():
    query = "청년 취업 지원"
    res = parse_search_query(q=query, region="무지개시 이상구")

    dim_map = {cond.dimension: cond for cond in res.conditions}
    assert "region" in dim_map
    assert dim_map["region"].value == "무지개시 이상구"
    assert dim_map["region"].source == "explicit"
    assert dim_map["region"].resolution == "unmapped"
    assert dim_map["region"].candidates == []
