import ast
from dataclasses import dataclass


SAFE_PYTHON_MODULES = {
    "array",
    "bisect",
    "collections",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "fractions",
    "functools",
    "heapq",
    "itertools",
    "json",
    "math",
    "operator",
    "queue",
    "random",
    "re",
    "statistics",
    "string",
    "sys",
    "time",
    "typing",
}

BLOCKED_CALL_NAMES = {
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

ALLOWED_DUNDER_NAMES = {"__name__"}


@dataclass(frozen=True)
class SecurityViolation:
    line: int
    column: int
    message: str


class PythonSecurityValidator(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def add_violation(self, node, message):
        self.violations.append(
            SecurityViolation(
                line=getattr(node, "lineno", 1) or 1,
                column=max((getattr(node, "col_offset", 0) or 0), 0),
                message=message,
            )
        )

    def visit_Import(self, node):
        for alias in node.names:
            module_name = (alias.name or "").strip()
            root_name = module_name.split(".", 1)[0]
            if root_name not in SAFE_PYTHON_MODULES:
                self.add_violation(node, f"禁止导入模块：{module_name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.level:
            self.add_violation(node, "禁止使用相对导入。")
            return

        module_name = (node.module or "").strip()
        root_name = module_name.split(".", 1)[0]
        if root_name not in SAFE_PYTHON_MODULES:
            self.add_violation(node, f"禁止导入模块：{module_name or '<unknown>'}")
        for alias in node.names:
            if alias.name == "*":
                self.add_violation(node, "禁止使用通配符导入。")
            elif alias.name.startswith("_"):
                self.add_violation(node, f"禁止导入受保护属性：{alias.name}")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id.startswith("__") and node.id not in ALLOWED_DUNDER_NAMES:
            self.add_violation(node, f"禁止访问敏感名称：{node.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if (node.attr or "").startswith("_"):
            self.add_violation(node, f"禁止访问受保护属性：{node.attr}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALL_NAMES:
            self.add_violation(node, f"禁止调用危险函数：{node.func.id}")
        self.generic_visit(node)


def validate_python_source(source_code):
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        line = exc.lineno or 1
        column = max((exc.offset or 1) - 1, 0)
        return False, [
            SecurityViolation(
                line=line,
                column=column,
                message=exc.msg or "Python 语法错误",
            )
        ]

    validator = PythonSecurityValidator()
    validator.visit(tree)
    return len(validator.violations) == 0, validator.violations


def violations_to_diagnostics(violations):
    return [
        {
            "row": max(item.line - 1, 0),
            "column": item.column,
            "text": item.message,
            "type": "error",
        }
        for item in violations
    ]


def first_violation_message(violations, fallback):
    if not violations:
        return fallback
    first = violations[0]
    return f"第 {first.line} 行：{first.message}"
