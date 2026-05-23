#!/usr/bin/env bash

[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_postgres_common.sh"

usage() {
    cat <<'EOF'
Usage: scripts/backup_postgres.sh [--label LABEL] [--output FILE] [--print-path]

Options:
  --label LABEL   Label used in the generated backup filename.
  --output FILE   Explicit output path for the backup dump.
  --print-path    Print only the final backup path to stdout.
EOF
}

label="backup"
output_path=""
print_path_only=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --label)
            [ "$#" -ge 2 ] || fail "--label requires a value"
            label="$2"
            shift 2
            ;;
        --output)
            [ "$#" -ge 2 ] || fail "--output requires a value"
            output_path="$2"
            shift 2
            ;;
        --print-path)
            print_path_only=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "Unknown argument: $1"
            ;;
    esac
done

load_database_url
parse_database_url
select_pg_runner

if [ -z "${output_path}" ]; then
    output_path="$(default_backup_path "${label}")"
else
    mkdir -p "$(dirname "${output_path}")"
fi

log "Backing up PostgreSQL database '${PG_DATABASE}' using ${PG_RUNNER} runner..."
run_pg_dump_to_file "${output_path}"

if [ "${print_path_only}" -eq 1 ]; then
    printf '%s\n' "${output_path}"
else
    printf 'Backup created: %s\n' "${output_path}"
fi
