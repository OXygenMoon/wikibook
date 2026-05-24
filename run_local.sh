#!/usr/bin/env bash

[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${ROOT_DIR}/.wikibook-local.pid"
LOGFILE="${ROOT_DIR}/.wikibook-local.log"
JUDGE_SCRIPT="${ROOT_DIR}/run_judge_local.sh"
ENSURE_POSTGRES_SCRIPT="${ROOT_DIR}/scripts/ensure_local_postgres.sh"

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
        "/opt/homebrew/anaconda3/bin/python" \
        "$(command -v python3 2>/dev/null || true)" \
        "$(command -v python 2>/dev/null || true)"; do
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

is_running() {
    if [ ! -f "${PIDFILE}" ]; then
        return 1
    fi

    local pid
    pid="$(cat "${PIDFILE}")"

    if [ -z "${pid}" ]; then
        return 1
    fi

    kill -0 "${pid}" 2>/dev/null
}

start_service() {
    if is_running; then
        echo "Wikibook local service is already running (PID: $(cat "${PIDFILE}"))."
        return 0
    fi

    rm -f "${PIDFILE}"

    load_env

    local python_bin
    python_bin="$(find_python)" || {
        echo "Unable to find a Python interpreter. Tried .venv/bin/python, venv/bin/python, python3, and python."
        exit 1
    }

    local host="${HOST:-127.0.0.1}"
    local port="${PORT:-5009}"

    if [ -x "${ENSURE_POSTGRES_SCRIPT}" ]; then
        echo "Ensuring PostgreSQL is available..."
        "${ENSURE_POSTGRES_SCRIPT}"
    fi

    cd "${ROOT_DIR}"
    build_frontend_assets
    : > "${LOGFILE}"

    echo "Starting Wikibook locally at http://${host}:${port}"
    local server_code
    server_code="import os; from app import app; app.run(host=os.environ.get('HOST', '${host}'), port=int(os.environ.get('PORT', '${port}')), debug=False, use_reloader=False)"
    "${python_bin}" - "${python_bin}" "${LOGFILE}" "${ROOT_DIR}" "${server_code}" > "${PIDFILE}" <<'PY'
import os
import subprocess
import sys

python_bin, log_file, cwd, server_code = sys.argv[1:5]
log = open(log_file, "ab", buffering=0)
process = subprocess.Popen(
    [python_bin, "-c", server_code],
    cwd=cwd,
    env=os.environ.copy(),
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
    close_fds=True,
)
print(process.pid)
PY
    sleep 2

    if is_running; then
        echo "Service started successfully (PID: $(cat "${PIDFILE}"))."
        echo "Log file: ${LOGFILE}"
        return 0
    fi

    echo "Service failed to start. Recent logs:"
    tail -n 40 "${LOGFILE}" 2>/dev/null || true
    echo "If Python modules are missing, install dependencies first: pip install -r requirements.txt"
    echo "If this is a fresh database, initialize it first: flask --app app wikibook init-platform --with-schema"
    rm -f "${PIDFILE}"
    exit 1
}

start_judge_service() {
    if [ "${SKIP_JUDGE:-0}" = "1" ]; then
        echo "Skipping judge worker startup because SKIP_JUDGE=1."
        return 0
    fi

    if [ ! -x "${JUDGE_SCRIPT}" ]; then
        echo "Judge startup script is missing or not executable: ${JUDGE_SCRIPT}"
        exit 1
    fi

    load_env
    echo "Starting judge worker and dependencies..."
    "${JUDGE_SCRIPT}" start
}

stop_service() {
    if ! is_running; then
        rm -f "${PIDFILE}"
        echo "Wikibook local service is not running."
        return 0
    fi

    local pid
    pid="$(cat "${PIDFILE}")"

    echo "Stopping Wikibook local service (PID: ${pid})..."
    kill "${pid}"

    local waited=0
    while kill -0 "${pid}" 2>/dev/null; do
        if [ "${waited}" -ge 10 ]; then
            echo "Process ${pid} did not stop after SIGTERM; forcing shutdown..."
            kill -9 "${pid}" 2>/dev/null || true
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done

    waited=0
    while kill -0 "${pid}" 2>/dev/null; do
        if [ "${waited}" -ge 5 ]; then
            echo "Process ${pid} is still running. Please check it manually."
            exit 1
        fi
        sleep 1
        waited=$((waited + 1))
    done

    rm -f "${PIDFILE}"
    echo "Service stopped."
}

stop_judge_service() {
    if [ ! -x "${JUDGE_SCRIPT}" ]; then
        echo "Judge startup script is missing or not executable: ${JUDGE_SCRIPT}"
        return 0
    fi

    echo "Stopping judge worker..."
    "${JUDGE_SCRIPT}" stop
}

restart_service() {
    echo "Restarting Wikibook local service and judge worker..."
    stop_judge_service
    stop_service
    start_service
    start_judge_service
}

show_status() {
    load_env

    local host="${HOST:-127.0.0.1}"
    local port="${PORT:-5009}"

    if is_running; then
        echo "Wikibook local service is running (PID: $(cat "${PIDFILE}"))."
        echo "URL: http://${host}:${port}"
    else
        echo "Wikibook local service is stopped."
    fi

    echo
    echo "Judge status:"
    if [ -x "${JUDGE_SCRIPT}" ]; then
        "${JUDGE_SCRIPT}" status
    else
        echo "Judge startup script is missing or not executable: ${JUDGE_SCRIPT}"
    fi
}

show_logs() {
    echo "== Wikibook local service logs =="
    if [ ! -f "${LOGFILE}" ]; then
        echo "No log file found yet at ${LOGFILE}."
    else
        tail -n 50 "${LOGFILE}"
    fi

    echo
    echo "== Judge worker logs =="
    if [ -x "${JUDGE_SCRIPT}" ]; then
        "${JUDGE_SCRIPT}" logs
    else
        echo "Judge startup script is missing or not executable: ${JUDGE_SCRIPT}"
    fi
}

case "${1:-restart}" in
    start)
        start_service
        start_judge_service
        ;;
    stop)
        stop_judge_service
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build-frontend)
        build_frontend_assets
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|build-frontend}"
        echo "No argument defaults to: restart"
        exit 1
        ;;
esac
