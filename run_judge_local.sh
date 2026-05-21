#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${ROOT_DIR}/.wikibook-judge-worker.pid"
LOGFILE="${ROOT_DIR}/.wikibook-judge-worker.log"
RUNTIME_IMAGE="${JUDGE_RUNTIME_IMAGE:-wikibook-judge-runtime:latest}"
COLIMA_SOCKET="${HOME}/.colima/default/docker.sock"

find_python() {
    local candidate
    for candidate in \
        "${ROOT_DIR}/.venv/bin/python" \
        "${ROOT_DIR}/venv/bin/python" \
        "/tmp/wikibook-verify-venv/bin/python" \
        "$(command -v python3 2>/dev/null || true)" \
        "$(command -v python 2>/dev/null || true)"; do
        if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

worker_env() {
    export PYTHONUNBUFFERED=1
    export JUDGE_WORKER_MODE="${JUDGE_WORKER_MODE:-simple}"
    if [ -z "${JUDGE_DOCKER_HOST:-}" ] && [ -S "${COLIMA_SOCKET}" ]; then
        export JUDGE_DOCKER_HOST="unix://${COLIMA_SOCKET}"
    fi
}

ensure_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        echo "Redis is running."
        return 0
    fi

    if ! command -v redis-server >/dev/null 2>&1; then
        echo "redis-server is missing. Install it with: brew install redis"
        exit 1
    fi

    redis-server --daemonize yes
    sleep 1
    redis-cli ping >/dev/null
    echo "Redis started."
}

ensure_colima() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "docker CLI is missing. Install it with: brew install docker docker-buildx"
        exit 1
    fi

    if docker info >/dev/null 2>&1; then
        echo "Docker is running."
        return 0
    fi

    if ! command -v colima >/dev/null 2>&1; then
        echo "Docker is not running, and colima is missing. Install it with: brew install colima"
        exit 1
    fi

    colima start --cpu "${COLIMA_CPU:-2}" --memory "${COLIMA_MEMORY:-4}" --disk "${COLIMA_DISK:-20}"
    echo "Colima started."
}

ensure_runtime_image() {
    if docker image inspect "${RUNTIME_IMAGE}" >/dev/null 2>&1; then
        echo "Judge runtime image exists: ${RUNTIME_IMAGE}"
        return 0
    fi

    docker build -t "${RUNTIME_IMAGE}" -f "${ROOT_DIR}/judge_runtime/Dockerfile" "${ROOT_DIR}"
    echo "Judge runtime image built: ${RUNTIME_IMAGE}"
}

is_worker_running() {
    [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null
}

start_worker_background() {
    if is_worker_running; then
        echo "Judge worker is already running (PID: $(cat "${PIDFILE}"))."
        return 0
    fi

    local python_bin
    python_bin="$(find_python)" || {
        echo "Unable to find Python."
        exit 1
    }

    worker_env
    : > "${LOGFILE}"
    cd "${ROOT_DIR}"
    nohup "${python_bin}" judge_worker.py >> "${LOGFILE}" 2>&1 &
    echo $! > "${PIDFILE}"
    sleep 2

    if is_worker_running; then
        echo "Judge worker started (PID: $(cat "${PIDFILE}"))."
        echo "Log file: ${LOGFILE}"
        return 0
    fi

    echo "Judge worker failed to stay running. Run foreground mode for diagnostics:"
    echo "  ./run_judge_local.sh worker"
    tail -n 80 "${LOGFILE}" 2>/dev/null || true
    exit 1
}

stop_worker() {
    if ! is_worker_running; then
        rm -f "${PIDFILE}"
        echo "Judge worker is not running."
        return 0
    fi

    local pid
    pid="$(cat "${PIDFILE}")"
    kill "${pid}" 2>/dev/null || true
    rm -f "${PIDFILE}"
    echo "Judge worker stopped."
}

show_status() {
    echo "Redis:"
    redis-cli ping 2>/dev/null || true
    echo
    echo "Docker:"
    docker info --format 'server={{.ServerVersion}} os={{.OperatingSystem}} arch={{.Architecture}}' 2>/dev/null || true
    echo
    echo "Runtime image:"
    docker images "${RUNTIME_IMAGE}" --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}' 2>/dev/null || true
    echo
    echo "Worker:"
    if is_worker_running; then
        ps -p "$(cat "${PIDFILE}")" -o pid,stat,command
    else
        echo "not running"
    fi
}

start_dependencies() {
    ensure_redis
    ensure_colima
    ensure_runtime_image
}

case "${1:-start}" in
    start)
        start_dependencies
        start_worker_background
        ;;
    deps)
        start_dependencies
        ;;
    worker)
        start_dependencies
        worker_env
        cd "${ROOT_DIR}"
        exec "$(find_python)" judge_worker.py
        ;;
    stop)
        stop_worker
        ;;
    restart)
        stop_worker
        start_dependencies
        start_worker_background
        ;;
    status)
        show_status
        ;;
    logs)
        tail -n 80 "${LOGFILE}" 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 {start|deps|worker|stop|restart|status|logs}"
        exit 1
        ;;
esac
