#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups/db}"
PG_SERVICE_NAME="${PG_SERVICE_NAME:-postgres}"
PG_CLIENT_IMAGE="${PG_CLIENT_IMAGE:-postgres:17}"
LOCAL_PG_CONTAINER_NAME="${LOCAL_PG_CONTAINER_NAME:-wikibook-local-postgres}"

log() {
    printf '%s\n' "$*" >&2
}

fail() {
    log "Error: $*"
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

find_python() {
    local candidate
    for candidate in \
        "${ROOT_DIR}/.venv/bin/python" \
        "${ROOT_DIR}/venv/bin/python" \
        "$(command -v python3 2>/dev/null || true)" \
        "$(command -v python 2>/dev/null || true)"; do
        if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
            printf '%s\n' "${candidate}"
            return 0
        fi
    done

    return 1
}

load_database_url() {
    if [ -n "${DATABASE_URL:-}" ]; then
        return 0
    fi

    if [ ! -f "${ENV_FILE}" ]; then
        fail "DATABASE_URL is not set and env file was not found: ${ENV_FILE}"
    fi

    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a

    if [ -z "${DATABASE_URL:-}" ]; then
        fail "DATABASE_URL is not configured in ${ENV_FILE}"
    fi
}

parse_database_url() {
    local python_bin
    python_bin="$(find_python)" || fail "Python is required to parse DATABASE_URL"

    local parsed
    parsed="$("${python_bin}" - <<'PY'
import os
import shlex
import sys
from urllib.parse import urlparse, unquote

url = os.environ.get("DATABASE_URL", "")
if not url:
    print("DATABASE_URL is empty", file=sys.stderr)
    sys.exit(1)

parsed = urlparse(url)
scheme = (parsed.scheme or "").lower()
if not (scheme.startswith("postgresql") or scheme.startswith("postgres")):
    print(
        f"DATABASE_URL must point to PostgreSQL, got: {url}. "
        "Please update .env and set DATABASE_URL to a postgresql:// or postgresql+psycopg:// value.",
        file=sys.stderr,
    )
    sys.exit(1)

database = unquote((parsed.path or "").lstrip("/"))
if not database:
    print("DATABASE_URL is missing the database name", file=sys.stderr)
    sys.exit(1)

fields = {
    "PG_USER": unquote(parsed.username or ""),
    "PG_PASSWORD": unquote(parsed.password or ""),
    "PG_HOST": parsed.hostname or "127.0.0.1",
    "PG_PORT": parsed.port or 5432,
    "PG_DATABASE": database,
}

for key, value in fields.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
)" || fail "Unable to parse DATABASE_URL"

    # shellcheck disable=SC2086
    eval "${parsed}"

    if [ -z "${PG_USER}" ]; then
        fail "DATABASE_URL is missing the PostgreSQL username"
    fi

    PG_MAINTENANCE_DB="${PG_MAINTENANCE_DB:-postgres}"
    if [ "${PG_MAINTENANCE_DB}" = "${PG_DATABASE}" ]; then
        PG_MAINTENANCE_DB="template1"
    fi
}

timestamp_now() {
    date +"%Y%m%d_%H%M%S"
}

sanitize_label() {
    local label="${1:-backup}"
    label="${label// /_}"
    label="${label//[^A-Za-z0-9._-]/_}"
    printf '%s\n' "${label}"
}

default_backup_path() {
    local label
    label="$(sanitize_label "${1:-backup}")"
    mkdir -p "${BACKUP_DIR}"
    printf '%s/%s_%s_%s.dump\n' "${BACKUP_DIR}" "${PG_DATABASE}" "${label}" "$(timestamp_now)"
}

have_local_pg_tools() {
    command -v pg_dump >/dev/null 2>&1 && \
        command -v pg_restore >/dev/null 2>&1 && \
        command -v psql >/dev/null 2>&1
}

docker_compose_container_id() {
    if command_exists docker && docker compose version >/dev/null 2>&1; then
        docker compose ps -q "${PG_SERVICE_NAME}" 2>/dev/null || true
    fi
}

docker_can_run() {
    command_exists docker && docker info >/dev/null 2>&1
}

local_pg_container_is_running() {
    docker_can_run && docker ps --format '{{.Names}}' | grep -Fx "${LOCAL_PG_CONTAINER_NAME}" >/dev/null 2>&1
}

