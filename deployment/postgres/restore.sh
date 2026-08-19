#!/bin/sh
set -eu

fail() {
  echo "DEP3_BLOCKED: $1" >&2
  exit 1
}

case "${ACCEPTANCE_DUMP_FILENAME:-}" in
  ""|*/*|*\\*) fail "dump filename must be a basename" ;;
esac

[ "${#ACCEPTANCE_DUMP_SHA256}" -eq 64 ] \
  || fail "dump SHA-256 must contain exactly 64 hexadecimal characters"
case "$ACCEPTANCE_DUMP_SHA256" in
  *[!0-9a-fA-F]*) fail "dump SHA-256 must contain only hexadecimal characters" ;;
esac

dump_path="/snapshot/${ACCEPTANCE_DUMP_FILENAME}"
[ -f "$dump_path" ] || fail "verified dump is not mounted"

actual_hash="$(sha256sum "$dump_path" | awk '{print $1}')"
[ "$actual_hash" = "$(printf '%s' "$ACCEPTANCE_DUMP_SHA256" | tr 'A-F' 'a-f')" ] \
  || fail "mounted dump SHA-256 does not match the verified manifest"

expected_tables="administrative_region_aliases,administrative_regions,alembic_version,collection_runs,policies,policy_region_rules,policy_search_documents"
actual_tables="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT string_agg(tablename, ',' ORDER BY tablename) FROM pg_catalog.pg_tables WHERE schemaname = 'public';")"
[ "$actual_tables" = "$expected_tables" ] \
  || fail "migration-created schema table allowlist mismatch"

actual_revision="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT version_num FROM alembic_version;")"
[ "$actual_revision" = "$ACCEPTANCE_ALEMBIC_REVISION" ] \
  || fail "migration-created schema revision mismatch"

data_tables="administrative_regions administrative_region_aliases collection_runs policies policy_region_rules policy_search_documents"
for table_name in $data_tables; do
  row_count="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
    --command "SELECT count(*) FROM public.$table_name;")"
  [ "$row_count" = "0" ] \
    || fail "target schema contains Acceptance data ($table_name=$row_count)"
done

full_toc="/tmp/acceptance-full.list"
data_toc="/tmp/acceptance-data.list"
pg_restore --list "$dump_path" > "$full_toc"
grep '^;' "$full_toc" > "$data_toc"

for table_name in $data_tables; do
  matches="$(grep -c " TABLE DATA public $table_name " "$full_toc" || true)"
  [ "$matches" = "1" ] || fail "dump table data TOC mismatch for $table_name"
  grep " TABLE DATA public $table_name " "$full_toc" >> "$data_toc"
done

for sequence_name in policies_id_seq policy_region_rules_id_seq; do
  matches="$(grep -c " SEQUENCE SET public $sequence_name " "$full_toc" || true)"
  [ "$matches" = "1" ] || fail "dump sequence TOC mismatch for $sequence_name"
  grep " SEQUENCE SET public $sequence_name " "$full_toc" >> "$data_toc"
done

pg_restore \
  --dbname "$PGDATABASE" \
  --data-only \
  --use-list "$data_toc" \
  --no-owner \
  --no-acl \
  --disable-triggers \
  --superuser "$PGUSER" \
  --exit-on-error \
  --single-transaction \
  "$dump_path"

restored_policy_count="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT count(*) FROM policies;")"
[ "$restored_policy_count" = "3273" ] \
  || fail "restored Policy count does not match the snapshot baseline"

echo "DEP3_RESTORE_COMPLETED: hash verified, migration schema loaded with snapshot data"
