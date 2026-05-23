import base64
import json
import traceback
from pathlib import Path

import docker
from docker.errors import DockerException

from app import JudgeTask, JudgeTaskResult, app, db, now_utc8


def _judge_timeout_seconds(task):
    case_count = max(len(task.test_cases or []), 1)
    base_seconds = max(int(task.time_limit_ms / 1000), 1)
    return max((base_seconds * case_count) + 10, 15)


def _build_payload(task):
    return {
        "language": task.language,
        "source_code": task.source_code,
        "test_cases": task.test_cases or [],
        "time_limit_ms": task.time_limit_ms,
        "memory_limit_mb": task.memory_limit_mb,
    }


def _get_docker_client():
    configured_host = (app.config.get("JUDGE_DOCKER_HOST") or "").strip()
    if configured_host:
        client = docker.DockerClient(base_url=configured_host)
        client.ping()
        return client

    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as primary_error:
        colima_socket = Path.home() / ".colima" / "default" / "docker.sock"
        if colima_socket.exists():
            client = docker.DockerClient(base_url=f"unix://{colima_socket}")
            client.ping()
            return client
        raise primary_error


def _run_in_runtime_container(task):
    client = _get_docker_client()
    runtime_image = task.runtime_image or app.config["JUDGE_RUNTIME_IMAGE"]
    payload_json = json.dumps(_build_payload(task), ensure_ascii=False)
    payload_b64 = base64.b64encode(payload_json.encode("utf-8")).decode("ascii")

    container = client.containers.run(
        runtime_image,
        command=["python", "/runner/run_submission.py"],
        detach=True,
        remove=False,
        environment={
            "JUDGE_PAYLOAD_B64": payload_b64,
            "JUDGE_MAX_OUTPUT_BYTES": str(app.config["JUDGE_MAX_OUTPUT_BYTES"]),
        },
        network_disabled=not app.config["JUDGE_ALLOW_NETWORK"],
        mem_limit=f"{task.memory_limit_mb}m",
        nano_cpus=int(app.config["JUDGE_CONTAINER_CPUS"] * 1_000_000_000),
        pids_limit=app.config["JUDGE_CONTAINER_PIDS_LIMIT"],
        read_only=True,
        user="65534:65534",
        working_dir="/workspace",
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        tmpfs={
            "/tmp": "rw,noexec,nosuid,nodev,size=64m,uid=65534,gid=65534,mode=1777",
            "/workspace": "rw,exec,nosuid,nodev,size=128m,uid=65534,gid=65534,mode=1777",
        },
    )

    try:
        wait_result = container.wait(timeout=_judge_timeout_seconds(task))
        output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
        status_code = wait_result.get("StatusCode", 1)
        if status_code != 0:
            raise RuntimeError(output.strip() or f"Judge runtime exited with status {status_code}.")

        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Judge runtime returned invalid JSON: {output}") from exc
    finally:
        try:
            container.remove(force=True)
        except Exception:
            pass


def _persist_results(task, payload):
    JudgeTaskResult.query.filter_by(task_id=task.id).delete()

    results = payload.get("results", [])
    for item in results:
        db.session.add(
            JudgeTaskResult(
                task_id=task.id,
                case_index=item.get("case_index", 0),
                status=item.get("status", "system_error"),
                score=item.get("score", 0),
                time_ms=item.get("time_ms", 0),
                memory_kb=item.get("memory_kb", 0),
                input_data=item.get("input_data"),
                expected_output=item.get("expected_output"),
                actual_output=item.get("actual_output"),
                stderr_text=item.get("stderr_text"),
            )
        )

    task.total_count = len(results)
    task.passed_count = sum(1 for item in results if item.get("status") == "accepted")
    task.total_score = payload.get("total_score", 0)
    task.result_summary = payload
    task.error_message = payload.get("error_message")
    task.status = payload.get("status", "failed")
    task.finished_at = now_utc8()
    db.session.commit()


def process_judge_task(task_id):
    with app.app_context():
        task = JudgeTask.query.get(task_id)
        if task is None:
            return

        task.status = "running"
        task.started_at = now_utc8()
        task.finished_at = None
        task.error_message = None
        db.session.commit()

        try:
            result_payload = _run_in_runtime_container(task)
            _persist_results(task, result_payload)
        except Exception as exc:
            task.status = "system_error"
            task.finished_at = now_utc8()
            task.error_message = f"{exc}\n\n{traceback.format_exc()}"
            task.result_summary = {
                "status": "system_error",
                "error_message": str(exc),
            }
            db.session.commit()
