#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${ROOT_DIR}/.wikibook-local.pid"
LOGFILE="${ROOT_DIR}/.wikibook-local.log"

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

    cd "${ROOT_DIR}"
    : > "${LOGFILE}"

    echo "Starting Wikibook locally at http://${host}:${port}"
    nohup "${python_bin}" -c "import os; from app import app; app.run(host=os.environ.get('HOST', '${host}'), port=int(os.environ.get('PORT', '${port}')), debug=False, use_reloader=False)" \
        >> "${LOGFILE}" 2>&1 &

    echo $! > "${PIDFILE}"
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

restart_service() {
    echo "Restarting Wikibook local service..."
    stop_service
    start_service
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
}

show_logs() {
    if [ ! -f "${LOGFILE}" ]; then
        echo "No log file found yet at ${LOGFILE}."
        return 0
    fi

    tail -n 50 "${LOGFILE}"
}

case "${1:-restart}" in
    start)
        start_service
        ;;
    stop)
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
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo "No argument defaults to: restart"
        exit 1
        ;;
esac