local_pg_is_ready() {
    local python_bin
    python_bin="$(find_python 2>/dev/null || true)"
    if [ -n "${python_bin}" ] && [ -x "${python_bin}" ]; then
        PGHOST="${PG_HOST}" \
        PGPORT="${PG_PORT}" \
        PGUSER="${PG_USER}" \
        PGPASSWORD="${PG_PASSWORD}" \
        PGDATABASE="${PG_DATABASE}" \
        "${python_bin}" - <<'PY' >/dev/null 2>&1
import os
import sys

try:
    import psycopg
except Exception:
    sys.exit(2)

try:
    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=2,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
except Exception:
    sys.exit(1)
PY
        case "$?" in
            0) return 0 ;;
            1) return 1 ;;
        esac
    fi

    if command_exists pg_isready; then
        pg_isready -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" >/dev/null 2>&1
        return $?
    fi

    return 1
}

docker_host_for_client() {
    case "${PG_HOST}" in
        127.0.0.1|localhost)
            if command_exists colima && colima status >/dev/null 2>&1; then
                printf '%s\n' "host.lima.internal"
            else
                printf '%s\n' "host.docker.internal"
            fi
            ;;
        *)
            printf '%s\n' "${PG_HOST}"
            ;;
    esac
}

ensure_pg_client_image() {
    if ! docker image inspect "${PG_CLIENT_IMAGE}" >/dev/null 2>&1; then
        log "Pulling PostgreSQL client image ${PG_CLIENT_IMAGE} ..."
        docker pull "${PG_CLIENT_IMAGE}" >/dev/null
    fi
}

run_docker_client() {
    ensure_pg_client_image
    docker run --rm \
        --add-host=host.docker.internal:host-gateway \
        --add-host=host.lima.internal:host-gateway \
        -e PGPASSWORD="${PG_PASSWORD}" \
        "${PG_CLIENT_IMAGE}" "$@"
}

docker_volume_pg_version() {
    local volume_name="$1"

    ensure_pg_client_image
    docker run --rm \
        -v "${volume_name}:/data:ro" \
        --entrypoint cat \
        "${PG_CLIENT_IMAGE}" \
        /data/PG_VERSION 2>/dev/null | tr -d '[:space:]'
}

start_temp_pg_from_volume() {
    local volume_name="$1"
    local version="$2"

    TEMP_PG_CONTAINER_NAME="wikibook-pg-temp-$$-$RANDOM"
    TEMP_PG_IMAGE="postgres:${version}"

    if ! docker image inspect "${TEMP_PG_IMAGE}" >/dev/null 2>&1; then
        log "Pulling PostgreSQL server image ${TEMP_PG_IMAGE} ..."
        docker pull "${TEMP_PG_IMAGE}" >/dev/null
    fi

    docker rm -f "${TEMP_PG_CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker run -d \
        --name "${TEMP_PG_CONTAINER_NAME}" \
        -e POSTGRES_PASSWORD="${PG_PASSWORD}" \
        -v "${volume_name}:/var/lib/postgresql/data" \
        "${TEMP_PG_IMAGE}" >/dev/null

    local attempt
    for attempt in $(seq 1 30); do
        if docker exec "${TEMP_PG_CONTAINER_NAME}" pg_isready -h 127.0.0.1 -p 5432 -U postgres >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done

    docker logs "${TEMP_PG_CONTAINER_NAME}" >&2 || true
    docker rm -f "${TEMP_PG_CONTAINER_NAME}" >/dev/null 2>&1 || true
    TEMP_PG_CONTAINER_NAME=""
    fail "Unable to start a temporary PostgreSQL ${version} container from volume ${volume_name}"
}

stop_temp_pg_from_volume() {
    if [ -n "${TEMP_PG_CONTAINER_NAME:-}" ]; then
        docker rm -f "${TEMP_PG_CONTAINER_NAME}" >/dev/null 2>&1 || true
        TEMP_PG_CONTAINER_NAME=""
    fi
}

detect_pg_volume_runner() {
    find_matching_pg_volume || return 1
    start_temp_pg_from_volume "${PG_VOLUME_NAME}" "${PG_VOLUME_VERSION}"
    trap 'stop_temp_pg_from_volume' EXIT
    return 0
}

