#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="/app"
PORT="${PORT:-5009}"
HOST="${HOST:-0.0.0.0}"
POSTGRES_DB="${POSTGRES_DB:-wikibook}"
POSTGRES_USER="${POSTGRES_USER:-wikibook}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-wikibook}"
PGDATA="${PGDATA:-/var/lib/postgresql/data}"
REDIS_DATA_DIR="${REDIS_DATA_DIR:-/var/lib/redis}"

export HOST
export PORT
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export JUDGE_DOCKER_HOST="${JUDGE_DOCKER_HOST:-}"

POSTGRES_PID=""
REDIS_PID=""
WORKER_PID=""
WEB_PID=""

find_postgres_bin_dir() {
    local version_dir
    version_dir="$(find /usr/lib/postgresql -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)"
    if [ -n "${version_dir}" ]; then
        printf '%s/bin\n' "${version_dir}"
    fi
}

cleanup() {
    local pids=("${WEB_PID}" "${WORKER_PID}" "${REDIS_PID}" "${POSTGRES_PID}")
    local pid

    for pid in "${pids[@]}"; do
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}" 2>/dev/null || true
        fi
    done

    wait || true
}

wait_for_postgres() {
    local attempts=0
    until pg_isready -h /var/run/postgresql -p 5432 -U postgres >/dev/null 2>&1; do
        attempts=$((attempts + 1))
        if [ "${attempts}" -ge 30 ]; then
            echo "PostgreSQL failed to start in time."
            return 1
        fi
        sleep 1
    done
}

wait_for_redis() {
    local attempts=0
    until redis-cli -h 127.0.0.1 ping >/dev/null 2>&1; do
        attempts=$((attempts + 1))
        if [ "${attempts}" -ge 30 ]; then
            echo "Redis failed to start in time."
            return 1
        fi
        sleep 1
    done
}

ensure_postgres_data() {
    local pg_bin_dir
    pg_bin_dir="$(find_postgres_bin_dir)"
    if [ -z "${pg_bin_dir}" ]; then
        echo "Unable to find PostgreSQL binaries."
        exit 1
    fi

    mkdir -p "${PGDATA}" /var/run/postgresql
    chown -R postgres:postgres "${PGDATA}" /var/run/postgresql

    if [ ! -f "${PGDATA}/PG_VERSION" ]; then
        gosu postgres "${pg_bin_dir}/initdb" -D "${PGDATA}" --username=postgres --auth-local=trust --auth-host=scram-sha-256 >/dev/null
        cat >> "${PGDATA}/postgresql.conf" <<'EOF'
listen_addresses = '127.0.0.1'
port = 5432
unix_socket_directories = '/var/run/postgresql'
EOF
        cat >> "${PGDATA}/pg_hba.conf" <<'EOF'
local   all             all                                     trust
host    all             all             127.0.0.1/32            scram-sha-256
EOF
    fi
}

start_postgres() {
    local pg_bin_dir
    pg_bin_dir="$(find_postgres_bin_dir)"
    gosu postgres "${pg_bin_dir}/postgres" -D "${PGDATA}" &
    POSTGRES_PID=$!
    wait_for_postgres

    gosu postgres psql -v ON_ERROR_STOP=1 postgres <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
        CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${POSTGRES_PASSWORD}';
    ELSE
        ALTER ROLE ${POSTGRES_USER} WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}';
    END IF;
END
\$\$;
SQL

    gosu postgres psql -v ON_ERROR_STOP=1 postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}'" | grep -q 1 \
        || gosu postgres createdb -O "${POSTGRES_USER}" "${POSTGRES_DB}"
}

start_redis() {
    mkdir -p "${REDIS_DATA_DIR}"
    redis-server \
        --save 60 1 \
        --loglevel warning \
        --bind 127.0.0.1 \
        --protected-mode yes \
        --dir "${REDIS_DATA_DIR}" &
    REDIS_PID=$!
    wait_for_redis
}

ensure_runtime_image() {
    export JUDGE_RUNTIME_IMAGE="${JUDGE_RUNTIME_IMAGE:-wikibook-judge-runtime:latest}"
    python - <<'PY'
import os

import docker

image_name = os.environ["JUDGE_RUNTIME_IMAGE"]
client = docker.from_env()

try:
    client.images.get(image_name)
except docker.errors.ImageNotFound:
    client.images.build(path="/app", dockerfile="judge_runtime/Dockerfile", tag=image_name)
PY
}

start_application() {
    cd "${ROOT_DIR}"
    python -m flask --app app wikibook init-platform --with-schema

    python judge_worker.py &
    WORKER_PID=$!

    gunicorn --config gunicorn.conf.py app:app &
    WEB_PID=$!
}

trap cleanup EXIT INT TERM

ensure_postgres_data
start_postgres
start_redis
ensure_runtime_image
start_application

echo "All-in-one Wikibook container is ready at http://${HOST}:${PORT}"
wait -n "${POSTGRES_PID}" "${REDIS_PID}" "${WORKER_PID}" "${WEB_PID}"
