import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import create_db_engine
from app.models.policy import Policy, utc_now
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument
from app.services.policy_search_evaluation import (
    MatchState,
    PolicySearchEvaluationService,
    ProjectionField,
    RegionDecisionReason,
    RegionResolutionState,
)
from app.services.region_reference_importer import import_region_reference


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
REGIONS_PATH = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIASES_PATH = (
    ROOT / "data" / "seeds" / "administrative_region_aliases.json"
)
SCHEME = "kr-bjd-20260803"
CHUNGNAM = "4400000000"
CHEONAN = "4413000000"
ASAN = "4420000000"


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


def _policy(external_id: str, coverage_scope: str) -> Policy:
    return Policy(
        schema_version="1.1.0",
        source_id="psf6-postgresql",
        source_name="PSF6 PostgreSQL test",
        external_id=external_id,
        title=external_id,
        categories=[],
        keywords=[],
        life_stages=[],
        target_groups=[],
        regions=[],
        coverage_scope=coverage_scope,
        age_min=19,
        age_max=34,
        application_status="open",
        education_statuses=[],
        employment_statuses=[],
        required_conditions=[],
        preferred_conditions=[],
        excluded_conditions=[],
        source_url=f"https://fixture.invalid/{external_id}",
        collected_at=utc_now(),
        provenance=[],
        data_quality_status="valid",
    )


def _rule(policy_id: int, code: str, relation: str = "include"):
    return PolicyRegionRule(
        policy_id=policy_id,
        relation=relation,
        resolution_status="matched",
        region_scheme=SCHEME,
        region_code=code,
    )


def test_postgresql_policy_search_evaluation_primitives():
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
    db_engine = create_db_engine(database_url)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )

    try:
        command.upgrade(config, "head")
        with session_factory() as db:
            imported = import_region_reference(db, REGIONS_PATH, ALIASES_PATH)
        assert imported.inserted_regions == 538
        assert imported.inserted_aliases == 1080

        with session_factory() as db:
            policies = {
                "nationwide": _policy("PSF6-NATIONWIDE", "nationwide"),
                "unknown": _policy("PSF6-UNKNOWN", "unknown"),
                "exact": _policy("PSF6-EXACT", "regional"),
                "ancestor": _policy("PSF6-ANCESTOR", "regional"),
                "other": _policy("PSF6-OTHER", "regional"),
                "excluded": _policy("PSF6-EXCLUDED", "regional"),
            }
            db.add_all(policies.values())
            db.flush()
            db.add_all(
                [
                    _rule(policies["exact"].id, CHEONAN),
                    _rule(policies["ancestor"].id, CHUNGNAM),
                    _rule(policies["other"].id, ASAN),
                    _rule(policies["excluded"].id, CHUNGNAM),
                    _rule(policies["excluded"].id, CHEONAN, "exclude"),
                    PolicySearchDocument(
                        policy_id=policies["exact"].id,
                        title_text="청년 월세 지원",
                        keyword_text="주거 월세",
                        summary_text="",
                        eligibility_text="천안 거주 19세 이상",
                        support_text="월 20만원",
                        search_text=(
                            "청년 월세 지원 주거 월세 천안 거주 "
                            "19세 이상 월 20만원"
                        ),
                        projection_version="1.0.0",
                    ),
                ]
            )
            db.commit()

            service = PolicySearchEvaluationService(db)
            query = service.resolve_region_alias("천안")
            ambiguous = service.resolve_region_alias("중구")

            assert query.status is RegionResolutionState.MATCHED
            assert ambiguous.status is RegionResolutionState.AMBIGUOUS
            assert service.evaluate_policy_region(
                policies["exact"].id, query
            ).reason is RegionDecisionReason.EXACT
            assert service.evaluate_policy_region(
                policies["ancestor"].id, query
            ).reason is RegionDecisionReason.ANCESTOR
            assert service.evaluate_policy_region(
                policies["other"].id, query
            ).reason is RegionDecisionReason.OTHER_REGION
            assert service.evaluate_policy_region(
                policies["nationwide"].id, query
            ).reason is RegionDecisionReason.NATIONWIDE
            assert service.evaluate_policy_region(
                policies["unknown"].id, query
            ).reason is RegionDecisionReason.POLICY_UNKNOWN
            assert service.evaluate_policy_region(
                policies["excluded"].id, query
            ).reason is RegionDecisionReason.EXCLUDE
            assert service.evaluate_policy_age(
                policies["exact"].id, 27
            ).state is MatchState.MATCH
            assert service.evaluate_policy_application_status(
                policies["exact"].id, "open"
            ).state is MatchState.MATCH
            evidence = service.match_policy_projection(
                policies["exact"].id,
                ["청년월세", "천안"],
            )
            assert {item.field for item in evidence.fields} == {
                ProjectionField.TITLE,
                ProjectionField.ELIGIBILITY,
            }
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
