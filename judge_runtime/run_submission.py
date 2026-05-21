import base64
import json
import os
import subprocess
import tempfile
import time


LANGUAGE_CONFIG = {
    "python": {
        "source_file": "main.py",
        "compile": None,
        "run": ["python3", "main.py"],
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


def compile_if_needed(language, workdir):
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return False, f"Unsupported language: {language}"

    if config["compile"] is None:
        return True, ""

    compile_proc = subprocess.run(
        config["compile"],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if compile_proc.returncode != 0:
        return False, (compile_proc.stderr or compile_proc.stdout or "Compilation failed.").strip()
    return True, ""


def run_case(run_command, workdir, input_data, expected_output, score, time_limit_ms):
    started_at = time.perf_counter()
    try:
        proc = subprocess.run(
            run_command,
            cwd=workdir,
            input=input_data or "",
            text=True,
            capture_output=True,
            timeout=max(time_limit_ms / 1000.0, 0.1),
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)

        if proc.returncode != 0:
            return {
                "status": "runtime_error",
                "score": 0,
                "time_ms": elapsed_ms,
                "memory_kb": 0,
                "actual_output": proc.stdout,
                "stderr_text": proc.stderr,
            }

        actual_output = proc.stdout or ""
        if normalize_output(actual_output) == normalize_output(expected_output or ""):
            return {
                "status": "accepted",
                "score": score,
                "time_ms": elapsed_ms,
                "memory_kb": 0,
                "actual_output": actual_output,
                "stderr_text": proc.stderr,
            }

        return {
            "status": "wrong_answer",
            "score": 0,
            "time_ms": elapsed_ms,
            "memory_kb": 0,
            "actual_output": actual_output,
            "stderr_text": proc.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "status": "time_limit_exceeded",
            "score": 0,
            "time_ms": elapsed_ms,
            "memory_kb": 0,
            "actual_output": exc.stdout or "",
            "stderr_text": exc.stderr or "",
        }


def build_result_payload(language, source_code, test_cases, time_limit_ms):
    with tempfile.TemporaryDirectory(dir="/tmp") as workdir:
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

        compiled, compile_error = compile_if_needed(language, workdir)
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
