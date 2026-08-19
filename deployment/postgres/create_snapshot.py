from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit

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
FORBIDDEN_COLUMN_NAMES = {
    "access_token",
    "api_key",
    "audit_payload",
    "log_message",
    "password",
    "password_hash",
    "pin",
    "raw_payload",
    "refresh_token",
    "secret",
    "session_id",
}
HIGH_RISK_QUERY_KEYS = {
    "apikey",
    "api_key",
    "api-key",
    "servicekey",
    "service_key",
    "service-key",
    "auth",
    "password",
    "secret",
}
STABLE_IDENTITIES = (
    ("regional-daegu-youth-platform", "8357"),
    (
        "regional-gangwon-youth-platform",
        "A2026010600300200900600001",
    ),
    ("regional-gyeongnam-youth-platform", "2091"),
)
EXPECTED_ADMISSION_CONTRACT_HASH = (
    "789f8e3b61c144843e93bc762d60f114179c6bfb8e5effd260138c73484e1203"
)
EXPECTED_ADMISSION_FILE_HASH = (
    "03b6d91952e53148e709d2a66838faaf26f63432a49050d48f7b2ab40186ebda"
)
LOCAL_PATH_PATTERN = r"([A-Za-z]:\\|/Users/|/home/)"
COLLECTION_ERROR_SENSITIVE_PATTERN = (
    r"(password|token|secret|api[_-]?key|[A-Za-z]:\\|/Users/|/home/)"
)


class SnapshotError(RuntimeError):
    pass


