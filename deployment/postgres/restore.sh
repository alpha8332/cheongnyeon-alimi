#!/bin/sh
set -eu

fail() {
  echo "DEP2_BLOCKED: $1" >&2
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

table_count="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname = 'public';")"
sequence_count="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT count(*) FROM pg_catalog.pg_sequences WHERE schemaname = 'public';")"

[ "$table_count" = "0" ] || fail "target database is not empty (public tables=$table_count)"
[ "$sequence_count" = "0" ] || fail "target database is not empty (public sequences=$sequence_count)"

pg_restore \
  --dbname "$PGDATABASE" \
  --no-owner \
  --no-acl \
  --exit-on-error \
  --single-transaction \
  "$dump_path"

restored_table_count="$(psql --no-psqlrc --tuples-only --no-align --set ON_ERROR_STOP=1 \
  --command "SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname = 'public';")"
[ "$restored_table_count" = "7" ] \
  || fail "restored public table count is not the expected allowlist size"

echo "DEP2_RESTORE_COMPLETED: hash verified, empty target restored"
