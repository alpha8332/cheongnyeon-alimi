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
    config.set_main_option("sqlalchemy.url", database_url)
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
        engine.dispose()


@pytest.fixture
def postgresql_session(postgresql_session_factory):
    with postgresql_session_factory() as session:
        try:
            yield session
        finally:
            session.rollback()


def test_postgresql_policy_search_end_to_end(postgresql_session):
    session = postgresql_session
    now = utc_now()

    # 테스트 정책 적재
    p1 = Policy(
        source_id="pg_test_1",
        source_name="온통청년",
        title="천안 청년 일자리 대출 지원",
        summary="충남 천안시 청년 취업 및 일자리 지원",
        categories=["employment", "finance"],
        application_status="open",
        region_text="충청남도 천안시",
        regions=["4413000000"],
        age_min=18,
        age_max=39,
        coverage_scope="regional",
        data_quality_status="valid",
        source_url="https://example.com/pg1",
        collected_at=now,
    )
    session.add(p1)
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
        title_text="천안 청년 일자리 대출 지원",
        keyword_text="천안 일자리 취업 대출 청년",
        summary_text="충남 천안시 청년 취업 및 일자리 지원",
        eligibility_text="18세~39세 청년",
        support_text="취업 수당 및 대출 이자 지원",
        search_text="천안 청년 일자리 대출 지원 천안 일자리 취업 대출 청년",
        projection_version="1.1.0",
        updated_at=now,
    )
    session.add_all([r1, doc1])
    session.commit()

    # 1. 자연어 검색 파싱 및 PostgreSQL Repository 조회
    interpreted = parse_search_query(q="천안 25세 일자리 모집중", db=session)
    search_repo = PolicySearchRepository(session)

    items, total = search_repo.search_policies(
        interpreted, include_partial=True, page=1, limit=10
    )

    assert total >= 1
    top_item = items[0]
    assert top_item.policy.id == p1.id
    assert top_item.verdicts.status == "match"
    assert top_item.verdicts.age == "match"

    # 2. 기존 목록 API 호환성 회귀 검증 (PolicyRepository.get_by_id)
    policy_repo = PolicyRepository(session)
    fetched = policy_repo.get_by_id(p1.id)
    assert fetched is not None
    assert fetched.title == "천안 청년 일자리 대출 지원"
