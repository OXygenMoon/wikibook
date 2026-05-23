#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_PIDFILE="${ROOT_DIR}/.wikibook-web.pid"
WEB_LOGFILE="${ROOT_DIR}/.wikibook-web.log"
JUDGE_PIDFILE="${ROOT_DIR}/.wikibook-judge.pid"
JUDGE_LOGFILE="${ROOT_DIR}/.wikibook-judge.log"

load_env() {
    if [ -f "${ROOT_DIR}/.env" ]; then
        set -a
        # shellcheck disable=SC1091
        source "${ROOT_DIR}/.env"
        set +a
    fi
}

find_python() {
    local candidate
    for candidate in \
        "${ROOT_DIR}/.venv/bin/python" \
        "${ROOT_DIR}/venv/bin/python" \
        "$(command -v python3 2>/dev/null || true)" \
        "$(command -v python 2>/dev/null || true)"; do
        if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

find_gunicorn() {
    local candidate
    for candidate in \
        "${ROOT_DIR}/.venv/bin/gunicorn" \
        "${ROOT_DIR}/venv/bin/gunicorn" \
        "$(command -v gunicorn 2>/dev/null || true)"; do
        if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

find_npm() {
    command -v npm 2>/dev/null || true
}

pid_is_running() {
    local pidfile="$1"
    if [ ! -f "${pidfile}" ]; then
        return 1
    fi

    local pid
    pid="$(cat "${pidfile}")"
    [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null
}

process_command() {
    local pid="$1"
    ps -p "${pid}" -o command= 2>/dev/null || true
}

process_cwd() {
    local pid="$1"
    if [ -L "/proc/${pid}/cwd" ]; then
        readlink "/proc/${pid}/cwd" 2>/dev/null || true
    else
        pwdx "${pid}" 2>/dev/null | sed 's/^[^:]*: //' || true
    fi
}

is_project_web_process() {
    local pid="$1"
    local command cwd
    command="$(process_command "${pid}")"
    cwd="$(process_cwd "${pid}")"

    if [[ "${command}" != *"gunicorn"* && "${command}" != *"from app import app"* ]]; then
        return 1
    fi

    [[ "${command}" == *"${ROOT_DIR}"* || "${cwd}" == "${ROOT_DIR}" ]]
}

stop_pid() {
    local pid="$1"
    local label="$2"

    if [ -z "${pid}" ] || ! kill -0 "${pid}" 2>/dev/null; then
        return 0
    fi

    echo "Stopping ${label} (PID: ${pid}) ..."
    kill "${pid}" 2>/dev/null || true

    local waited=0
    while kill -0 "${pid}" 2>/dev/null; do
        if [ "${waited}" -ge 10 ]; then
            echo "${label} did not stop after SIGTERM; forcing shutdown ..."
            kill -9 "${pid}" 2>/dev/null || true
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done
}

stop_orphaned_web_processes() {
    local pids pid found
    found=0
    pids="$(pgrep -f 'gunicorn|from app import app' 2>/dev/null || true)"

    for pid in ${pids}; do
        if [ "${pid}" = "$$" ]; then
            continue
        fi
        if is_project_web_process "${pid}"; then
            found=1
            stop_pid "${pid}" "orphaned web process"
        fi
    done

    if [ "${found}" -eq 0 ]; then
        echo "No orphaned Wikibook web processes found."
    fi
}

try_start_system_service() {
    local service_name="$1"
    if ! command -v systemctl >/dev/null 2>&1; then
        return 1
    fi

    if systemctl is-active --quiet "${service_name}"; then
        return 0
    fi

    echo "Starting system service: ${service_name}"
    if [ "$(id -u)" -eq 0 ]; then
        systemctl start "${service_name}"
    elif command -v sudo >/dev/null 2>&1; then
        sudo systemctl start "${service_name}"
    else
        echo "Cannot start ${service_name}: current user is not root and sudo is unavailable."
        return 1
    fi
}

redis_is_ready() {
    load_env

    local python_bin
    python_bin="$(find_python)" || return 1

    REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}" "${python_bin}" - <<'PY' >/dev/null 2>&1
import os
from redis import Redis

Redis.from_url(os.environ["REDIS_URL"]).ping()
PY
}

ensure_postgres() {
    if command -v pg_isready >/dev/null 2>&1; then
        if pg_isready -q; then
            echo "PostgreSQL is running."
            return 0
        fi
    fi

    if try_start_system_service postgresql; then
        sleep 2
    fi

    if command -v pg_isready >/dev/null 2>&1 && pg_isready -q; then
        echo "PostgreSQL started."
        return 0
    fi

    echo "PostgreSQL does not appear to be ready. Please verify your database service."
    return 1
}

ensure_redis() {
    if redis_is_ready; then
        echo "Redis is running."
        return 0
    fi

    if try_start_system_service redis-server; then
        sleep 1
    fi

    if redis_is_ready; then
        echo "Redis started."
        return 0
    fi

    echo "Redis is not available. Please install/start redis-server first."
    return 1
}

ensure_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "Docker CLI is missing. Install docker.io or Docker Engine first."
        return 1
    fi

    if docker info >/dev/null 2>&1; then
        echo "Docker is running."
        return 0
    fi

    if try_start_system_service docker; then
        sleep 2
    fi

    if docker info >/dev/null 2>&1; then
        echo "Docker started."
        return 0
    fi

    echo "Docker daemon is not reachable. Please verify docker permissions/service."
    return 1
}

ensure_runtime_image() {
    local runtime_image="${JUDGE_RUNTIME_IMAGE:-wikibook-judge-runtime:latest}"

    if docker image inspect "${runtime_image}" >/dev/null 2>&1; then
        echo "Judge runtime image exists: ${runtime_image}"
        return 0
    fi

    echo "Judge runtime image is missing. Building ${runtime_image} ..."
    docker build -t "${runtime_image}" -f "${ROOT_DIR}/judge_runtime/Dockerfile" "${ROOT_DIR}"
}

build_frontend_assets() {
    local npm_bin
    npm_bin="$(find_npm)"
    if [ -z "${npm_bin}" ]; then
        echo "npm is missing; skipping OJ Vue asset build."
        return 0
    fi

    cd "${ROOT_DIR}"
    if [ ! -d "${ROOT_DIR}/node_modules" ]; then
        echo "Installing frontend dependencies ..."
        "${npm_bin}" install
    fi

    echo "Building OJ Vue assets ..."
    "${npm_bin}" run build:oj
}

ensure_dependencies() {
    load_env
    ensure_postgres
    ensure_redis
    ensure_docker
    ensure_runtime_image
}

start_web() {
    if pid_is_running "${WEB_PIDFILE}"; then
        echo "Web service is already running (PID: $(cat "${WEB_PIDFILE}"))."
        return 0
    fi

    load_env

    local gunicorn_bin
    gunicorn_bin="$(find_gunicorn)" || {
        echo "Unable to find gunicorn. Install dependencies first: pip install -r requirements.txt"
        exit 1
    }

    local host="${HOST:-127.0.0.1}"
    local port="${PORT:-5009}"

    cd "${ROOT_DIR}"
    stop_orphaned_web_processes
    : > "${WEB_LOGFILE}"

    echo "Starting Wikibook web at http://${host}:${port}"
    GUNICORN_DAEMON=true \
    GUNICORN_PIDFILE="${WEB_PIDFILE}" \
    GUNICORN_BIND="${host}:${port}" \
    GUNICORN_ACCESSLOG="${WEB_LOGFILE}" \
    GUNICORN_ERRORLOG="${WEB_LOGFILE}" \
    "${gunicorn_bin}" --config "${ROOT_DIR}/gunicorn.conf.py" app:app

    sleep 2
    if pid_is_running "${WEB_PIDFILE}"; then
        echo "Web service started (PID: $(cat "${WEB_PIDFILE}"))."
        echo "Web log: ${WEB_LOGFILE}"
        return 0
    fi

    echo "Web service failed to start. Recent logs:"
    tail -n 80 "${WEB_LOGFILE}" 2>/dev/null || true
    exit 1
}

start_judge() {
    if [ "${SKIP_JUDGE:-0}" = "1" ]; then
        echo "Skipping judge worker because SKIP_JUDGE=1."
        return 0
    fi

    if pid_is_running "${JUDGE_PIDFILE}"; then
        echo "Judge worker is already running (PID: $(cat "${JUDGE_PIDFILE}"))."
        return 0
    fi

    load_env

    local python_bin
    python_bin="$(find_python)" || {
        echo "Unable to find Python interpreter."
        exit 1
    }

    cd "${ROOT_DIR}"
    : > "${JUDGE_LOGFILE}"

    echo "Starting judge worker ..."
    nohup env PYTHONUNBUFFERED=1 "${python_bin}" "${ROOT_DIR}/judge_worker.py" >> "${JUDGE_LOGFILE}" 2>&1 &
    echo $! > "${JUDGE_PIDFILE}"
    sleep 2

    if pid_is_running "${JUDGE_PIDFILE}"; then
        echo "Judge worker started (PID: $(cat "${JUDGE_PIDFILE}"))."
        echo "Judge log: ${JUDGE_LOGFILE}"
        return 0
    fi

    echo "Judge worker failed to start. Recent logs:"
    tail -n 80 "${JUDGE_LOGFILE}" 2>/dev/null || true
    exit 1
}

stop_process() {
    local pidfile="$1"
    local label="$2"

    if ! pid_is_running "${pidfile}"; then
        rm -f "${pidfile}"
        echo "${label} is not running."
        return 0
    fi

    local pid
    pid="$(cat "${pidfile}")"
    stop_pid "${pid}" "${label}"

    rm -f "${pidfile}"
    echo "${label} stopped."
}

stop_web() {
    stop_process "${WEB_PIDFILE}" "Web service"
    stop_orphaned_web_processes
    rm -f "${ROOT_DIR}/.wikibook-local.pid"
}

show_status() {
    load_env

    local host="${HOST:-127.0.0.1}"
    local port="${PORT:-5009}"

    echo "Wikibook status"
    echo "==============="
    if pid_is_running "${WEB_PIDFILE}"; then
        echo "Web:    running (PID: $(cat "${WEB_PIDFILE}"))"
        echo "URL:    http://${host}:${port}"
    else
        echo "Web:    stopped"
    fi
    local extra_web_pids=""
    local pid
    for pid in $(pgrep -f 'gunicorn|from app import app' 2>/dev/null || true); do
        if [ "${pid}" != "$$" ] && is_project_web_process "${pid}"; then
            extra_web_pids="${extra_web_pids} ${pid}"
        fi
    done
    if [ -n "${extra_web_pids}" ]; then
        echo "Web pids:${extra_web_pids}"
    fi

    if pid_is_running "${JUDGE_PIDFILE}"; then
        echo "Judge:  running (PID: $(cat "${JUDGE_PIDFILE}"))"
    else
        echo "Judge:  stopped"
    fi

    echo
    if command -v pg_isready >/dev/null 2>&1; then
        echo -n "PostgreSQL: "
        if pg_isready -q; then
            echo "ready"
        else
            echo "not ready"
        fi
    fi

    if command -v redis-cli >/dev/null 2>&1; then
        echo -n "Redis:      "
        if redis_is_ready; then
            echo "ready"
        else
            echo "not ready"
        fi
    fi

    if command -v docker >/dev/null 2>&1; then
        echo -n "Docker:     "
        if docker info >/dev/null 2>&1; then
            echo "ready"
        else
            echo "not ready"
        fi
    fi
}

show_logs() {
    echo "== Web logs =="
    if [ -f "${WEB_LOGFILE}" ]; then
        tail -n 80 "${WEB_LOGFILE}"
    else
        echo "No web log file yet: ${WEB_LOGFILE}"
    fi

    echo
    echo "== Judge logs =="
    if [ -f "${JUDGE_LOGFILE}" ]; then
        tail -n 80 "${JUDGE_LOGFILE}"
    else
        echo "No judge log file yet: ${JUDGE_LOGFILE}"
    fi
}

bootstrap_schema() {
    load_env

    local python_bin
    python_bin="$(find_python)" || {
        echo "Unable to find Python interpreter."
        exit 1
    }

    cd "${ROOT_DIR}"
    "${python_bin}" -m flask --app app wikibook init-platform --with-schema
}

case "${1:-restart}" in
    start)
        ensure_dependencies
        build_frontend_assets
        start_web
        start_judge
        ;;
    stop)
        stop_process "${JUDGE_PIDFILE}" "Judge worker"
        stop_web
        ;;
    restart)
        stop_process "${JUDGE_PIDFILE}" "Judge worker"
        stop_web
        ensure_dependencies
        build_frontend_assets
        start_web
        start_judge
        ;;
    build-frontend)
        build_frontend_assets
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    deps)
        ensure_dependencies
        ;;
    init)
        bootstrap_schema
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|deps|init|build-frontend}"
        echo "No argument defaults to: restart"
        exit 1
        ;;
esac
