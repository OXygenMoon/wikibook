#!/usr/bin/env bash

[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_postgres_common.sh"

LOCAL_PG_CONTAINER_NAME="${LOCAL_PG_CONTAINER_NAME:-wikibook-local-postgres}"

container_needs_recreate() {
    local current_mount current_cmd
    current_mount="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "${LOCAL_PG_CONTAINER_NAME}" 2>/dev/null || true)"
    current_cmd="$(docker inspect -f '{{json .Config.Cmd}}' "${LOCAL_PG_CONTAINER_NAME}" 2>/dev/null || true)"

    [ "${current_mount}" != "${PG_VOLUME_NAME}" ] && return 0
    printf '%s' "${current_cmd}" | grep -F 'listen_addresses=*' >/dev/null 2>&1 || return 0
    return 1
}

ensure_container_hba() {
    if ! docker exec "${LOCAL_PG_CONTAINER_NAME}" bash -lc "grep -F \"host all all 0.0.0.0/0 scram-sha-256\" /var/lib/postgresql/data/pg_hba.conf >/dev/null"; then
        docker exec "${LOCAL_PG_CONTAINER_NAME}" bash -lc "printf '\nhost all all 0.0.0.0/0 scram-sha-256\nhost all all ::/0 scram-sha-256\n' >> /var/lib/postgresql/data/pg_hba.conf"
    fi
    docker exec "${LOCAL_PG_CONTAINER_NAME}" psql -U postgres -d postgres -tAc "SELECT pg_reload_conf();" >/dev/null
}

wait_for_docker() {
    local attempts="${1:-45}"
    local waited=0

    while [ "${waited}" -lt "${attempts}" ]; do
        if docker_can_run; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    return 1
}

ensure_docker_for_local_postgres() {
    if docker_can_run; then
        return 0
    fi

    if ! command_exists docker; then
        return 1
    fi

    if ! command_exists colima; then
        return 1
    fi

    log "Docker is unavailable; starting Colima ..."
    colima start --cpu "${COLIMA_CPU:-2}" --memory "${COLIMA_MEMORY:-4}" --disk "${COLIMA_DISK:-20}" || return 1
    wait_for_docker 45
}

usage() {
    cat <<'EOF'
Usage: scripts/ensure_local_postgres.sh

Ensure a local PostgreSQL instance is reachable for the current DATABASE_URL.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

load_database_url
parse_database_url

case "${PG_HOST}" in
    127.0.0.1|localhost)
        ;;
    *)
        if local_pg_is_ready; then
            printf 'PostgreSQL is reachable at %s:%s\n' "${PG_HOST}" "${PG_PORT}"
            exit 0
        fi
        fail "DATABASE_URL points to ${PG_HOST}:${PG_PORT}, but the server is not reachable"
        ;;
esac

if local_pg_is_ready; then
    printf 'PostgreSQL is already running at %s:%s\n' "${PG_HOST}" "${PG_PORT}"
    exit 0
fi

ensure_docker_for_local_postgres || fail "PostgreSQL is not reachable at ${PG_HOST}:${PG_PORT}, and Docker is unavailable"
find_matching_pg_volume || fail "PostgreSQL is not reachable at ${PG_HOST}:${PG_PORT}, and no matching Docker PostgreSQL data volume was found"

image_name="postgres:${PG_VOLUME_VERSION}"

if ! docker image inspect "${image_name}" >/dev/null 2>&1; then
    log "Pulling ${image_name} ..."
    docker pull "${image_name}" >/dev/null
fi

if docker ps -a --format '{{.Names}}' | grep -Fx "${LOCAL_PG_CONTAINER_NAME}" >/dev/null 2>&1; then
    if container_needs_recreate; then
        docker rm -f "${LOCAL_PG_CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
fi

if ! docker ps --format '{{.Names}}' | grep -Fx "${LOCAL_PG_CONTAINER_NAME}" >/dev/null 2>&1; then
    if docker ps -a --format '{{.Names}}' | grep -Fx "${LOCAL_PG_CONTAINER_NAME}" >/dev/null 2>&1; then
        docker start "${LOCAL_PG_CONTAINER_NAME}" >/dev/null
    else
        log "Starting PostgreSQL from Docker volume ${PG_VOLUME_NAME} ..."
        docker run -d \
            --name "${LOCAL_PG_CONTAINER_NAME}" \
            -p "${PG_PORT}:5432" \
            -e POSTGRES_PASSWORD="${PG_PASSWORD}" \
            -v "${PG_VOLUME_NAME}:/var/lib/postgresql/data" \
            "${image_name}" \
            -c listen_addresses='*' >/dev/null
    fi
fi

attempt=0
until docker exec "${LOCAL_PG_CONTAINER_NAME}" pg_isready -h 127.0.0.1 -p 5432 -U postgres >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "${attempt}" -ge 30 ]; then
        docker logs --tail 80 "${LOCAL_PG_CONTAINER_NAME}" >&2 || true
        fail "PostgreSQL container ${LOCAL_PG_CONTAINER_NAME} did not become ready in time"
    fi
    sleep 1
done

ensure_container_hba

docker exec "${LOCAL_PG_CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "ALTER ROLE ${PG_USER} WITH LOGIN PASSWORD '${PG_PASSWORD}';" >/dev/null 2>&1 || true

if ! local_pg_is_ready; then
    fail "PostgreSQL container started, but ${PG_HOST}:${PG_PORT} is still not reachable from the host"
fi

printf 'PostgreSQL is ready at %s:%s using Docker volume %s\n' "${PG_HOST}" "${PG_PORT}" "${PG_VOLUME_NAME}"
