#!/usr/bin/env bash

[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_postgres_common.sh"

usage() {
    cat <<'EOF'
Usage: scripts/restore_postgres.sh BACKUP_FILE

The script will always back up the current database before restoring.
EOF
}

if [ "$#" -ne 1 ]; then
    usage >&2
    exit 1
fi

case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
esac

backup_file="$1"
if [ ! -f "${backup_file}" ]; then
    fail "Backup file does not exist: ${backup_file}"
fi

load_database_url
parse_database_url
select_pg_runner

log "Creating a safety backup before restore..."
pre_restore_backup="$("${SCRIPT_DIR}/backup_postgres.sh" --label pre_restore --print-path)"
log "Current database backup saved to: ${pre_restore_backup}"

log "Resetting PostgreSQL database '${PG_DATABASE}'..."
reset_database

log "Restoring database from: ${backup_file}"
restore_dump_file "${backup_file}"

printf 'Restore completed from %s\nSafety backup created at %s\n' "${backup_file}" "${pre_restore_backup}"
