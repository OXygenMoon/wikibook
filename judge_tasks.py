import base64
import json
import traceback
from pathlib import Path

import docker
from docker.errors import DockerException

from app import JudgeTask, JudgeTaskResult, app, db, now_utc8
from utils.ast_checker import check_ast_rules


def _normalize_output_text(value):
    if value is None:
        return ""
    normalized = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


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
    if task.status == "accepted":
        ast_result = _evaluate_ast_result(task)
        task.result_summary = {**payload, "ast_result": ast_result}
        task.status = "PAC" if ast_result.get("passed") else "AC"
    task.finished_at = now_utc8()
    db.session.commit()


def _evaluate_ast_result(task):
    enabled_rules = []
    if task.problem and task.problem.ast_check_enabled:
        public_sample_outputs = [
            _normalize_output_text(case.expected_output)
            for case in task.problem.sample_cases
            if _normalize_output_text(case.expected_output)
        ]
        all_problem_outputs = [
            _normalize_output_text(case.expected_output)
            for case in task.problem.test_cases
            if _normalize_output_text(case.expected_output)
        ]
        enabled_rules = [
            {
                "id": rule.id,
                "rule_type": rule.rule_type,
                "target": rule.target,
                "min_count": rule.min_count,
                "max_count": rule.max_count,
                "required_value": rule.required_value,
                "params": {
                    **(rule.params or {}),
                    "public_sample_outputs": public_sample_outputs,
                    "problem_outputs": all_problem_outputs,
                    "forbidden_outputs": (
                        public_sample_outputs
                        if (rule.params or {}).get("match_source") == "public_sample_outputs"
                        else all_problem_outputs
                    ),
                },
                "description": rule.description,
                "fail_message": rule.fail_message,
                "enabled": bool(rule.enabled),
            }
            for rule in task.problem.ast_rules
            if rule.enabled
        ]
    has_rules = bool(enabled_rules)
    if not has_rules:
        return {"applied": False, "has_rules": False, "passed": True, "failed_rules": [], "stats": {}}

    if task.language != "python":
        return {
            "applied": True,
            "has_rules": True,
            "passed": False,
            "failed_rules": [
                {
                    "rule_id": None,
                    "description": "当前题目配置了 Python AST 满星目标",
                    "message": "当前满星语法检查仅支持 Python 代码，请使用 Python 提交以冲击满星通过。",
                }
            ],
            "stats": {},
        }

    result = check_ast_rules(task.source_code, enabled_rules)
    result["applied"] = True
    result["has_rules"] = True
    return result


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
