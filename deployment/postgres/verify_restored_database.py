from __future__ import annotations

import os
import sys

import psycopg2


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
        if int(scalar(cursor, "SELECT count(*) FROM policies")) != 3273:
            raise RestoredDatabaseError("Policy baseline count mismatch")
        if int(scalar(cursor, "SELECT count(*) FROM collection_runs")) != 61:
            raise RestoredDatabaseError("CollectionRun baseline count mismatch")
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
        print("DEP2_RESTORE_BASELINE_VERIFIED")
        return 0
    except (RestoredDatabaseError, psycopg2.Error) as error:
        print(f"DEP2_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

