import unittest

from utils.ast_checker import check_ast_rules


def make_rule(rule_type, target, **extra):
    rule = {
        "id": extra.pop("id", 1),
        "rule_type": rule_type,
        "target": target,
        "description": extra.pop("description", "rule"),
        "fail_message": extra.pop("fail_message", "rule"),
        "enabled": True,
    }
    rule.update(extra)
    return rule


class AstCheckerTestCase(unittest.TestCase):
    def test_no_rules_passes(self):
        self.assertTrue(check_ast_rules('print("Hello")', [])["passed"])

    def test_min_print_calls_passes(self):
        result = check_ast_rules(
            'print("A")\nprint("B")\nprint("C")\n',
            [make_rule("function_call", "print", min_count=3)],
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["stats"]["function_calls"]["print"], 3)

    def test_min_print_calls_fails(self):
        result = check_ast_rules(
            'print("A\\nB\\nC")\n',
            [make_rule("function_call", "print", min_count=3)],
        )
        self.assertFalse(result["passed"])

    def test_max_input_calls(self):
        result = check_ast_rules(
            'a = input()\nb = input()\n',
            [make_rule("function_call", "input", max_count=1)],
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["stats"]["function_calls"]["input"], 2)

    def test_if_else_passes(self):
        result = check_ast_rules(
            'x = int(input())\nif x >= 60:\n    print("及格")\nelse:\n    print("不及格")\n',
            [
                make_rule("syntax_node", "If", min_count=1),
                make_rule("branch_feature", "else", min_count=1, id=2),
            ],
        )
        self.assertTrue(result["passed"])

    def test_if_without_else_fails(self):
        result = check_ast_rules(
            'x = int(input())\nif x >= 60:\n    print("及格")\nif x < 60:\n    print("不及格")\n',
            [
                make_rule("syntax_node", "If", min_count=1),
                make_rule("branch_feature", "else", min_count=1, id=2),
            ],
        )
        self.assertFalse(result["passed"])

    def test_variable_assignment_rule(self):
        passed = check_ast_rules(
            'name = "小码"\nprint(name)\n',
            [make_rule("assign", "assign", min_count=1)],
        )
        failed = check_ast_rules(
            'print("小码")\n',
            [make_rule("assign", "assign", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_mod_operator_rule(self):
        passed = check_ast_rules(
            'n = int(input())\nif n % 2 == 0:\n    print("偶数")\nelse:\n    print("奇数")\n',
            [make_rule("operator", "Mod", min_count=1)],
        )
        failed = check_ast_rules(
            'n = int(input())\nprint("偶数" if n in [0, 2, 4, 6, 8] else "奇数")\n',
            [make_rule("operator", "Mod", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_and_operator_rule(self):
        result = check_ast_rules(
            'score = int(input())\nif score >= 60 and score <= 100:\n    print("通过")\nelse:\n    print("未通过")\n',
            [make_rule("bool_operator", "And", min_count=1)],
        )
        self.assertTrue(result["passed"])

    def test_chained_compare_rule(self):
        passed = check_ast_rules(
            'score = int(input())\nif 60 <= score < 90:\n    print("合格")\nelse:\n    print("其他")\n',
            [make_rule("chained_compare", "chain", min_count=1)],
        )
        failed = check_ast_rules(
            'score = int(input())\nif score >= 60 and score < 90:\n    print("合格")\nelse:\n    print("其他")\n',
            [make_rule("chained_compare", "chain", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_f_string_rule(self):
        passed = check_ast_rules(
            'name = input()\nprint(f"你好，{name}")\n',
            [make_rule("f_string", "JoinedStr", min_count=1)],
        )
        failed = check_ast_rules(
            'name = input()\nprint("你好，" + name)\n',
            [make_rule("f_string", "JoinedStr", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_append_rule(self):
        result = check_ast_rules(
            'nums = []\nnums.append(1)\nprint(nums[0])\n',
            [make_rule("method_call", "append", min_count=1)],
        )
        self.assertTrue(result["passed"])

    def test_function_return_rule(self):
        passed = check_ast_rules(
            'def add(a, b):\n    return a + b\n\nprint(add(1, 2))\n',
            [
                make_rule("function_def", "FunctionDef", min_count=1),
                make_rule("return_required", "FunctionDef", min_count=1, id=2),
            ],
        )
        failed = check_ast_rules(
            'def add(a, b):\n    print(a + b)\n\nadd(1, 2)\n',
            [
                make_rule("function_def", "FunctionDef", min_count=1),
                make_rule("return_required", "FunctionDef", min_count=1, id=2),
            ],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_try_except_and_valueerror_rule(self):
        result = check_ast_rules(
            'try:\n    n = int(input())\n    print(n)\nexcept ValueError:\n    print("输入错误")\n',
            [
                make_rule("try_except", "try", min_count=1),
                make_rule("exception_handler", "ValueError", id=2, params={"exception_name": "ValueError"}),
            ],
        )
        self.assertTrue(result["passed"])

    def test_forbid_literal_output(self):
        failed = check_ast_rules(
            'print("25-03-001")\n',
            [
                make_rule(
                    "forbid_literal_output",
                    "answer",
                    params={"forbidden_outputs": ["25-03-001"]},
                )
            ],
        )
        passed = check_ast_rules(
            'print("25", "03", "001", sep="-")\n',
            [
                make_rule(
                    "forbid_literal_output",
                    "answer",
                    params={"forbidden_outputs": ["25-03-001"]},
                )
            ],
        )
        self.assertFalse(failed["passed"])
        self.assertTrue(passed["passed"])


if __name__ == "__main__":
    unittest.main()
