from __future__ import annotations

import os
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
STABLE_IDENTITIES = (
    ("regional-daegu-youth-platform", "8357"),
    (
        "regional-gangwon-youth-platform",
        "A2026010600300200900600001",
    ),
    ("regional-gyeongnam-youth-platform", "2091"),
)
EXPECTED_ROW_COUNTS = {
    "administrative_region_aliases": 1080,
    "administrative_regions": 538,
    "collection_runs": 61,
    "policies": 3273,
    "policy_region_rules": 123884,
    "policy_search_documents": 3273,
}


class RestoredDatabaseError(RuntimeError):
    pass


def scalar(cursor, statement: str, parameters=()):
    cursor.execute(statement, parameters)
    row = cursor.fetchone()
    return None if row is None else row[0]


def verify(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        )
        tables = tuple(row[0] for row in cursor.fetchall())
        if tables != ALLOWLIST_TABLES:
            raise RestoredDatabaseError("public table allowlist mismatch")
        for table_name, expected_count in EXPECTED_ROW_COUNTS.items():
            cursor.execute(
                sql.SQL("SELECT count(*) FROM {}").format(
                    sql.Identifier("public", table_name)
                )
            )
            if int(cursor.fetchone()[0]) != expected_count:
                raise RestoredDatabaseError(
                    f"{table_name} baseline count mismatch"
                )
        if scalar(cursor, "SELECT version_num FROM alembic_version") != "20260810_0006":
            raise RestoredDatabaseError("snapshot Alembic revision mismatch")
        for source_id, external_id in STABLE_IDENTITIES:
            count = int(
                scalar(
                    cursor,
                    "SELECT count(*) FROM policies "
                    "WHERE source_id=%s AND external_id=%s",
                    (source_id, external_id),
                )
            )
            if count != 1:
                raise RestoredDatabaseError("stable identity baseline mismatch")

        orphan_queries = (
            "SELECT count(*) FROM administrative_region_aliases a "
            "LEFT JOIN administrative_regions r ON r.scheme=a.scheme "
            "AND r.code=a.region_code WHERE r.code IS NULL",
            "SELECT count(*) FROM policy_region_rules pr "
            "LEFT JOIN policies p ON p.id=pr.policy_id WHERE p.id IS NULL",
            "SELECT count(*) FROM policy_region_rules pr "
            "LEFT JOIN administrative_regions r ON r.scheme=pr.region_scheme "
            "AND r.code=pr.region_code WHERE pr.region_code IS NOT NULL "
            "AND r.code IS NULL",
            "SELECT count(*) FROM policy_search_documents ps "
            "LEFT JOIN policies p ON p.id=ps.policy_id WHERE p.id IS NULL",
        )
        if any(int(scalar(cursor, statement)) != 0 for statement in orphan_queries):
            raise RestoredDatabaseError("restored foreign-key orphan detected")


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DEP2_BLOCKED: DATABASE_URL is missing", file=sys.stderr)
        return 1
    try:
        connection = psycopg2.connect(
            database_url,
            connect_timeout=5,
            application_name="acceptance_pre_migrate_verifier",
        )
        try:
            connection.set_session(readonly=True, autocommit=True)
            verify(connection)
        finally:
            connection.close()
        print("DEP3_RESTORE_BASELINE_VERIFIED")
        return 0
    except (RestoredDatabaseError, psycopg2.Error) as error:
        print(f"DEP2_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
