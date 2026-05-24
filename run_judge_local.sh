#!/usr/bin/env bash

[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${ROOT_DIR}/.wikibook-judge-worker.pid"
LOGFILE="${ROOT_DIR}/.wikibook-judge-worker.log"
PROXY_PIDFILE="${ROOT_DIR}/.wikibook-docker-proxy.pid"
PROXY_LOGFILE="${ROOT_DIR}/.wikibook-docker-proxy.log"
RUNTIME_IMAGE="${JUDGE_RUNTIME_IMAGE:-wikibook-judge-runtime:latest}"
DOCKER_PROXY_PORT="${JUDGE_DOCKER_PROXY_PORT:-23750}"

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
    if [ -z "${JUDGE_DOCKER_HOST:-}" ]; then
        export JUDGE_DOCKER_HOST="tcp://127.0.0.1:${DOCKER_PROXY_PORT}"
    fi
}

proxy_is_running() {
    [ -f "${PROXY_PIDFILE}" ] && kill -0 "$(cat "${PROXY_PIDFILE}")" 2>/dev/null
}

proxy_pid_from_port() {
    lsof -tiTCP:"${DOCKER_PROXY_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
}

proxy_is_healthy() {
    [ "$(curl -s --max-time 2 "http://127.0.0.1:${DOCKER_PROXY_PORT}/_ping" 2>/dev/null || true)" = "OK" ]
}

wait_for_docker() {
    local attempts="${1:-30}"
    local waited=0
    while [ "${waited}" -lt "${attempts}" ]; do
        if docker info >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    return 1
}

stop_proxy_pid() {
    local pid="${1:-}"
    [ -n "${pid}" ] || return 0

    kill "${pid}" 2>/dev/null || true

    local waited=0
    while kill -0 "${pid}" 2>/dev/null; do
        if [ "${waited}" -ge 5 ]; then
            kill -9 "${pid}" 2>/dev/null || true
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done
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

    if wait_for_docker 45; then
        echo "Colima started and Docker is ready."
        return 0
    fi

    echo "Colima is running, but Docker did not become reachable."
    echo "Try: colima restart"
    exit 1
}

ensure_docker_proxy() {
    if [ -n "${JUDGE_DOCKER_HOST:-}" ] && [ "${JUDGE_DOCKER_HOST}" != "tcp://127.0.0.1:${DOCKER_PROXY_PORT}" ]; then
        echo "Using custom JUDGE_DOCKER_HOST=${JUDGE_DOCKER_HOST}; skipping local Docker proxy."
        return 0
    fi

    if proxy_is_healthy; then
        local running_pid
        running_pid="$(proxy_pid_from_port)"
        if [ -n "${running_pid}" ]; then
            echo "${running_pid}" > "${PROXY_PIDFILE}"
        fi
        echo "Restricted Docker proxy is running at tcp://127.0.0.1:${DOCKER_PROXY_PORT}."
        return 0
    fi

    rm -f "${PROXY_PIDFILE}"

    local stale_pid
    stale_pid="$(proxy_pid_from_port)"
    if [ -n "${stale_pid}" ]; then
        echo "Stopping unhealthy Docker proxy on port ${DOCKER_PROXY_PORT} (PID: ${stale_pid})."
        stop_proxy_pid "${stale_pid}"
    fi

    local python_bin
    python_bin="$(find_python)" || {
        echo "Unable to find Python for the Docker proxy."
        exit 1
    }

    echo "Starting restricted Docker proxy at tcp://127.0.0.1:${DOCKER_PROXY_PORT} ..."
    : > "${PROXY_LOGFILE}"
    nohup env JUDGE_DOCKER_PROXY_PORT="${DOCKER_PROXY_PORT}" "${python_bin}" "${ROOT_DIR}/judge_docker_proxy.py" --host 127.0.0.1 --port "${DOCKER_PROXY_PORT}" >> "${PROXY_LOGFILE}" 2>&1 &
    echo $! > "${PROXY_PIDFILE}"

    sleep 1
    if proxy_is_healthy; then
        local running_pid
        running_pid="$(proxy_pid_from_port)"
        if [ -n "${running_pid}" ]; then
            echo "${running_pid}" > "${PROXY_PIDFILE}"
        fi
        echo "Restricted Docker proxy started."
        return 0
    fi

    echo "Restricted Docker proxy failed to start."
    tail -n 80 "${PROXY_LOGFILE}" 2>/dev/null || true
    exit 1
}

ensure_runtime_image() {
    if docker image inspect "${RUNTIME_IMAGE}" >/dev/null 2>&1; then
        echo "Judge runtime image exists: ${RUNTIME_IMAGE}"
        return 0
    fi

    docker build -t "${RUNTIME_IMAGE}" -f "${ROOT_DIR}/judge_runtime/Dockerfile" "${ROOT_DIR}"
    echo "Judge runtime image built: ${RUNTIME_IMAGE}"
}

stop_docker_proxy() {
    if [ -n "${JUDGE_DOCKER_HOST:-}" ] && [ "${JUDGE_DOCKER_HOST}" != "tcp://127.0.0.1:${DOCKER_PROXY_PORT}" ]; then
        return 0
    fi

    local pid
    pid="$(cat "${PROXY_PIDFILE}" 2>/dev/null || true)"
    if [ -z "${pid}" ] || ! kill -0 "${pid}" 2>/dev/null; then
        pid="$(proxy_pid_from_port)"
    fi
    if [ -z "${pid}" ]; then
        rm -f "${PROXY_PIDFILE}"
        return 0
    fi
    stop_proxy_pid "${pid}"

    rm -f "${PROXY_PIDFILE}"
    echo "Restricted Docker proxy stopped."
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
    worker_env
    echo "Redis:"
    redis-cli ping 2>/dev/null || true
    echo
    echo "Docker:"
    docker info --format 'server={{.ServerVersion}} os={{.OperatingSystem}} arch={{.Architecture}}' 2>/dev/null || true
    echo "Docker host: ${JUDGE_DOCKER_HOST}"
    echo -n "Docker proxy: "
    if proxy_is_healthy; then
        local running_pid
        running_pid="$(proxy_pid_from_port)"
        if [ -n "${running_pid}" ]; then
            echo "${running_pid}" > "${PROXY_PIDFILE}"
            echo "running (PID: ${running_pid})"
        else
            echo "running"
        fi
    else
        echo "stopped"
    fi
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
    ensure_docker_proxy
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
        worker_env
        stop_docker_proxy
        ;;
    restart)
        stop_worker
        worker_env
        stop_docker_proxy
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
