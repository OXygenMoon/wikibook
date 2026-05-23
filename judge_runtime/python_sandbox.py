import builtins
import sys
import types
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
for candidate in (CURRENT_DIR, PARENT_DIR):
    candidate_path = str(candidate)
    if candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

from judge_security import SAFE_PYTHON_MODULES, validate_python_source


SECURITY_EXIT_CODE = 40
BLOCKED_BUILTINS = {
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "locals",
    "open",
    "setattr",
    "vars",
}
ALLOWED_BUILTIN_DUNDERS = {"__build_class__"}
ORIGINAL_IMPORT = builtins.__import__
ORIGINAL_COMPILE = builtins.compile
SAFE_SYS_MODULE = None


def _preload_safe_modules():
    for module_name in sorted(SAFE_PYTHON_MODULES - {"sys"}):
        ORIGINAL_IMPORT(module_name)


def _blocked_builtin(name):
    def _raiser(*args, **kwargs):
        raise PermissionError(f"禁止调用危险函数：{name}")

    return _raiser


def _build_safe_sys_module():
    safe_sys = types.ModuleType("sys")
    safe_sys.stdin = sys.stdin
    safe_sys.stdout = sys.stdout
    safe_sys.stderr = sys.stderr
    safe_sys.argv = ["main.py"]
    safe_sys.maxsize = sys.maxsize

    def getrecursionlimit():
        return sys.getrecursionlimit()

    def setrecursionlimit(limit):
        if not isinstance(limit, int):
            raise TypeError("递归深度必须是整数。")
        if limit < 1 or limit > 10**6:
            raise ValueError("递归深度超出允许范围。")
        return sys.setrecursionlimit(limit)

    safe_sys.getrecursionlimit = getrecursionlimit
    safe_sys.setrecursionlimit = setrecursionlimit
    safe_sys.exit = sys.exit
    return safe_sys


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0:
        raise ImportError("禁止使用相对导入。")

    root_name = (name or "").split(".", 1)[0]
    if root_name not in SAFE_PYTHON_MODULES:
        raise ImportError(f"禁止导入模块：{name}")
    if root_name == "sys":
        return SAFE_SYS_MODULE

    return ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


def _build_safe_builtins():
    safe_builtins = {}
    for name in dir(builtins):
        if name in BLOCKED_BUILTINS:
            safe_builtins[name] = _blocked_builtin(name)
            continue

        if name.startswith("__") and name not in ALLOWED_BUILTIN_DUNDERS:
            continue

        safe_builtins[name] = getattr(builtins, name)

    safe_builtins["__import__"] = _guarded_import
    return safe_builtins


def _load_source_code(source_path):
    return Path(source_path).read_text(encoding="utf-8")


def _report_security_error(message):
    print(message, file=sys.stderr)
    raise SystemExit(SECURITY_EXIT_CODE)


def main():
    if len(sys.argv) != 2:
        _report_security_error("缺少待执行的 Python 源码路径。")

    source_path = sys.argv[1]
    source_code = _load_source_code(source_path)
    is_safe, violations = validate_python_source(source_code)
    if not is_safe:
        joined = "\n".join(f"Line {item.line}: {item.message}" for item in violations)
        _report_security_error(joined or "Python 代码未通过安全检查。")

    _preload_safe_modules()

    global SAFE_SYS_MODULE
    SAFE_SYS_MODULE = _build_safe_sys_module()
    safe_globals = {
        "__builtins__": _build_safe_builtins(),
        "__name__": "__main__",
    }
    code = ORIGINAL_COMPILE(source_code, source_path, "exec", dont_inherit=True)
    exec(code, safe_globals, None)


if __name__ == "__main__":
    main()