find_matching_pg_volume() {
    docker_can_run || return 1

    local matches=0
    local volume_name version has_db has_role volumes_file
    volumes_file="$(mktemp)"
    docker volume ls -q > "${volumes_file}"

    while IFS= read -r volume_name; do
        [ -n "${volume_name}" ] || continue
        version="$(docker_volume_pg_version "${volume_name}")"
        [ -n "${version}" ] || continue

        start_temp_pg_from_volume "${volume_name}" "${version}"
        has_db="$(docker exec "${TEMP_PG_CONTAINER_NAME}" psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${PG_DATABASE}'" 2>/dev/null | tr -d '[:space:]')"
        has_role="$(docker exec "${TEMP_PG_CONTAINER_NAME}" psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname = '${PG_USER}'" 2>/dev/null | tr -d '[:space:]')"
        stop_temp_pg_from_volume

        if [ "${has_db}" = "1" ] && [ "${has_role}" = "1" ]; then
            matches=$((matches + 1))
            PG_VOLUME_NAME="${volume_name}"
            PG_VOLUME_VERSION="${version}"
        fi
    done < "${volumes_file}"
    rm -f "${volumes_file}"

    if [ "${matches}" -eq 1 ]; then
        return 0
    fi

    if [ "${matches}" -gt 1 ]; then
        fail "Found multiple PostgreSQL data volumes matching database '${PG_DATABASE}'. Set PG_VOLUME_NAME explicitly."
    fi

    return 1
}

select_pg_runner() {
    PG_CONTAINER_ID=""
    if docker_can_run; then
        PG_CONTAINER_ID="$(docker_compose_container_id)"
    fi

    if [ "${PG_HOST}" = "postgres" ] && [ -n "${PG_CONTAINER_ID}" ]; then
        PG_RUNNER="compose"
        return 0
    fi

    if local_pg_container_is_running; then
        PG_RUNNER="docker-local"
        return 0
    fi

    if have_local_pg_tools && local_pg_is_ready; then
        PG_RUNNER="local"
        return 0
    fi

    if local_pg_is_ready; then
        if have_local_pg_tools; then
            PG_RUNNER="local"
        else
            PG_RUNNER="docker-client"
        fi
        return 0
    fi

    if detect_pg_volume_runner; then
        PG_RUNNER="docker-volume"
        return 0
    fi

    case "${PG_HOST}" in
        localhost|127.0.0.1)
            fail "No active PostgreSQL instance is reachable at ${PG_HOST}:${PG_PORT}, and no matching Docker PostgreSQL data volume was found"
            ;;
        postgres)
            if [ -n "${PG_CONTAINER_ID}" ]; then
                PG_RUNNER="compose"
                return 0
            fi
            fail "DATABASE_URL host is 'postgres', but docker compose service '${PG_SERVICE_NAME}' is not running"
            ;;
        *)
            if have_local_pg_tools; then
                fail "PostgreSQL server ${PG_HOST}:${PG_PORT} is not reachable"
            fi
            fail "DATABASE_URL host '${PG_HOST}' requires local PostgreSQL client tools"
            ;;
    esac
}

run_pg_dump_to_file() {
    local output_path="$1"

    if [ "${PG_RUNNER}" = "local" ]; then
        PGPASSWORD="${PG_PASSWORD}" pg_dump \
            -h "${PG_HOST}" \
            -p "${PG_PORT}" \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            -Fc \
            -f "${output_path}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "compose" ]; then
        docker compose exec -T \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${PG_SERVICE_NAME}" \
            pg_dump \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            -Fc > "${output_path}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-local" ]; then
        docker exec \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${LOCAL_PG_CONTAINER_NAME}" \
            pg_dump \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            -Fc > "${output_path}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-volume" ]; then
        docker exec \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${TEMP_PG_CONTAINER_NAME}" \
            pg_dump \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            -Fc > "${output_path}"
        return 0
    fi

    run_docker_client \
        pg_dump \
        -h "$(docker_host_for_client)" \
        -p "${PG_PORT}" \
        -U "${PG_USER}" \
        -d "${PG_DATABASE}" \
        -Fc > "${output_path}"
}

run_psql_maintenance() {
    local sql="$1"

    if [ "${PG_RUNNER}" = "local" ]; then
        PGPASSWORD="${PG_PASSWORD}" psql \
            -v ON_ERROR_STOP=1 \
            -v db_name="${PG_DATABASE}" \
            -h "${PG_HOST}" \
            -p "${PG_PORT}" \
            -U "${PG_USER}" \
            -d "${PG_MAINTENANCE_DB}" \
            -c "${sql}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "compose" ]; then
        docker compose exec -T \
            "${PG_SERVICE_NAME}" \
            psql \
            -v ON_ERROR_STOP=1 \
            -U postgres \
            -d "${PG_MAINTENANCE_DB}" \
            -c "${sql}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-local" ]; then
        docker exec \
            "${LOCAL_PG_CONTAINER_NAME}" \
            psql \
            -v ON_ERROR_STOP=1 \
            -U postgres \
            -d "${PG_MAINTENANCE_DB}" \
            -c "${sql}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-volume" ]; then
        docker exec \
            "${TEMP_PG_CONTAINER_NAME}" \
            psql \
            -v ON_ERROR_STOP=1 \
            -U postgres \
            -d "${PG_MAINTENANCE_DB}" \
            -c "${sql}"
        return 0
    fi

    run_docker_client \
        psql \
        -v ON_ERROR_STOP=1 \
        -v db_name="${PG_DATABASE}" \
        -h "$(docker_host_for_client)" \
        -p "${PG_PORT}" \
        -U "${PG_USER}" \
        -d "${PG_MAINTENANCE_DB}" \
        -c "${sql}"
}

