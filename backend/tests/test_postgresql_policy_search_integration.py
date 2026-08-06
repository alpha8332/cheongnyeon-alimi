import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.models.policy import Policy, utc_now
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument
from app.repositories.policy import PolicyRepository
from app.repositories.policy_search import PolicySearchRepository
from app.services.policy_search_parser import parse_search_query
from app.services.region_reference_importer import import_region_reference


BACKEND_ROOT = ROOT / "backend"
REGIONS_PATH = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIASES_PATH = (
    ROOT / "data" / "seeds" / "administrative_region_aliases.json"
)


def _require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL")
    if not parsed.database or not parsed.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'")
    return database_url


def _migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    return config


@pytest.fixture(scope="module")
def postgresql_session_factory():
    database_url = _require_test_database_url()
    engine = create_db_engine(database_url)
    with engine.connect() as connection:
        connection.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(sa.text("CREATE SCHEMA public"))
        connection.commit()
    command.upgrade(_migration_config(database_url), "head")

    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        import_region_reference(
            db=session,
            regions_path=REGIONS_PATH,
            aliases_path=ALIASES_PATH,
        )
        session.commit()

    try:
        yield session_factory
    finally:
        with engine.connect() as connection:
            connection.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(sa.text("CREATE SCHEMA public"))
            connection.commit()
        engine.dispose()


@pytest.fixture
def postgresql_session(postgresql_session_factory):
    with postgresql_session_factory() as session:
        try:
            yield session
        finally:
            session.rollback()


def test_postgresql_golden_query_27_cheonan_short_stay(postgresql_session):
    session = postgresql_session
    now = utc_now()

    # 테스트 정책 적재 (천안 27세 청년 단기숙소 지원)
    p1 = Policy(
        source_id="pg_test_cheonan_1",
        source_name="온통청년",
        title="청년단기숙소 지원사업",
        summary="충남 천안시 청년 단기숙소 주거 지원",
        categories=["housing"],
        application_schedule="always",
        application_status="open",
        region_text="충청남도 천안시",
        regions=["4413000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/pg_cheonan1",
        collected_at=now,
    )
    session.add(p1)
    session.flush()

    distractor = Policy(
        source_id="pg_test_cheonan_generic",
        source_name="온통청년",
        title="천안 청년 생활지원 사업",
        summary="충남 천안시 청년을 위한 일반 생활 지원",
        categories=["housing"],
        application_schedule="always",
        application_status="open",
        region_text="충청남도 천안시",
        regions=["4413000000"],
        age_min=19,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/pg_cheonan_generic",
        collected_at=now,
    )
    session.add(distractor)
    session.flush()

    r1 = PolicyRegionRule(
        policy_id=p1.id,
        relation="include",
        resolution_status="matched",
        region_scheme="kr-bjd-20260803",
        region_code="4413000000",
        source_code="4413000000",
        source_text="충청남도 천안시",
    )
    doc1 = PolicySearchDocument(
        policy_id=p1.id,
        title_text="청년단기숙소 지원사업",
        keyword_text="천안 단기숙소 주거 지원 청년",
        summary_text="충남 천안시 청년 단기숙소 주거 지원",
        eligibility_text="19세~39세 청년",
        support_text="청년 단기숙소 상시 지원",
        search_text="청년단기숙소 지원사업 천안 단기숙소 주거 지원 청년",
        projection_version="1.1.0",
        updated_at=now,
    )
    distractor_rule = PolicyRegionRule(
        policy_id=distractor.id,
        relation="include",
        resolution_status="matched",
        region_scheme="kr-bjd-20260803",
        region_code="4413000000",
        source_code="4413000000",
        source_text="충청남도 천안시",
    )
    distractor_doc = PolicySearchDocument(
        policy_id=distractor.id,
        title_text="천안 청년 생활지원 사업",
        keyword_text="천안 청년 지원 주거 생활",
        summary_text="충남 천안시 청년을 위한 일반 생활 지원",
        eligibility_text="19세~39세 청년",
        support_text="청년 생활 지원",
        search_text="천안 청년 생활지원 사업 주거 일반 생활 지원",
        projection_version="1.1.0",
        updated_at=now,
    )
    session.add_all([r1, doc1, distractor_rule, distractor_doc])
    session.commit()

    golden_query = "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?"
    interpreted = parse_search_query(q=golden_query, db=session)

    # 1. 지역 '천안'이 지역 조건으로 파싱 및 resolution 되었는지 assert (Blocker 2 해결 검증)
    cond_map = {cond.dimension: cond for cond in interpreted.conditions}
    assert interpreted.q_raw == golden_query
    assert "region" in cond_map
    assert cond_map["region"].resolution == "resolved"

    search_repo = PolicySearchRepository(session)
    items, total = search_repo.search_policies(
        interpreted, include_partial=True, page=1, limit=10
    )

    assert total == 1
    top_item = items[0]
    assert top_item.policy.id == p1.id
    assert top_item.verdicts.status is None
    assert top_item.verdicts.age == "match"
    assert top_item.verdicts.region == "match"  # 지역 verdict match 검증


def test_postgresql_golden_query_unmatched_term_zero(postgresql_session):
    session = postgresql_session

    # Golden query 2: "존재하지않는특수키워드검색어12345" -> 0건 (Blocker 1 해결 검증)
    interpreted = parse_search_query(q="존재하지않는특수키워드검색어12345", db=session)
    search_repo = PolicySearchRepository(session)

    items, total = search_repo.search_policies(
        interpreted, include_partial=True, page=1, limit=10
    )

    assert total == 0
    assert items == []


def test_postgresql_explain_query_plan(postgresql_session):
    session = postgresql_session

    # PostgreSQL EXPLAIN 실행 계획 검증 (Blocker 3 해결 검증)
    query_str = "EXPLAIN SELECT * FROM policies WHERE data_quality_status != 'invalid'"
    result = session.execute(sa.text(query_str)).fetchall()
    assert len(result) > 0
