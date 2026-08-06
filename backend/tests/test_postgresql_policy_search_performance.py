import json
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.core.database import create_db_engine


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PRE_SEARCH_REVISION = "20260730_0003"
SYNTHETIC_POLICY_COUNT = 20_000
EXPECTED_MATCH_COUNT = SYNTHETIC_POLICY_COUNT // 100
SEARCH_INDEX = "ix_policy_search_documents_search_text_trgm"


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


def _plan_nodes(plan: dict) -> tuple[dict, ...]:
    children = tuple(
        node
        for child in plan.get("Plans", ())
        for node in _plan_nodes(child)
    )
    return (plan, *children)


def test_postgresql_reports_default_and_index_projection_search_plans():
    database_url = _require_test_database_url()
    config = _migration_config(database_url)
    db_engine = create_db_engine(database_url)

    try:
        command.upgrade(config, PRE_SEARCH_REVISION)
        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO policies (
                        source_id,
                        source_name,
                        external_id,
                        title,
                        categories,
                        regions,
                        education_statuses,
                        employment_statuses,
                        required_conditions,
                        preferred_conditions,
                        excluded_conditions,
                        source_url,
                        collected_at,
                        provenance,
                        data_quality_status
                    )
                    SELECT
                        'psf7-benchmark',
                        'PSF7 benchmark',
                        'PSF7-' || value,
                        '합성 정책 ' || value,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        '[]'::jsonb,
                        'https://fixture.invalid/' || value,
                        '2026-08-03T00:00:00+00:00'::timestamptz,
                        '[]'::jsonb,
                        'valid'
                    FROM generate_series(1, :policy_count) AS value
                    """
                ),
                {"policy_count": SYNTHETIC_POLICY_COUNT},
            )

        command.upgrade(config, "head")
        with db_engine.begin() as connection:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO policy_search_documents (
                        policy_id,
                        title_text,
                        keyword_text,
                        summary_text,
                        eligibility_text,
                        support_text,
                        search_text,
                        projection_version
                    )
                    SELECT
                        id,
                        title,
                        CASE
                            WHEN id % 100 = 0 THEN '청년 월세 주거'
                            ELSE '일반 지원'
                        END,
                        '',
                        '',
                        '',
                        CASE
                            WHEN id % 100 = 0
                                THEN title || ' 청년 월세 주거'
                            ELSE title || ' 일반 지원'
                        END,
                        '1.0.0'
                    FROM policies
                    """
                )
            )
            connection.execute(
                sa.text("ANALYZE policy_search_documents")
            )
            default_raw_plan = connection.execute(
                sa.text(
                    """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    SELECT policy_id
                    FROM policy_search_documents
                    WHERE search_text ILIKE '%청년 월세%'
                    """
                )
            ).scalar_one()
            like_raw_plan = connection.execute(
                sa.text(
                    """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    SELECT policy_id
                    FROM policy_search_documents
                    WHERE search_text LIKE '%청년 월세%'
                    """
                )
            ).scalar_one()
            connection.execute(sa.text("SET LOCAL enable_seqscan = off"))
            index_raw_plan = connection.execute(
                sa.text(
                    """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    SELECT policy_id
                    FROM policy_search_documents
                    WHERE search_text ILIKE '%청년 월세%'
                    """
                )
            ).scalar_one()

        default_report = (
            json.loads(default_raw_plan)
            if isinstance(default_raw_plan, str)
            else default_raw_plan
        )
        index_report = (
            json.loads(index_raw_plan)
            if isinstance(index_raw_plan, str)
            else index_raw_plan
        )
        like_report = (
            json.loads(like_raw_plan)
            if isinstance(like_raw_plan, str)
            else like_raw_plan
        )
        default_summary = default_report[0]
        like_summary = like_report[0]
        index_summary = index_report[0]
        default_nodes = _plan_nodes(default_summary["Plan"])
        like_nodes = _plan_nodes(like_summary["Plan"])
        index_nodes = _plan_nodes(index_summary["Plan"])
        indexes = {
            node.get("Index Name")
            for node in index_nodes
            if node.get("Index Name") is not None
        }
        default_rows = default_summary["Plan"]["Actual Rows"]
        like_rows = like_summary["Plan"]["Actual Rows"]
        index_rows = index_summary["Plan"]["Actual Rows"]

        print(
            "PSF7 default search plan: "
            f"policies={SYNTHETIC_POLICY_COUNT} "
            f"matches={default_rows} "
            f"estimated={default_summary['Plan']['Plan Rows']} "
            f"planning_ms={default_summary['Planning Time']:.3f} "
            f"execution_ms={default_summary['Execution Time']:.3f} "
            "nodes="
            f"{','.join(node['Node Type'] for node in default_nodes)}"
        )
        print(
            "PSF7 LIKE search plan: "
            f"matches={like_rows} "
            f"estimated={like_summary['Plan']['Plan Rows']} "
            f"planning_ms={like_summary['Planning Time']:.3f} "
            f"execution_ms={like_summary['Execution Time']:.3f} "
            f"nodes={','.join(node['Node Type'] for node in like_nodes)}"
        )
        print(
            "PSF7 index search plan: "
            f"matches={index_rows} "
            f"estimated={index_summary['Plan']['Plan Rows']} "
            f"planning_ms={index_summary['Planning Time']:.3f} "
            f"execution_ms={index_summary['Execution Time']:.3f} "
            f"nodes={','.join(node['Node Type'] for node in index_nodes)}"
        )
        assert default_rows == EXPECTED_MATCH_COUNT
        assert like_rows == EXPECTED_MATCH_COUNT
        assert index_rows == EXPECTED_MATCH_COUNT
        assert SEARCH_INDEX in indexes
    finally:
        try:
            command.downgrade(config, "base")
            assert not sa.inspect(db_engine).has_table("policies")
        finally:
            db_engine.dispose()
