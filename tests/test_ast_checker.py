import unittest

from utils.ast_checker import check_ast_rules, get_default_ast_rule_templates


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

    def test_forbid_variable_rule(self):
        failed = check_ast_rules(
            'tmp = 1\nprint(tmp)\n',
            [make_rule("forbid_variable", "variable", params={"variable_name": "tmp"})],
        )
        passed = check_ast_rules(
            'score = 1\nprint(score)\n',
            [make_rule("forbid_variable", "variable", params={"variable_name": "tmp"})],
        )
        self.assertFalse(failed["passed"])
        self.assertTrue(passed["passed"])

    def test_forbid_function_rule(self):
        failed = check_ast_rules(
            'print("Hello")\n',
            [make_rule("forbid_function", "function", params={"function_name": "print"})],
        )
        passed = check_ast_rules(
            'name = "Hello"\nvalue = len(name)\n',
            [make_rule("forbid_function", "function", params={"function_name": "print"})],
        )
        self.assertFalse(failed["passed"])
        self.assertTrue(passed["passed"])

    def test_forbid_method_rule(self):
        failed = check_ast_rules(
            'nums = []\nnums.append(1)\n',
            [make_rule("forbid_method", "method", params={"method_name": "append"})],
        )
        passed = check_ast_rules(
            'nums = [1, 2, 3]\nprint(nums[0])\n',
            [make_rule("forbid_method", "method", params={"method_name": "append"})],
        )
        self.assertFalse(failed["passed"])
        self.assertTrue(passed["passed"])

    def test_exact_for_count_rule(self):
        passed = check_ast_rules(
            'for i in range(3):\n    print(i)\nfor j in range(2):\n    print(j)\n',
            [make_rule("syntax_node", "For", min_count=2, max_count=2)],
        )
        failed = check_ast_rules(
            'for i in range(3):\n    print(i)\n',
            [make_rule("syntax_node", "For", min_count=2, max_count=2)],
        )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_parallel_assignment_rule(self):
        passed = check_ast_rules(
            'a, b = map(int, input().split())\nprint(a + b)\n',
            [make_rule("parallel_assignment", "parallel", min_count=1)],
        )
        failed = check_ast_rules(
            'a = int(input())\nb = int(input())\nprint(a + b)\n',
            [make_rule("parallel_assignment", "parallel", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertEqual(passed["stats"]["parallel_assignment_count"], 1)
        self.assertFalse(failed["passed"])

    def test_chain_assignment_rule(self):
        result = check_ast_rules(
            'left = right = 0\nprint(left + right)\n',
            [make_rule("chain_assignment", "chain", min_count=1)],
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["stats"]["chain_assignment_count"], 1)

    def test_swap_assignment_rule(self):
        result = check_ast_rules(
            'a = 1\nb = 2\na, b = b, a\nprint(a, b)\n',
            [make_rule("swap_assignment", "swap", min_count=1)],
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["stats"]["swap_assignment_count"], 1)

    def test_nested_for_rule(self):
        passed = check_ast_rules(
            'for row in grid:\n    for cell in row:\n        print(cell)\n',
            [make_rule("nested_for", "nested_for", min_count=1)],
        )
        failed = check_ast_rules(
            'for row in grid:\n    print(row)\n',
            [make_rule("nested_for", "nested_for", min_count=1)],
        )
        self.assertTrue(passed["passed"])
        self.assertEqual(passed["stats"]["nested_for_count"], 1)
        self.assertFalse(failed["passed"])

    def test_extended_templates_registered(self):
        codes = {template["code"] for template in get_default_ast_rule_templates()}
        self.assertIn("exact_for_count", codes)
        self.assertIn("require_parallel_assign", codes)
        self.assertIn("require_nested_for", codes)
        self.assertIn("forbid_specific_function", codes)
        self.assertIn("forbid_specific_method", codes)


if __name__ == "__main__":
    unittest.main()
