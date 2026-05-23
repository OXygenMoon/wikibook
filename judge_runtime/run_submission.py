import base64
import json
import os
import subprocess
import tempfile
import time


PYTHON_SECURITY_EXIT_CODE = 40
DEFAULT_MAX_OUTPUT_BYTES = 65536

LANGUAGE_CONFIG = {
    "python": {
        "source_file": "main.py",
        "compile": None,
        "run": ["python3", "-I", "/runner/python_sandbox.py", "main.py"],
    },
    "c": {
        "source_file": "main.c",
        "compile": ["gcc", "main.c", "-O2", "-std=c11", "-o", "main"],
        "run": ["./main"],
    },
    "cpp": {
        "source_file": "main.cpp",
        "compile": ["g++", "main.cpp", "-O2", "-std=c++17", "-o", "main"],
        "run": ["./main"],
    },
}


def build_process_env():
    return {
        "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "HOME": "/tmp",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONHASHSEED": "0",
    }


def get_max_output_bytes():
    raw_value = os.environ.get("JUDGE_MAX_OUTPUT_BYTES", str(DEFAULT_MAX_OUTPUT_BYTES))
    try:
        return max(int(raw_value), 1024)
    except ValueError:
        return DEFAULT_MAX_OUTPUT_BYTES


def read_limited_text(file_obj, max_output_bytes):
    file_obj.flush()
    file_obj.seek(0, os.SEEK_END)
    total_bytes = file_obj.tell()
    file_obj.seek(0)

    chunk = file_obj.read(max_output_bytes)
    text = chunk.decode("utf-8", errors="replace")
    truncated = total_bytes > max_output_bytes
    if truncated:
        omitted_bytes = max(total_bytes - len(chunk), 0)
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"...[truncated {omitted_bytes} bytes]"

    return text, truncated


def execute_command(command, workdir, env, max_output_bytes, input_text=None, timeout=None):
    stdin_data = None if input_text is None else input_text.encode("utf-8")

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        proc = subprocess.Popen(
            command,
            cwd=workdir,
            env=env,
            stdin=subprocess.PIPE if stdin_data is not None else None,
            stdout=stdout_file,
            stderr=stderr_file,
        )

        timed_out = False
        try:
            proc.communicate(input=stdin_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.communicate()

        stdout_text, stdout_truncated = read_limited_text(stdout_file, max_output_bytes)
        stderr_text, stderr_truncated = read_limited_text(stderr_file, max_output_bytes)
        return {
            "returncode": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "timed_out": timed_out,
        }


def normalize_output(output_text):
    if output_text is None:
        return ""
    normalized = output_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def load_payload():
    payload_b64 = os.environ.get("JUDGE_PAYLOAD_B64", "")
    if not payload_b64:
        raise RuntimeError("Missing JUDGE_PAYLOAD_B64 payload.")
    return json.loads(base64.b64decode(payload_b64).decode("utf-8"))


def compile_if_needed(language, workdir, max_output_bytes):
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return False, f"Unsupported language: {language}"

    if config["compile"] is None:
        return True, ""

    compile_result = execute_command(
        config["compile"],
        workdir,
        build_process_env(),
        max_output_bytes,
        timeout=30,
    )
    if compile_result["timed_out"]:
        return False, "Compilation timed out after 30 seconds."
    if compile_result["returncode"] != 0:
        return False, (
            compile_result["stderr"] or compile_result["stdout"] or "Compilation failed."
        ).strip()
    return True, ""


def run_case(run_command, workdir, input_data, expected_output, score, time_limit_ms, max_output_bytes):
    started_at = time.perf_counter()
    run_result = execute_command(
        run_command,
        workdir,
        build_process_env(),
        max_output_bytes,
        input_text=input_data or "",
        timeout=max(time_limit_ms / 1000.0, 0.1),
    )
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)

    if run_result["timed_out"]:
        return {
            "status": "time_limit_exceeded",
            "score": 0,
            "time_ms": elapsed_ms,
            "memory_kb": 0,
            "actual_output": run_result["stdout"],
            "stderr_text": run_result["stderr"],
        }

    if run_result["returncode"] != 0:
        if run_result["returncode"] == PYTHON_SECURITY_EXIT_CODE:
            return {
                "status": "security_violation",
                "score": 0,
                "time_ms": elapsed_ms,
                "memory_kb": 0,
                "actual_output": run_result["stdout"],
                "stderr_text": run_result["stderr"],
            }
        return {
            "status": "runtime_error",
            "score": 0,
            "time_ms": elapsed_ms,
            "memory_kb": 0,
            "actual_output": run_result["stdout"],
            "stderr_text": run_result["stderr"],
        }

    actual_output = run_result["stdout"] or ""
    if (
        not run_result["stdout_truncated"]
        and normalize_output(actual_output) == normalize_output(expected_output or "")
    ):
        return {
            "status": "accepted",
            "score": score,
            "time_ms": elapsed_ms,
            "memory_kb": 0,
            "actual_output": actual_output,
            "stderr_text": run_result["stderr"],
        }

    return {
        "status": "wrong_answer",
        "score": 0,
        "time_ms": elapsed_ms,
        "memory_kb": 0,
        "actual_output": actual_output,
        "stderr_text": run_result["stderr"],
    }


def build_result_payload(language, source_code, test_cases, time_limit_ms):
    max_output_bytes = get_max_output_bytes()
    with tempfile.TemporaryDirectory(dir="/workspace") as workdir:
        language_config = LANGUAGE_CONFIG.get(language)
        if not language_config:
            return {
                "status": "failed",
                "total_score": 0,
                "results": [],
                "error_message": f"Unsupported language: {language}",
            }

        source_path = os.path.join(workdir, language_config["source_file"])
        with open(source_path, "w", encoding="utf-8") as source_file:
            source_file.write(source_code)

        compiled, compile_error = compile_if_needed(language, workdir, max_output_bytes)
        if not compiled:
            return {
                "status": "failed",
                "total_score": 0,
                "results": [],
                "error_message": compile_error,
                "failure_reason": "compile_error",
            }

        results = []
        total_score = 0
        for index, test_case in enumerate(test_cases):
            case_score = int(test_case.get("score", 1))
            case_result = run_case(
                language_config["run"],
                workdir,
                test_case.get("input", ""),
                test_case.get("expected_output", ""),
                case_score,
                time_limit_ms,
                max_output_bytes,
            )
            case_result.update(
                {
                    "case_index": index,
                    "input_data": test_case.get("input"),
                    "expected_output": test_case.get("expected_output"),
                }
            )
            total_score += case_result["score"]
            results.append(case_result)

        all_accepted = bool(results) and all(item["status"] == "accepted" for item in results)
        return {
            "status": "accepted" if all_accepted else "failed",
            "total_score": total_score,
            "results": results,
            "error_message": None,
        }


def main():
    try:
        payload = load_payload()
        response = build_result_payload(
            payload["language"],
            payload["source_code"],
            payload.get("test_cases", []),
            int(payload.get("time_limit_ms", 2000)),
        )
    except Exception as exc:
        response = {
            "status": "system_error",
            "total_score": 0,
            "results": [],
            "error_message": str(exc),
        }

    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