@dataclass(frozen=True)
class PgpassEntry:
    host: str
    port: str
    database: str
    user: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_manifest_hash(value: dict[str, Any]) -> str:
    selected = dict(value)
    selected.pop("manifest_sha256", None)
    payload = json.dumps(
        selected,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def split_pgpass_line(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    escaped = False
    for character in line.rstrip("\r\n"):
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(character)
    if escaped:
        current.append("\\")
    fields.append("".join(current))
    return fields


def resolve_pgpass_entry(
    path: Path,
    *,
    host: str,
    port: int,
    database: str,
) -> PgpassEntry:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        fields = split_pgpass_line(line)
        if len(fields) != 5:
            continue
        entry_host, entry_port, entry_database, entry_user, _ = fields
        accepted_hosts = {host, "*"}
        if host in {"localhost", "127.0.0.1"}:
            accepted_hosts.update({"localhost", "127.0.0.1"})
        host_matches = entry_host in accepted_hosts
        if (
            host_matches
            and entry_port in {str(port), "*"}
            and entry_database in {database, "*"}
            and entry_user
        ):
            return PgpassEntry(
                host=entry_host,
                port=entry_port,
                database=entry_database,
                user=entry_user,
            )
    raise SnapshotError("pgpass has no entry for the requested database")


def extract_secret_candidates(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    text = path.read_text(encoding="utf-8")
    candidates: set[str] = set()
    for value in re.findall(r"[A-Za-z0-9%+/_=-]{16,}", text):
        candidates.add(value)
        candidates.add(unquote(value))
        if "=" in value:
            candidates.add(unquote(value.split("=", 1)[1]))
    return tuple(sorted(value for value in candidates if len(value) >= 16))


def classify_source_urls(
    rows: Iterable[tuple[str, str, str]],
    *,
    secret_candidates: tuple[str, ...],
) -> dict[str, int]:
    high_risk_count = 0
    public_navigation_token_count = 0
    unsafe_token_count = 0
    for _, _, source_url in rows:
        parsed = urlsplit(source_url)
        official_government_host = (
            parsed.hostname is not None and parsed.hostname.endswith(".go.kr")
        )
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            lowered_key = key.lower()
            if lowered_key in HIGH_RISK_QUERY_KEYS:
                high_risk_count += 1
                continue
            if lowered_key != "token":
                continue
            matches_secret = any(
                value == candidate or value in candidate
                for candidate in secret_candidates
            )
            is_public_navigation_token = (
                official_government_host
                and value.isdigit()
                and 1 <= len(value) <= 32
                and not matches_secret
            )
            if is_public_navigation_token:
                public_navigation_token_count += 1
            else:
                unsafe_token_count += 1
    return {
        "source_url_high_risk_query_count": high_risk_count,
        "source_url_public_navigation_token_count": (
            public_navigation_token_count
        ),
        "source_url_unsafe_token_count": unsafe_token_count,
    }


def _scalar(cursor, query: str, parameters: tuple[Any, ...] = ()) -> Any:
    cursor.execute(query, parameters)
    row = cursor.fetchone()
    return None if row is None else row[0]


def _grouped_counts(cursor, column: str) -> dict[str, int]:
    statement = sql.SQL(
        "SELECT coalesce({column}::text, 'null'), count(*) "
        "FROM policies GROUP BY {column} ORDER BY 1"
    ).format(column=sql.Identifier(column))
    cursor.execute(statement)
    return {str(key): int(count) for key, count in cursor.fetchall()}


def inspect_database(
    connection,
    *,
    secret_candidates: tuple[str, ...],
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        )
        tables = tuple(row[0] for row in cursor.fetchall())
        if tables != ALLOWLIST_TABLES:
            missing = sorted(set(ALLOWLIST_TABLES) - set(tables))
            unexpected = sorted(set(tables) - set(ALLOWLIST_TABLES))
            raise SnapshotError(
                f"public table inventory mismatch; missing={missing}, "
                f"unexpected={unexpected}"
            )

        cursor.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema='public' ORDER BY table_name, ordinal_position"
        )
        columns: dict[str, list[str]] = {table: [] for table in tables}
        forbidden_columns: list[str] = []
        for table_name, column_name in cursor.fetchall():
            columns[table_name].append(column_name)
            if column_name.lower() in FORBIDDEN_COLUMN_NAMES:
                forbidden_columns.append(f"{table_name}.{column_name}")
        if forbidden_columns:
            raise SnapshotError(
                "forbidden columns found in allowlist tables: "
                + ", ".join(forbidden_columns)
            )

        row_counts: dict[str, int] = {}
        for table_name in tables:
            cursor.execute(
                sql.SQL("SELECT count(*) FROM {}").format(
                    sql.Identifier("public", table_name)
                )
            )
            row_counts[table_name] = int(cursor.fetchone()[0])

        cursor.execute(
            "SELECT source_id, external_id, source_url FROM policies "
            "ORDER BY source_id, external_id"
        )
        url_scan = classify_source_urls(
            cursor.fetchall(),
            secret_candidates=secret_candidates,
        )

        known_secret_match_count = 0
        for candidate in secret_candidates:
            for table_name in tables:
                cursor.execute(
                    sql.SQL(
                        "SELECT count(*) FROM {} AS candidate_row "
                        "WHERE POSITION(%s IN to_jsonb(candidate_row)::text) > 0"
                    ).format(sql.Identifier("public", table_name)),
                    (candidate,),
                )
                known_secret_match_count += int(cursor.fetchone()[0])

        contact_count = int(
            _scalar(
                cursor,
                "SELECT count(*) FROM policies p CROSS JOIN LATERAL "
                "jsonb_array_elements("
                "p.eligibility_summary::jsonb->'institutional_contacts'"
                ") contact",
            )
        )
        bad_contact_kind_count = int(
            _scalar(
                cursor,
                "SELECT count(*) FROM policies p CROSS JOIN LATERAL "
                "jsonb_array_elements("
                "p.eligibility_summary::jsonb->'institutional_contacts'"
                ") contact WHERE coalesce(contact->>'kind','') "
                "NOT IN ('phone','official_channel')",
            )
        )
        email_contact_count = int(
            _scalar(
                cursor,
                "SELECT count(*) FROM policies p CROSS JOIN LATERAL "
                "jsonb_array_elements("
                "p.eligibility_summary::jsonb->'institutional_contacts'"
                ") contact WHERE coalesce(contact->>'value','') LIKE '%%@%%'",
            )
        )
        local_path_count = int(
            _scalar(
                cursor,
                "SELECT count(*) FROM policies "
                "WHERE provenance::text ~* %s",
                (LOCAL_PATH_PATTERN,),
            )
        )
        collection_error_sensitive_count = int(
            _scalar(
                cursor,
                "SELECT count(*) FROM collection_runs "
                "WHERE coalesce(error_type,'') ~* %s",
                (COLLECTION_ERROR_SENSITIVE_PATTERN,),
            )
        )

        scan = {
            "forbidden_column_count": len(forbidden_columns),
            "known_secret_candidate_count": len(secret_candidates),
            "known_secret_match_count": known_secret_match_count,
            "institutional_contact_count": contact_count,
            "disallowed_contact_kind_count": bad_contact_kind_count,
            "email_contact_count": email_contact_count,
            "local_path_provenance_count": local_path_count,
            "collection_error_sensitive_count": (
                collection_error_sensitive_count
            ),
            **url_scan,
        }
        blocking_scan_keys = (
            "forbidden_column_count",
            "known_secret_match_count",
            "disallowed_contact_kind_count",
            "email_contact_count",
            "local_path_provenance_count",
            "collection_error_sensitive_count",
            "source_url_high_risk_query_count",
            "source_url_unsafe_token_count",
        )
        blockers = {
            key: scan[key]
            for key in blocking_scan_keys
            if int(scan[key]) != 0
        }
        if blockers:
            raise SnapshotError(f"sensitive data scan failed: {blockers}")

        stable_identity_counts: dict[str, int] = {}
        for source_id, external_id in STABLE_IDENTITIES:
            count = int(
                _scalar(
                    cursor,
                    "SELECT count(*) FROM policies "
                    "WHERE source_id=%s AND external_id=%s",
                    (source_id, external_id),
                )
            )
            stable_identity_counts[f"{source_id}/{external_id}"] = count
        if any(count != 1 for count in stable_identity_counts.values()):
            raise SnapshotError(
                f"stable identity mismatch: {stable_identity_counts}"
            )

        cursor.execute(
            "SELECT source_id, count(*) FROM policies "
            "GROUP BY source_id ORDER BY source_id"
        )
        source_counts = {
            str(source_id): int(count)
            for source_id, count in cursor.fetchall()
        }

        return {
            "postgresql_version": str(
                _scalar(cursor, "SELECT current_setting('server_version')")
            ),
            "postgresql_version_num": str(
                _scalar(
                    cursor,
                    "SELECT current_setting('server_version_num')",
                )
            ),
            "alembic_revision": str(
                _scalar(cursor, "SELECT version_num FROM alembic_version")
            ),
            "tables": list(tables),
            "columns": columns,
            "row_counts": row_counts,
            "quality_counts": _grouped_counts(
                cursor, "data_quality_status"
            ),
            "application_status_counts": _grouped_counts(
                cursor, "application_status"
            ),
            "source_counts": source_counts,
            "stable_identity_counts": stable_identity_counts,
            "sensitive_data_scan": scan,
        }


def verify_admission_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    contract_hash = canonical_manifest_hash(value)
    file_hash = sha256_file(path)
    if contract_hash != EXPECTED_ADMISSION_CONTRACT_HASH:
        raise SnapshotError("admission manifest contract hash mismatch")
    if value.get("manifest_sha256") != EXPECTED_ADMISSION_CONTRACT_HASH:
        raise SnapshotError("admission manifest embedded hash mismatch")
    if file_hash != EXPECTED_ADMISSION_FILE_HASH:
        raise SnapshotError("admission manifest file hash mismatch")
    return {
        "rule_version": value.get("rule_version"),
        "taxonomy_version": value.get("taxonomy_version"),
        "git_sha": value.get("git_sha"),
        "contract_sha256": contract_hash,
        "file_sha256": file_hash,
    }


def repository_state(repository_root: Path) -> dict[str, str]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise SnapshotError(
            "repository worktree must be clean before snapshot creation"
        )
    return {"git_sha": head}


def resolve_executable(explicit: Path | None, name: str) -> Path:
    if explicit is not None:
        resolved = explicit.resolve()
        if not resolved.is_file():
            raise SnapshotError(f"{name} executable does not exist")
        return resolved
    discovered = shutil.which(name)
    if not discovered:
        raise SnapshotError(f"{name} executable was not found")
    return Path(discovered).resolve()


def create_dump(
    *,
    target: Path,
    pg_dump: Path,
    pg_restore: Path,
    pgpass_file: Path,
    host: str,
    port: int,
    database: str,
    user: str,
) -> dict[str, Any]:
    if target.exists():
        raise SnapshotError("snapshot dump already exists; refusing overwrite")
    partial = target.with_suffix(target.suffix + ".partial")
    if partial.exists():
        raise SnapshotError("partial snapshot dump already exists")
    environment = dict(os.environ)
    environment["PGPASSFILE"] = str(pgpass_file)
    command = [
        str(pg_dump),
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--host",
        host,
        "--port",
        str(port),
        "--username",
        user,
        "--dbname",
        database,
        "--file",
        str(partial),
    ]
    for table_name in ALLOWLIST_TABLES:
        command.extend(("--table", f"public.{table_name}"))
    try:
        subprocess.run(
            command,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        toc = subprocess.run(
            [str(pg_restore), "--list", str(partial)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        missing_tables = [
            table_name
            for table_name in ALLOWLIST_TABLES
            if table_name not in toc
        ]
        acl_entry_count = sum(
            1 for line in toc.splitlines() if " ACL " in line
        )
        if missing_tables or acl_entry_count:
            raise SnapshotError(
                f"dump TOC validation failed; missing={missing_tables}, "
                f"acl_entries={acl_entry_count}"
            )
        schema_sql = subprocess.run(
            [
                str(pg_restore),
                "--schema-only",
                "--no-owner",
                "--no-acl",
                "--file=-",
                str(partial),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        forbidden_schema_statements = sum(
            schema_sql.upper().count(value)
            for value in ("OWNER TO", "GRANT ", "REVOKE ")
        )
        if forbidden_schema_statements:
            raise SnapshotError(
                "owner or ACL statements remain in sanitized schema output"
            )
        partial.replace(target)
        version = subprocess.run(
            [str(pg_dump), "--version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return {
            "filename": target.name,
            "format": "custom",
            "bytes": target.stat().st_size,
            "sha256": sha256_file(target),
            "pg_dump_version": version,
            "toc_acl_entry_count": acl_entry_count,
            "schema_owner_acl_statement_count": forbidden_schema_statements,
        }
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def write_manifest(path: Path, manifest: dict[str, Any]) -> str:
    if path.exists():
        raise SnapshotError("snapshot manifest already exists; refusing overwrite")
    manifest["manifest_sha256"] = canonical_manifest_hash(manifest)
    serialized = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    path.write_text(serialized, encoding="utf-8", newline="\n")
    return sha256_file(path)


def ensure_outside_workspace(path: Path, repository_root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError:
        return resolved
    raise SnapshotError("secret and snapshot paths must be outside workspace")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a fail-closed post-admission Acceptance snapshot."
    )
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--pgpass-file", type=Path, required=True)
    parser.add_argument("--admission-manifest", type=Path, required=True)
    parser.add_argument("--runtime-archive", type=Path, required=True)
    parser.add_argument("--known-secret-file", type=Path)
    parser.add_argument("--pg-dump", type=Path)
    parser.add_argument("--pg-restore", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--database", default="cheongnyeon_alimi")
    parser.add_argument("--expected-policy-count", type=int, default=3273)
    parser.add_argument("--expected-collection-run-count", type=int, default=61)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    try:
        snapshot_dir = ensure_outside_workspace(
            args.snapshot_dir, repository_root
        )
        pgpass_file = ensure_outside_workspace(
            args.pgpass_file, repository_root
        )
        runtime_archive = ensure_outside_workspace(
            args.runtime_archive, repository_root
        )
        if args.known_secret_file is not None:
            known_secret_file = ensure_outside_workspace(
                args.known_secret_file, repository_root
            )
        else:
            known_secret_file = None
        for required_path in (
            pgpass_file,
            args.admission_manifest.resolve(),
            runtime_archive,
        ):
            if not required_path.is_file():
                raise SnapshotError(f"required input is missing: {required_path}")
        if known_secret_file is not None and not known_secret_file.is_file():
            raise SnapshotError("known secret file does not exist")

        repository = repository_state(repository_root)
        pgpass_entry = resolve_pgpass_entry(
            pgpass_file,
            host=args.host,
            port=args.port,
            database=args.database,
        )
        previous_pgpass = os.environ.get("PGPASSFILE")
        os.environ["PGPASSFILE"] = str(pgpass_file)
        try:
            connection = psycopg2.connect(
                host=args.host,
                port=args.port,
                dbname=args.database,
                user=pgpass_entry.user,
                connect_timeout=5,
                application_name="acceptance_snapshot_read_only",
            )
            connection.set_session(readonly=True, autocommit=True)
            try:
                database = inspect_database(
                    connection,
                    secret_candidates=extract_secret_candidates(
                        known_secret_file
                    ),
                )
            finally:
                connection.close()
        finally:
            if previous_pgpass is None:
                os.environ.pop("PGPASSFILE", None)
            else:
                os.environ["PGPASSFILE"] = previous_pgpass

        if database["row_counts"]["policies"] != args.expected_policy_count:
            raise SnapshotError("Policy count does not match RA4 baseline")
        if (
            database["row_counts"]["collection_runs"]
            != args.expected_collection_run_count
        ):
            raise SnapshotError("CollectionRun count does not match RA4 baseline")
        if database["alembic_revision"] != "20260810_0006":
            raise SnapshotError("Alembic revision does not match RA4 baseline")

        snapshot_dir.mkdir(parents=True, exist_ok=True)
        dump_path = snapshot_dir / "acceptance-post-admission.dump"
        manifest_path = snapshot_dir / "acceptance-snapshot.manifest.json"
        if manifest_path.exists():
            raise SnapshotError("snapshot manifest already exists")

        pg_dump = resolve_executable(args.pg_dump, "pg_dump")
        pg_restore = resolve_executable(args.pg_restore, "pg_restore")
        dump = create_dump(
            target=dump_path,
            pg_dump=pg_dump,
            pg_restore=pg_restore,
            pgpass_file=pgpass_file,
            host=args.host,
            port=args.port,
            database=args.database,
            user=pgpass_entry.user,
        )
        try:
            admission = verify_admission_manifest(
                args.admission_manifest.resolve()
            )
            manifest: dict[str, Any] = {
                "schema_version": "1.0.0",
                "snapshot_version": (
                    f"acceptance-{datetime.now(timezone.utc):%Y%m%d}-"
                    f"{repository['git_sha'][:7]}"
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "repository": repository,
                "admission": admission,
                "database": database,
                "dump": dump,
                "runtime_archive": {
                    "identifier": runtime_archive.parent.name
                    + "/"
                    + runtime_archive.name,
                    "bytes": runtime_archive.stat().st_size,
                    "sha256": sha256_file(runtime_archive),
                },
            }
            manifest_file_hash = write_manifest(manifest_path, manifest)
        except Exception:
            dump_path.unlink(missing_ok=True)
            raise

        print(
            json.dumps(
                {
                    "status": "DEP1_SNAPSHOT_CREATED",
                    "snapshot_version": manifest["snapshot_version"],
                    "dump_path": str(dump_path),
                    "dump_bytes": dump["bytes"],
                    "dump_sha256": dump["sha256"],
                    "manifest_path": str(manifest_path),
                    "manifest_contract_sha256": manifest["manifest_sha256"],
                    "manifest_file_sha256": manifest_file_hash,
                    "policy_count": database["row_counts"]["policies"],
                    "collection_run_count": database["row_counts"][
                        "collection_runs"
                    ],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (
        SnapshotError,
        OSError,
        psycopg2.Error,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as error:
        print(f"DEP1_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
