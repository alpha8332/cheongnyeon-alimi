from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.policy import Policy


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REVISION = "20260728_0001"


def alembic_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "alembic"),
    )
    config.attributes["database_url"] = (
        "postgresql://migration:masked@database:5432/policies"
    )
    return config


def render_upgrade_sql() -> str:
    config = alembic_config()
    output = StringIO()
    config.output_buffer = output
    command.upgrade(config, "head", sql=True)
    return output.getvalue()


def render_downgrade_sql() -> str:
    config = alembic_config()
    output = StringIO()
    config.output_buffer = output
    command.downgrade(config, f"{REVISION}:base", sql=True)
    return output.getvalue()


def test_initial_revision_is_the_single_alembic_head():
    scripts = ScriptDirectory.from_config(alembic_config())
    revision = scripts.get_current_head()

    assert revision == REVISION
    assert scripts.get_revision(revision).down_revision is None


def test_upgrade_sql_matches_postgresql_policy_contract():
    sql = render_upgrade_sql()

    assert "CREATE TABLE policies" in sql
    assert sql.count(" JSONB NOT NULL") == 8
    assert "TIMESTAMP WITH TIME ZONE" in sql
    assert "CREATE TYPE policy_application_schedule AS ENUM" in sql
    assert "CREATE TYPE policy_application_status AS ENUM" in sql
    assert "CREATE TYPE policy_data_quality_status AS ENUM" in sql
    assert "USING gin (categories)" in sql
    assert "USING gin (regions)" in sql
    assert "CONSTRAINT uq_policies_source_external UNIQUE" in sql
    assert "CONSTRAINT ck_policies_age_order CHECK" in sql
    assert "CONSTRAINT ck_policies_application_date_order CHECK" in sql

    for column in Policy.__table__.columns:
        assert f"\n    {column.name} " in sql


def test_downgrade_sql_removes_table_indexes_and_enum_types():
    sql = render_downgrade_sql()

    assert "DROP INDEX ix_policies_categories_gin" in sql
    assert "DROP INDEX ix_policies_regions_gin" in sql
    assert "DROP TABLE policies" in sql
    assert "DROP TYPE policy_data_quality_status" in sql
    assert "DROP TYPE policy_application_status" in sql
    assert "DROP TYPE policy_application_schedule" in sql
