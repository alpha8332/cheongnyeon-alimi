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

    assert "keyword" in dim_map
    assert dim_map["keyword"].value == "월세"
    assert dim_map["keyword"].source == "q"

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


def test_parse_search_query_cheonan_short_stay_anchor(db):
    from app.models.administrative_region import AdministrativeRegion, AdministrativeRegionAlias
    reg = AdministrativeRegion(
        scheme="kr-bjd-20260803",
        code="4413000000",
        name="천안시",
        full_name="충청남도 천안시",
        level="district",
        status="active",
    )
    alias = AdministrativeRegionAlias(
        scheme="kr-bjd-20260803",
        region_code="4413000000",
        alias="천안",
        kind="curated",
    )
    db.add_all([reg, alias])
    db.commit()

    query = "   천안 사는 27살 청년 단기숙소 지원 받을 수 있나?   "
    res = parse_search_query(q=query, db=db)

    # q_raw 보존 검증 (공백 포함 원문 유지)
    assert res.q_raw == query
    assert res.q_clean == "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?"

    dim_map = {cond.dimension: cond for cond in res.conditions}
    assert "region" in dim_map
    assert dim_map["region"].source == "q"
    assert dim_map["region"].resolution == "resolved"
    assert "충청남도 천안시" in dim_map["region"].candidates
    assert dim_map["age"].value == 27
    assert dim_map["category"].value == "housing"
    assert dim_map["keyword"].value == "단기숙소"
    assert res.uninterpreted_terms == ["청년", "지원"]


def test_parse_search_query_resolves_suffixless_yangsan(db):
    from app.models.administrative_region import (
        AdministrativeRegion,
        AdministrativeRegionAlias,
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
    db.add_all(
        [
            gyeongnam,
            yangsan,
            AdministrativeRegionAlias(
                scheme="kr-bjd-20260803",
                region_code=yangsan.code,
                alias="양산시",
                kind="official_short",
            ),
        ]
    )
    db.commit()

    inferred = parse_search_query(q="양산 청년 취업", db=db)
    compound = parse_search_query(q="경상남도 양산시 청년 취업", db=db)
    explicit = parse_search_query(q="청년 취업", region="양산", db=db)

    inferred_region = next(
        condition
        for condition in inferred.conditions
        if condition.dimension == "region"
    )
    explicit_region = next(
        condition
        for condition in explicit.conditions
        if condition.dimension == "region"
    )
    compound_region = next(
        condition
        for condition in compound.conditions
        if condition.dimension == "region"
    )
    assert inferred_region.value == "경상남도 양산시"
    assert inferred_region.resolution == "resolved"
    assert "양산" not in inferred.uninterpreted_terms
    assert compound_region.value == "경상남도 양산시"
    assert compound_region.resolution == "resolved"
    assert "경상남도" not in compound.uninterpreted_terms
    assert "양산시" not in compound.uninterpreted_terms
    assert explicit_region.candidates == ["경상남도 양산시"]
    assert explicit_region.resolution == "resolved"


def test_parse_search_query_marks_duplicate_suffixless_county_ambiguous(db):
    from app.models.administrative_region import AdministrativeRegion

    db.add_all(
        [
            AdministrativeRegion(
                scheme="kr-bjd-20260803",
                code="4282000000",
                name="고성군",
                full_name="강원특별자치도 고성군",
                level="district",
                status="active",
            ),
            AdministrativeRegion(
                scheme="kr-bjd-20260803",
                code="4882000000",
                name="고성군",
                full_name="경상남도 고성군",
                level="district",
                status="active",
            ),
        ]
    )
    db.commit()

    result = parse_search_query(q="고성 청년 정책", db=db)
    region = next(
        condition
        for condition in result.conditions
        if condition.dimension == "region"
    )

    assert region.resolution == "ambiguous"
    assert region.candidates == [
        "강원특별자치도 고성군",
        "경상남도 고성군",
    ]
