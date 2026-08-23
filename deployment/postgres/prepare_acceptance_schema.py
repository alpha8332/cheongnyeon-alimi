from __future__ import annotations

import os
import re
import sys

import psycopg2
from psycopg2 import sql


ALLOWLIST_TABLES = (
    "administrative_region_aliases",
    "administrative_regions",
    "alembic_version",
    "collection_runs",
    "policies",
    "policy_region_rules",
    "policy_search_documents",
)
DATA_TABLES = tuple(
    table for table in ALLOWLIST_TABLES if table != "alembic_version"
)
REVISION_PATTERN = re.compile(r"^[0-9]{8}_[0-9]{4}$")


class SchemaPreparationError(RuntimeError):
    pass


def inspect_schema(connection, *, target_revision: str) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        )
        tables = tuple(row[0] for row in cursor.fetchall())
        if not tables:
            return "empty"
        if tables != ALLOWLIST_TABLES:
            raise SchemaPreparationError("public table allowlist mismatch")

        cursor.execute("SELECT version_num FROM alembic_version")
        revisions = tuple(row[0] for row in cursor.fetchall())
        if revisions != (target_revision,):
            raise SchemaPreparationError("Alembic revision mismatch")

        nonempty: dict[str, int] = {}
        for table in DATA_TABLES:
            cursor.execute(
                sql.SQL("SELECT count(*) FROM {}").format(
                    sql.Identifier("public", table)
                )
            )
            count = int(cursor.fetchone()[0])
            if count:
                nonempty[table] = count
        if nonempty:
            raise SchemaPreparationError(
                f"schema contains Acceptance data: {nonempty}"
            )
        return "ready"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    target_revision = os.environ.get("ACCEPTANCE_ALEMBIC_REVISION", "")
    if not database_url:
        print("DEP3_BLOCKED: DATABASE_URL is missing", file=sys.stderr)
        return 1
    if not REVISION_PATTERN.fullmatch(target_revision):
        print(
            "DEP3_BLOCKED: Acceptance Alembic revision is malformed",
            file=sys.stderr,
        )
        return 1
    try:
        connection = psycopg2.connect(
            database_url,
            connect_timeout=5,
            application_name="acceptance_schema_preparation_guard",
        )
        try:
            connection.set_session(readonly=True, autocommit=True)
            state = inspect_schema(
                connection,
                target_revision=target_revision,
            )
        finally:
            connection.close()
        print(f"DEP3_SCHEMA_STATE={state}")
        return 0
    except (SchemaPreparationError, psycopg2.Error) as error:
        print(f"DEP3_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