reset_database() {
    local db_literal db_identifier owner_identifier
    db_literal="'${PG_DATABASE//\'/\'\'}'"
    db_identifier="\"${PG_DATABASE//\"/\"\"}\""
    owner_identifier="\"${PG_USER//\"/\"\"}\""

    run_psql_maintenance "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = ${db_literal} AND pid <> pg_backend_pid();"
    run_psql_maintenance "DROP DATABASE IF EXISTS ${db_identifier};"
    run_psql_maintenance "CREATE DATABASE ${db_identifier} OWNER ${owner_identifier};"
}

restore_dump_file() {
    local dump_path="$1"

    if [ "${PG_RUNNER}" = "local" ]; then
        PGPASSWORD="${PG_PASSWORD}" pg_restore \
            --no-owner \
            --no-privileges \
            -h "${PG_HOST}" \
            -p "${PG_PORT}" \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            "${dump_path}"
        return 0
    fi

    if [ "${PG_RUNNER}" = "compose" ]; then
        local remote_dump="/tmp/$(basename "${dump_path}")"
        docker cp "${dump_path}" "${PG_CONTAINER_ID}:${remote_dump}" >/dev/null
        trap 'docker compose exec -T "${PG_SERVICE_NAME}" rm -f "'"${remote_dump}"'" >/dev/null 2>&1 || true' RETURN

        docker compose exec -T \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${PG_SERVICE_NAME}" \
            pg_restore \
            --no-owner \
            --no-privileges \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            "${remote_dump}"

        docker compose exec -T "${PG_SERVICE_NAME}" rm -f "${remote_dump}" >/dev/null 2>&1 || true
        trap - RETURN
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-local" ]; then
        local remote_dump="/tmp/$(basename "${dump_path}")"
        docker cp "${dump_path}" "${LOCAL_PG_CONTAINER_NAME}:${remote_dump}" >/dev/null
        trap 'docker exec "${LOCAL_PG_CONTAINER_NAME}" rm -f "'"${remote_dump}"'" >/dev/null 2>&1 || true' RETURN

        docker exec \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${LOCAL_PG_CONTAINER_NAME}" \
            pg_restore \
            --no-owner \
            --no-privileges \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            "${remote_dump}"

        docker exec "${LOCAL_PG_CONTAINER_NAME}" rm -f "${remote_dump}" >/dev/null 2>&1 || true
        trap - RETURN
        return 0
    fi

    if [ "${PG_RUNNER}" = "docker-volume" ]; then
        local remote_dump="/tmp/$(basename "${dump_path}")"
        docker cp "${dump_path}" "${TEMP_PG_CONTAINER_NAME}:${remote_dump}" >/dev/null
        trap 'docker exec "${TEMP_PG_CONTAINER_NAME}" rm -f "'"${remote_dump}"'" >/dev/null 2>&1 || true' RETURN

        docker exec \
            -e PGPASSWORD="${PG_PASSWORD}" \
            "${TEMP_PG_CONTAINER_NAME}" \
            pg_restore \
            --no-owner \
            --no-privileges \
            -h 127.0.0.1 \
            -p 5432 \
            -U "${PG_USER}" \
            -d "${PG_DATABASE}" \
            "${remote_dump}"

        docker exec "${TEMP_PG_CONTAINER_NAME}" rm -f "${remote_dump}" >/dev/null 2>&1 || true
        trap - RETURN
        return 0
    fi

    local dump_dir dump_name
    dump_dir="$(cd "$(dirname "${dump_path}")" && pwd)"
    dump_name="$(basename "${dump_path}")"

    docker run --rm \
        --add-host=host.docker.internal:host-gateway \
        -e PGPASSWORD="${PG_PASSWORD}" \
        -v "${dump_dir}:/work:ro" \
        "${PG_CLIENT_IMAGE}" \
        pg_restore \
        --no-owner \
        --no-privileges \
        -h "$(docker_host_for_client)" \
        -p "${PG_PORT}" \
        -U "${PG_USER}" \
        -d "${PG_DATABASE}" \
        "/work/${dump_name}"
}
