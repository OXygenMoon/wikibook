import ast
import copy
import json


SUPPORTED_AST_RULE_TYPES = {
    "assign",
    "assign_count",
    "bool_operator",
    "branch_feature",
    "chain_assignment",
    "chained_compare",
    "compare_operator",
    "default_args",
    "dict_call",
    "dict_literal",
    "exception_handler",
    "f_string",
    "forbid",
    "forbid_literal_output",
    "forbid_variable",
    "format_method",
    "format_spec",
    "function_args_count",
    "function_call",
    "function_def",
    "function_def_name",
    "import_forbid",
    "import_from_forbid",
    "import_from_required",
    "import_required",
    "iterate_collection",
    "keyword_arg",
    "list_call",
    "list_comprehension",
    "list_literal",
    "method_call",
    "open_mode",
    "operator",
    "parallel_assignment",
    "percent_format",
    "print_arg_count",
    "required_variable",
    "return_required",
    "set_call",
    "set_literal",
    "slice",
    "swap_assignment",
    "subscript",
    "syntax_node",
    "try_except",
    "unary_operator",
    "with_open",
    "with_statement",
    "aug_assign_operator",
    "nested_for",
}


NODE_LABELS = {
    "If": "if 分支结构",
    "For": "for 循环",
    "While": "while 循环",
    "FunctionDef": "函数定义",
    "Return": "return",
    "Break": "break",
    "Continue": "continue",
    "Try": "try",
    "With": "with",
}


METHOD_LABELS = {
    "append": "append()",
    "insert": "insert()",
    "pop": "pop()",
    "sort": "sort()",
    "split": "split()",
    "join": "join()",
    "strip": "strip()",
    "replace": "replace()",
    "find": "find()",
    "count": "count()",
    "upper": "upper()",
    "lower": "lower()",
    "startswith": "startswith()",
    "endswith": "endswith()",
    "remove": "remove()",
    "get": "get()",
    "keys": "keys()",
    "values": "values()",
    "items": "items()",
    "read": "read()",
    "readline": "readline()",
    "readlines": "readlines()",
    "write": "write()",
    "format": "format()",
}


FORBID_LABELS = {
    "import": "import",
    "eval": "eval()",
    "exec": "exec()",
    "open": "open()",
    "os": "os 模块",
    "subprocess": "subprocess 模块",
}


OPERATOR_LABELS = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "//",
    "Mod": "%",
    "Pow": "**",
    "BitAnd": "&",
    "BitOr": "|",
}


COMPARE_LABELS = {
    "Eq": "==",
    "NotEq": "!=",
    "Gt": ">",
    "GtE": ">=",
    "Lt": "<",
    "LtE": "<=",
}


BOOL_LABELS = {
    "And": "and",
    "Or": "or",
}


UNARY_LABELS = {
    "Not": "not",
}


PARAM_METADATA_KEYS = {
    "editable_fields",
    "field_labels",
    "field_types",
    "min_count",
    "max_count",
    "required_value",
}


def _template(code, name, category, rule_type, target="", default_params=None, description="", enabled=True):
    return {
        "code": code,
        "name": name,
        "category": category,
        "rule_type": rule_type,
        "target": target,
        "description": description,
        "default_params": default_params or {},
        "enabled": enabled,
    }


def _range_rule_templates(prefix, category, rule_type, target, singular_name):
    return [
        _template(
            f"require_{prefix}",
            f"必须使用 {singular_name}",
            category,
            rule_type,
            target,
            {"min_count": 1, "editable_fields": []},
        ),
        _template(
            f"min_{prefix}_count",
            f"{singular_name} 至少出现 N 次",
            category,
            rule_type,
            target,
            {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}},
        ),
        _template(
            f"max_{prefix}_count",
            f"{singular_name} 至多出现 N 次",
            category,
            rule_type,
            target,
            {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}},
        ),
    ]


def _exact_count_template(code, name, category, rule_type, target, exact_count=2):
    return _template(
        code,
        name,
        category,
        rule_type,
        target,
        {
            "min_count": exact_count,
            "max_count": exact_count,
            "exact_count": exact_count,
            "editable_fields": ["exact_count"],
            "field_labels": {"exact_count": "精确次数"},
            "field_types": {"exact_count": "number"},
        },
    )


def _call_rule_templates(prefix, category, target):
    return [
        _template(
            f"call_{prefix}",
            f"必须调用 {target}()",
            category,
            "function_call",
            target,
            {"min_count": 1, "editable_fields": []},
        ),
        _template(
            f"min_{prefix}_calls",
            f"{target} 调用次数至少 N 次",
            category,
            "function_call",
            target,
            {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}},
        ),
        _template(
            f"max_{prefix}_calls",
            f"{target} 调用次数至多 N 次",
            category,
            "function_call",
            target,
            {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}},
        ),
    ]


def _method_rule_templates(prefix, category, target):
    return [
        _template(
            f"require_{prefix}",
            f"必须使用 {target}()",
            category,
            "method_call",
            target,
            {"min_count": 1, "editable_fields": []},
        )
    ]


def _operator_rule(code, name, symbol_name, category="运算符"):
    return _template(code, name, category, "operator", symbol_name, {"min_count": 1, "editable_fields": []})


def _build_default_templates():
    rows = []

    rows.extend(_call_rule_templates("print", "输出函数", "print"))
    rows.extend(_call_rule_templates("input", "输入函数", "input"))
    rows.extend(
        [
            _template("call_int", "必须调用 int()", "输入函数", "function_call", "int", {"min_count": 1, "editable_fields": []}),
            _template("call_float", "必须调用 float()", "输入函数", "function_call", "float", {"min_count": 1, "editable_fields": []}),
            _template("call_str", "必须调用 str()", "字符串", "function_call", "str", {"min_count": 1, "editable_fields": []}),
            _template("call_len", "必须调用 len()", "字符串", "function_call", "len", {"min_count": 1, "editable_fields": []}),
            _template("call_range", "必须调用 range()", "循环结构", "function_call", "range", {"min_count": 1, "editable_fields": []}),
            _template("input_required", "输入题必须使用 input() 读取数据", "输入函数", "function_call", "input", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("print_sep_exists", "必须使用 print 的 sep 参数", "输出函数", "keyword_arg", "print", {"editable_fields": [], "function": "print", "keyword": "sep"}),
            _template(
                "print_sep_equals",
                "print 的 sep 参数必须等于指定值",
                "输出函数",
                "keyword_arg",
                "print",
                {
                    "required_value": "-",
                    "editable_fields": ["required_value"],
                    "field_labels": {"required_value": "sep 值"},
                    "function": "print",
                    "keyword": "sep",
                },
            ),
            _template("print_end_exists", "必须使用 print 的 end 参数", "输出函数", "keyword_arg", "print", {"editable_fields": [], "function": "print", "keyword": "end"}),
            _template(
                "print_end_equals",
                "print 的 end 参数必须等于指定值",
                "输出函数",
                "keyword_arg",
                "print",
                {
                    "required_value": "\\n",
                    "editable_fields": ["required_value"],
                    "field_labels": {"required_value": "end 值"},
                    "function": "print",
                    "keyword": "end",
                },
            ),
            _template(
                "min_print_arg_count",
                "至少有一次 print 包含 N 个及以上输出对象",
                "输出函数",
                "print_arg_count",
                "print",
                {
                    "min_count": 1,
                    "arg_count": 3,
                    "comparison": "gte",
                    "editable_fields": ["arg_count"],
                    "field_labels": {"arg_count": "输出对象数量阈值"},
                },
            ),
            _template(
                "max_print_arg_count",
                "至多允许一次 print 包含 N 个及以上输出对象",
                "输出函数",
                "print_arg_count",
                "print",
                {
                    "max_count": 1,
                    "arg_count": 3,
                    "comparison": "gte",
                    "editable_fields": ["arg_count", "max_count"],
                    "field_labels": {"arg_count": "输出对象数量阈值", "max_count": "最多次数"},
                },
            ),
        ]
    )

    rows.extend(
        [
            _template("require_assign", "必须使用变量赋值", "变量赋值", "assign", "assign", {"min_count": 1, "editable_fields": []}),
            _template("min_assign_count", "变量赋值至少 N 次", "变量赋值", "assign_count", "assign", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _template("max_assign_count", "变量赋值至多 N 次", "变量赋值", "assign_count", "assign", {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}}),
            _exact_count_template("exact_assign_count", "变量赋值恰好 N 次", "变量赋值", "assign_count", "assign"),
            _template(
                "require_variable_name",
                "必须使用指定变量名",
                "变量赋值",
                "required_variable",
                "variable",
                {"editable_fields": ["variable_name"], "field_labels": {"variable_name": "变量名"}, "variable_name": "score"},
            ),
            _template(
                "forbid_variable_name",
                "禁止使用指定变量名",
                "变量赋值",
                "forbid_variable",
                "variable",
                {"editable_fields": ["variable_name"], "field_labels": {"variable_name": "变量名"}, "variable_name": "temp"},
            ),
            _template("require_parallel_assign", "必须使用同步赋值", "变量赋值", "parallel_assignment", "parallel", {"min_count": 1, "editable_fields": []}),
            _template("min_parallel_assign_count", "同步赋值至少 N 次", "变量赋值", "parallel_assignment", "parallel", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _exact_count_template("exact_parallel_assign_count", "同步赋值恰好 N 次", "变量赋值", "parallel_assignment", "parallel"),
            _template("require_chain_assign", "必须使用连锁赋值", "变量赋值", "chain_assignment", "chain", {"min_count": 1, "editable_fields": []}),
            _template("require_swap_assign", "必须使用交换赋值", "变量赋值", "swap_assignment", "swap", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _operator_rule("require_add_operator", "必须使用加法 +", "Add"),
            _operator_rule("require_sub_operator", "必须使用减法 -", "Sub"),
            _operator_rule("require_mult_operator", "必须使用乘法 *", "Mult"),
            _operator_rule("require_div_operator", "必须使用除法 /", "Div"),
            _operator_rule("require_floor_div_operator", "必须使用整除 //", "FloorDiv"),
            _operator_rule("require_mod_operator", "必须使用取余 %", "Mod"),
            _operator_rule("require_pow_operator", "必须使用幂运算 **", "Pow"),
            _operator_rule("require_set_intersection", "必须使用交集 &", "BitAnd", "集合"),
            _operator_rule("require_set_union", "必须使用并集 |", "BitOr", "集合"),
            _operator_rule("require_set_difference", "必须使用差集 -", "Sub", "集合"),
            _template("require_aug_add", "必须使用复合赋值 +=", "运算符", "aug_assign_operator", "Add", {"min_count": 1, "editable_fields": []}),
            _template("require_aug_sub", "必须使用复合赋值 -=", "运算符", "aug_assign_operator", "Sub", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_eq_compare", "必须使用 ==", "比较运算符", "compare_operator", "Eq", {"min_count": 1, "editable_fields": []}),
            _template("require_neq_compare", "必须使用 !=", "比较运算符", "compare_operator", "NotEq", {"min_count": 1, "editable_fields": []}),
            _template("require_gt_compare", "必须使用 >", "比较运算符", "compare_operator", "Gt", {"min_count": 1, "editable_fields": []}),
            _template("require_gte_compare", "必须使用 >=", "比较运算符", "compare_operator", "GtE", {"min_count": 1, "editable_fields": []}),
            _template("require_lt_compare", "必须使用 <", "比较运算符", "compare_operator", "Lt", {"min_count": 1, "editable_fields": []}),
            _template("require_lte_compare", "必须使用 <=", "比较运算符", "compare_operator", "LtE", {"min_count": 1, "editable_fields": []}),
            _template("require_chained_compare", "必须使用区间判断，例如 60 <= score < 90", "比较运算符", "chained_compare", "chain", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_and", "必须使用 and", "逻辑运算符", "bool_operator", "And", {"min_count": 1, "editable_fields": []}),
            _template("require_or", "必须使用 or", "逻辑运算符", "bool_operator", "Or", {"min_count": 1, "editable_fields": []}),
            _template("require_not", "必须使用 not", "逻辑运算符", "unary_operator", "Not", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_if", "必须使用 if", "分支结构", "syntax_node", "If", {"min_count": 1, "editable_fields": []}),
            _template("min_if_count", "if 至少出现 N 次", "分支结构", "syntax_node", "If", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _template("max_if_count", "if 至多出现 N 次", "分支结构", "syntax_node", "If", {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}}),
            _exact_count_template("exact_if_count", "if 恰好出现 N 次", "分支结构", "syntax_node", "If"),
            _template("require_else", "必须使用 else", "分支结构", "branch_feature", "else", {"min_count": 1, "editable_fields": []}),
            _template("require_elif", "必须使用 elif", "分支结构", "branch_feature", "elif", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_for", "必须使用 for", "循环结构", "syntax_node", "For", {"min_count": 1, "editable_fields": []}),
            _template("min_for_count", "for 至少出现 N 次", "循环结构", "syntax_node", "For", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _template("max_for_count", "for 至多出现 N 次", "循环结构", "syntax_node", "For", {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}}),
            _exact_count_template("exact_for_count", "for 恰好出现 N 次", "循环结构", "syntax_node", "For"),
            _template("require_while", "必须使用 while", "循环结构", "syntax_node", "While", {"min_count": 1, "editable_fields": []}),
            _template("min_while_count", "while 至少出现 N 次", "循环结构", "syntax_node", "While", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _template("max_while_count", "while 至多出现 N 次", "循环结构", "syntax_node", "While", {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}}),
            _exact_count_template("exact_while_count", "while 恰好出现 N 次", "循环结构", "syntax_node", "While"),
            _template("require_break", "必须使用 break", "循环结构", "syntax_node", "Break", {"min_count": 1, "editable_fields": []}),
            _template("require_continue", "必须使用 continue", "循环结构", "syntax_node", "Continue", {"min_count": 1, "editable_fields": []}),
            _template("require_nested_for", "必须使用嵌套 for", "循环结构", "nested_for", "nested_for", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_f_string", "必须使用 f-string", "字符串", "f_string", "JoinedStr", {"min_count": 1, "editable_fields": []}),
            _template("require_format_method", "必须使用 format()", "字符串", "format_method", "format", {"min_count": 1, "editable_fields": []}),
            _template("require_percent_format", "必须使用 % 格式化", "字符串", "percent_format", "Mod", {"min_count": 1, "editable_fields": []}),
            _template("require_two_decimal_format", "必须使用保留小数格式，例如 :.2f", "字符串", "format_spec", "format_spec", {"required_value": ".2f", "editable_fields": ["required_value"], "field_labels": {"required_value": "格式说明"}}),
            _template("require_zero_pad_format", "必须使用补零格式，例如 :03d", "字符串", "format_spec", "format_spec", {"required_value": "03d", "editable_fields": ["required_value"], "field_labels": {"required_value": "格式说明"}}),
            _template("require_percent_output_format", "必须使用百分比格式，例如 :.2%", "字符串", "format_spec", "format_spec", {"required_value": ".2%", "editable_fields": ["required_value"], "field_labels": {"required_value": "格式说明"}}),
        ]
    )

    rows.extend(
        [
            _template("require_list_literal", "必须使用列表字面量 []", "列表", "list_literal", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_list_call", "必须使用 list()", "列表", "list_call", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_list_creation", "必须创建列表", "列表", "list_literal", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_list_subscript", "必须使用列表索引", "列表", "subscript", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_list_slice", "必须使用列表切片", "列表", "slice", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_iterate_list", "必须遍历列表", "列表", "iterate_collection", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_list_comp", "必须使用列表推导式", "列表", "list_comprehension", "list", {"min_count": 1, "editable_fields": []}),
            _template("require_sorted_call", "必须使用 sorted()", "列表", "function_call", "sorted", {"min_count": 1, "editable_fields": []}),
        ]
    )
    for method_name in ("append", "insert", "pop", "remove", "sort"):
        rows.extend(_method_rule_templates(method_name, "列表", method_name))

    rows.extend(
        [
            _template("require_split", "必须使用 split()", "字符串", "method_call", "split", {"min_count": 1, "editable_fields": []}),
            _template("require_join", "必须使用 join()", "字符串", "method_call", "join", {"min_count": 1, "editable_fields": []}),
            _template("require_strip", "必须使用 strip()", "字符串", "method_call", "strip", {"min_count": 1, "editable_fields": []}),
            _template("require_replace", "必须使用 replace()", "字符串", "method_call", "replace", {"min_count": 1, "editable_fields": []}),
            _template("require_find", "必须使用 find()", "字符串", "method_call", "find", {"min_count": 1, "editable_fields": []}),
            _template("require_count_method", "必须使用 count()", "字符串", "method_call", "count", {"min_count": 1, "editable_fields": []}),
            _template("require_upper", "必须使用 upper()", "字符串", "method_call", "upper", {"min_count": 1, "editable_fields": []}),
            _template("require_lower", "必须使用 lower()", "字符串", "method_call", "lower", {"min_count": 1, "editable_fields": []}),
            _template("require_startswith", "必须使用 startswith()", "字符串", "method_call", "startswith", {"min_count": 1, "editable_fields": []}),
            _template("require_endswith", "必须使用 endswith()", "字符串", "method_call", "endswith", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_dict_literal", "必须使用字典字面量 {}", "字典", "dict_literal", "dict", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_call", "必须使用 dict()", "字典", "dict_call", "dict", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_creation", "必须创建字典", "字典", "dict_literal", "dict", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_subscript", "必须使用字典键访问", "字典", "subscript", "dict", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_get", "必须使用字典 get()", "字典", "method_call", "get", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_keys", "必须使用 keys()", "字典", "method_call", "keys", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_values", "必须使用 values()", "字典", "method_call", "values", {"min_count": 1, "editable_fields": []}),
            _template("require_dict_items", "必须使用 items()", "字典", "method_call", "items", {"min_count": 1, "editable_fields": []}),
            _template("require_iterate_dict", "必须遍历字典", "字典", "iterate_collection", "dict", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_set_literal", "必须创建集合", "集合", "set_literal", "set", {"min_count": 1, "editable_fields": []}),
            _template("require_set_call", "必须使用 set()", "集合", "set_call", "set", {"min_count": 1, "editable_fields": []}),
            _template("require_set_dedup", "必须使用集合去重", "集合", "set_call", "set", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_def", "必须定义函数 def", "函数定义", "function_def", "FunctionDef", {"min_count": 1, "editable_fields": []}),
            _template("min_def_count", "函数定义至少 N 个", "函数定义", "function_def", "FunctionDef", {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少次数"}}),
            _template("max_def_count", "函数定义至多 N 个", "函数定义", "function_def", "FunctionDef", {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多次数"}}),
            _exact_count_template("exact_def_count", "函数定义恰好 N 个", "函数定义", "function_def", "FunctionDef"),
            _template("require_return", "必须使用 return", "函数定义", "syntax_node", "Return", {"min_count": 1, "editable_fields": []}),
            _template(
                "require_function_name",
                "必须定义指定名称的函数",
                "函数定义",
                "function_def_name",
                "FunctionDef",
                {"editable_fields": ["function_name"], "field_labels": {"function_name": "函数名"}, "function_name": "check_score"},
            ),
            _template(
                "require_custom_function_call",
                "必须调用自定义函数",
                "函数定义",
                "function_call",
                "__user_defined__",
                {"min_count": 1, "editable_fields": []},
            ),
            _template(
                "min_function_args",
                "函数参数至少 N 个",
                "函数定义",
                "function_args_count",
                "FunctionDef",
                {"min_count": 1, "editable_fields": ["min_count"], "field_labels": {"min_count": "最少参数个数"}},
            ),
            _template(
                "max_function_args",
                "函数参数至多 N 个",
                "函数定义",
                "function_args_count",
                "FunctionDef",
                {"max_count": 1, "editable_fields": ["max_count"], "field_labels": {"max_count": "最多参数个数"}},
            ),
            _template("require_default_args", "必须使用默认参数", "函数定义", "default_args", "FunctionDef", {"min_count": 1, "editable_fields": []}),
            _template("require_function_return", "禁止函数中只 print 不 return", "函数定义", "return_required", "FunctionDef", {"min_count": 1, "editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template("require_try", "必须使用 try-except", "异常处理", "try_except", "try", {"min_count": 1, "editable_fields": []}),
            _template("require_except", "必须使用 except", "异常处理", "try_except", "except", {"min_count": 1, "editable_fields": []}),
            _template("require_try_else", "必须使用 else", "异常处理", "try_except", "else", {"min_count": 1, "editable_fields": []}),
            _template("require_finally", "必须使用 finally", "异常处理", "try_except", "finally", {"min_count": 1, "editable_fields": []}),
            _template(
                "require_valueerror_handler",
                "必须捕获 ValueError",
                "异常处理",
                "exception_handler",
                "ValueError",
                {"editable_fields": ["exception_name"], "field_labels": {"exception_name": "异常类型"}, "exception_name": "ValueError"},
            ),
            _template(
                "require_zerodivision_handler",
                "必须捕获 ZeroDivisionError",
                "异常处理",
                "exception_handler",
                "ZeroDivisionError",
                {"editable_fields": ["exception_name"], "field_labels": {"exception_name": "异常类型"}, "exception_name": "ZeroDivisionError"},
            ),
        ]
    )

    rows.extend(
        [
            _template("require_with", "必须使用 with", "文件操作", "with_statement", "With", {"min_count": 1, "editable_fields": []}),
            _template("require_with_open", "必须使用 with open()", "文件操作", "with_open", "open", {"min_count": 1, "editable_fields": []}),
            _template("require_open", "必须使用 open()", "文件操作", "function_call", "open", {"min_count": 1, "editable_fields": []}),
            _template("require_read", "必须使用 read()", "文件操作", "method_call", "read", {"min_count": 1, "editable_fields": []}),
            _template("require_readline", "必须使用 readline()", "文件操作", "method_call", "readline", {"min_count": 1, "editable_fields": []}),
            _template("require_readlines", "必须使用 readlines()", "文件操作", "method_call", "readlines", {"min_count": 1, "editable_fields": []}),
            _template("require_write", "必须使用 write()", "文件操作", "method_call", "write", {"min_count": 1, "editable_fields": []}),
            _template(
                "require_append_mode",
                "必须使用 append 模式",
                "文件操作",
                "open_mode",
                "a",
                {"required_value": "a", "editable_fields": ["required_value"], "field_labels": {"required_value": "open 模式"}},
            ),
        ]
    )

    rows.extend(
        [
            _template("forbid_import", "禁止 import", "禁止写法", "forbid", "import", {"editable_fields": []}),
            _template("forbid_eval", "禁止 eval()", "禁止写法", "forbid", "eval", {"editable_fields": []}),
            _template("forbid_exec", "禁止 exec()", "禁止写法", "forbid", "exec", {"editable_fields": []}),
            _template("forbid_open", "禁止 open()", "禁止写法", "forbid", "open", {"editable_fields": []}),
            _template("forbid_os", "禁止使用 os", "禁止写法", "forbid", "os", {"editable_fields": []}),
            _template("forbid_subprocess", "禁止使用 subprocess", "禁止写法", "forbid", "subprocess", {"editable_fields": []}),
        ]
    )

    rows.extend(
        [
            _template(
                "require_import_module",
                "必须 import 指定模块",
                "import 与模块",
                "import_required",
                "import",
                {"editable_fields": ["module"], "field_labels": {"module": "模块名"}, "module": "math"},
            ),
            _template(
                "forbid_import_module",
                "禁止 import 指定模块",
                "import 与模块",
                "import_forbid",
                "import",
                {"editable_fields": ["module"], "field_labels": {"module": "模块名"}, "module": "os"},
            ),
            _template(
                "require_import_from_module",
                "必须 from ... import ...",
                "import 与模块",
                "import_from_required",
                "import_from",
                {"editable_fields": ["module"], "field_labels": {"module": "模块名"}, "module": "math"},
            ),
            _template(
                "forbid_import_from_module",
                "禁止 from ... import ...",
                "import 与模块",
                "import_from_forbid",
                "import_from",
                {"editable_fields": ["module"], "field_labels": {"module": "模块名"}, "module": "os"},
            ),
        ]
    )

    rows.extend(
        [
            _template(
                "forbid_literal_output_answer",
                "禁止直接输出完整目标答案",
                "禁止写法",
                "forbid_literal_output",
                "answer",
                {"editable_fields": [], "match_source": "problem_outputs"},
            ),
            _template(
                "forbid_literal_output_sample",
                "禁止直接输出公开样例答案",
                "禁止写法",
                "forbid_literal_output",
                "sample",
                {"editable_fields": [], "match_source": "public_sample_outputs"},
            ),
        ]
    )

    for index, row in enumerate(rows, start=1):
        row["sort_order"] = index * 10
    return rows


DEFAULT_AST_RULE_TEMPLATES = _build_default_templates()


def get_default_ast_rule_templates():
    templates = []
    for template in DEFAULT_AST_RULE_TEMPLATES:
        row = copy.deepcopy(template)
        row.setdefault("enabled", True)
        row.setdefault("description", "")
        row.setdefault("default_params", {})
        templates.append(row)
    return templates


def _json_text(value):
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False)


def _literal_node_value(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _safe_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_output_text(text):
    if text is None:
        return ""
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def _compare_counts(actual_count, min_count, max_count):
    if min_count is not None and actual_count < min_count:
        return False
    if max_count is not None and actual_count > max_count:
        return False
    return True


def _first_param(params, *keys):
    for key in keys:
        if params.get(key) not in (None, ""):
            return params.get(key)
    return None


def _target_display(rule_type, target, params=None):
    params = params or {}
    if rule_type == "syntax_node":
        return NODE_LABELS.get(target, target)
    if rule_type == "method_call":
        return METHOD_LABELS.get(target, f"{target}()")
    if rule_type == "operator":
        return OPERATOR_LABELS.get(target, target)
    if rule_type == "compare_operator":
        return COMPARE_LABELS.get(target, target)
    if rule_type == "bool_operator":
        return BOOL_LABELS.get(target, target)
    if rule_type == "unary_operator":
        return UNARY_LABELS.get(target, target)
    if rule_type == "forbid":
        return FORBID_LABELS.get(target, target)
    if target == "__user_defined__":
        return "自定义函数"
    if params.get("function_name"):
        return params["function_name"]
    if params.get("variable_name"):
        return params["variable_name"]
    if params.get("module"):
        return params["module"]
    if params.get("exception_name"):
        return params["exception_name"]
    if target:
        return str(target)
    return "目标语法"


def build_rule_description(rule):
    rule_type = (rule.get("rule_type") or "").strip()
    target = (rule.get("target") or "").strip()
    min_count = rule.get("min_count")
    max_count = rule.get("max_count")
    required_value = rule.get("required_value")
    params = rule.get("params") or {}
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {}

    if rule_type == "function_call":
        function_name = target if target != "__user_defined__" else "自定义函数"
        if function_name == "__user_defined__":
            function_name = "自定义函数"
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求 {function_name}() 恰好调用 {min_count} 次。"
        if min_count is not None and max_count is not None:
            return f"本题要求 {function_name} 调用次数在 {min_count} 到 {max_count} 次之间。"
        if min_count is not None:
            if target == "__user_defined__":
                return "本题要求调用自定义函数。"
            if int(min_count) <= 1:
                return f"本题要求调用 {function_name}()。"
            return f"本题要求至少调用 {min_count} 次 {function_name}()。"
        if max_count is not None:
            return f"本题要求 {function_name}() 调用次数不超过 {max_count} 次。"
        return f"本题要求调用 {function_name}()。"

    if rule_type == "syntax_node":
        label = NODE_LABELS.get(target, target)
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求 {label} 恰好出现 {min_count} 次。"
        if min_count is not None and int(min_count) <= 1:
            if target == "If":
                return "本题要求使用 if 分支结构。"
            if target == "For":
                return "本题要求使用 for 循环。"
            if target == "While":
                return "本题要求使用 while 循环。"
            if target == "Try":
                return "本题要求使用 try。"
            if target == "With":
                return "本题要求使用 with。"
            if target == "FunctionDef":
                return "本题要求定义函数。"
            return f"本题要求使用 {label}。"
        if min_count is not None and max_count is not None:
            return f"本题要求 {label} 出现 {min_count} 到 {max_count} 次。"
        if min_count is not None:
            return f"本题要求 {label} 至少出现 {min_count} 次。"
        if max_count is not None:
            return f"本题要求 {label} 至多出现 {max_count} 次。"
        return f"本题要求使用 {label}。"

    if rule_type in {"assign", "assign_count"}:
        if min_count is not None and int(min_count) <= 1 and max_count is None:
            return "本题要求使用变量保存数据。"
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求变量赋值恰好出现 {min_count} 次。"
        if min_count is not None and max_count is not None:
            return f"本题要求变量赋值次数在 {min_count} 到 {max_count} 次之间。"
        if min_count is not None:
            return f"本题要求至少出现 {min_count} 次变量赋值。"
        if max_count is not None:
            return f"本题要求变量赋值次数不超过 {max_count} 次。"
        return "本题要求使用变量保存数据。"

    if rule_type == "required_variable":
        variable_name = _first_param(params, "variable_name") or required_value or target
        return f"本题要求使用变量名 {variable_name}。"

    if rule_type == "forbid_variable":
        variable_name = _first_param(params, "variable_name") or required_value or target
        return f"本题不允许使用变量名 {variable_name}。"

    if rule_type == "operator":
        return f"本题要求使用 {OPERATOR_LABELS.get(target, target)} 运算符。"

    if rule_type == "aug_assign_operator":
        return f"本题要求使用复合赋值 {OPERATOR_LABELS.get(target, target)}="

    if rule_type == "compare_operator":
        return f"本题要求使用 {COMPARE_LABELS.get(target, target)} 比较运算符。"

    if rule_type == "chained_compare":
        return "本题要求使用链式区间判断，例如 60 <= score < 90。"

    if rule_type == "bool_operator":
        return f"本题要求使用 {BOOL_LABELS.get(target, target)} 连接多个条件。"

    if rule_type == "unary_operator":
        return f"本题要求使用 {UNARY_LABELS.get(target, target)} 进行取反判断。"

    if rule_type == "method_call":
        label = METHOD_LABELS.get(target, f"{target}()")
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求 {label} 恰好调用 {min_count} 次。"
        if min_count is not None and max_count is not None:
            return f"本题要求 {label} 调用次数在 {min_count} 到 {max_count} 次之间。"
        if min_count is not None:
            if int(min_count) <= 1:
                return f"本题要求使用 {label} 方法。"
            return f"本题要求至少使用 {min_count} 次 {label} 方法。"
        if max_count is not None:
            return f"本题要求 {label} 调用次数不超过 {max_count} 次。"
        return f"本题要求使用 {label} 方法。"

    if rule_type == "keyword_arg":
        function_name = params.get("function") or target or "print"
        keyword = params.get("keyword") or target
        if required_value not in (None, ""):
            return f"本题要求使用 {function_name}() 的 {keyword} 参数，且 {keyword} 的值为 {_json_text(required_value)}。"
        return f"本题要求使用 {function_name}() 的 {keyword} 参数。"

    if rule_type == "print_arg_count":
        arg_count = int(params.get("arg_count") or 1)
        if max_count is not None:
            return f"本题至多允许 {max_count} 次 print() 包含 {arg_count} 个及以上输出对象。"
        return f"本题要求至少有一次 print() 包含 {arg_count} 个及以上输出对象。"

    if rule_type == "branch_feature":
        if target == "else":
            return "本题要求使用 else 分支。"
        if target == "elif":
            return "本题要求使用 elif 分支。"
        return f"本题要求使用 {target} 分支。"

    if rule_type == "f_string":
        return "本题要求使用 f-string 完成格式化输出。"

    if rule_type == "format_method":
        return "本题要求使用 format() 完成格式化输出。"

    if rule_type == "percent_format":
        return "本题要求使用 % 格式化输出。"

    if rule_type == "format_spec":
        spec = required_value or params.get("format_spec") or target
        return f"本题要求使用格式控制 {spec}。"

    if rule_type == "list_literal":
        return "本题要求使用列表字面量 []。"

    if rule_type == "list_call":
        return "本题要求使用 list() 创建列表。"

    if rule_type == "dict_literal":
        return "本题要求使用字典字面量 {}。"

    if rule_type == "dict_call":
        return "本题要求使用 dict() 创建字典。"

    if rule_type == "set_literal":
        return "本题要求使用集合字面量创建集合。"

    if rule_type == "set_call":
        return "本题要求使用 set() 创建集合。"

    if rule_type == "subscript":
        collection_type = target
        if collection_type == "list":
            return "本题要求使用列表下标访问元素。"
        if collection_type == "dict":
            return "本题要求使用字典键访问内容。"
        return "本题要求使用下标访问。"

    if rule_type == "slice":
        return "本题要求使用切片。"

    if rule_type == "list_comprehension":
        return "本题要求使用列表推导式。"

    if rule_type == "iterate_collection":
        if target == "list":
            return "本题要求使用 for 循环遍历列表。"
        if target == "dict":
            return "本题要求使用 for 循环遍历字典。"
        return "本题要求遍历集合中的数据。"

    if rule_type == "function_def":
        return build_rule_description({"rule_type": "syntax_node", "target": "FunctionDef", "min_count": min_count, "max_count": max_count})

    if rule_type == "parallel_assignment":
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求同步赋值恰好出现 {min_count} 次。"
        if min_count is not None and max_count is not None:
            return f"本题要求同步赋值出现 {min_count} 到 {max_count} 次。"
        if min_count is not None:
            if int(min_count) <= 1:
                return "本题要求使用同步赋值。"
            return f"本题要求至少使用 {min_count} 次同步赋值。"
        if max_count is not None:
            return f"本题要求同步赋值不超过 {max_count} 次。"
        return "本题要求使用同步赋值。"

    if rule_type == "chain_assignment":
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求连锁赋值恰好出现 {min_count} 次。"
        return "本题要求使用连锁赋值。"

    if rule_type == "swap_assignment":
        if min_count is not None and max_count is not None and int(min_count) == int(max_count):
            return f"本题要求交换赋值恰好出现 {min_count} 次。"
        return "本题要求使用交换赋值，例如 a, b = b, a。"

    if rule_type == "nested_for":
        return "本题要求使用嵌套 for 循环。"

    if rule_type == "function_def_name":
        function_name = _first_param(params, "function_name") or required_value or target
        return f"本题要求定义函数 {function_name}。"

    if rule_type == "function_args_count":
        if min_count is not None and max_count is not None:
            return f"本题要求函数参数数量在 {min_count} 到 {max_count} 个之间。"
        if min_count is not None:
            return f"本题要求函数至少包含 {min_count} 个参数。"
        if max_count is not None:
            return f"本题要求函数参数数量不超过 {max_count} 个。"
        return "本题要求函数参数数量满足要求。"

    if rule_type == "default_args":
        return "本题要求函数使用默认参数。"

    if rule_type == "return_required":
        return "本题要求函数使用 return 返回结果。"

    if rule_type == "try_except":
        if target == "try":
            return "本题要求使用 try-except 处理异常。"
        if target == "except":
            return "本题要求使用 except 分支处理异常。"
        if target == "else":
            return "本题要求在异常处理中使用 else。"
        if target == "finally":
            return "本题要求在异常处理中使用 finally。"

    if rule_type == "exception_handler":
        exception_name = _first_param(params, "exception_name") or required_value or target
        return f"本题要求捕获 {exception_name}。"

    if rule_type == "with_statement":
        return "本题要求使用 with 语句。"

    if rule_type == "with_open":
        return "本题要求使用 with open()。"

    if rule_type == "open_mode":
        mode = required_value or params.get("mode") or target
        return f"本题要求使用 open() 的 {mode} 模式。"

    if rule_type == "import_required":
        module_name = _first_param(params, "module") or required_value or target
        return f"本题要求导入 {module_name} 模块。"

    if rule_type == "import_forbid":
        module_name = _first_param(params, "module") or required_value or target
        return f"本题不允许导入 {module_name} 模块。"

    if rule_type == "import_from_required":
        module_name = _first_param(params, "module") or required_value or target
        return f"本题要求使用 from {module_name} import ...。"

    if rule_type == "import_from_forbid":
        module_name = _first_param(params, "module") or required_value or target
        return f"本题不允许使用 from {module_name} import ...。"

    if rule_type == "forbid_literal_output":
        if target == "sample":
            return "本题要求不要直接输出公开样例答案。"
        return "本题要求不要直接输出完整目标答案。"

    if rule_type == "forbid":
        return f"本题要求不要使用 {_target_display(rule_type, target, params)}。"

    return rule.get("description") or "本题包含一条语法目标。"


def _extract_store_names(target):
    names = []
    if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for item in target.elts:
            names.extend(_extract_store_names(item))
    return names


def _flatten_constant_string(node):
    if node is None:
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
        return "".join(parts)
    return ""


def _is_string_like(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _function_body_walk(node):
    for statement in node.body:
        yield from _walk_without_nested_functions(statement)


def _walk_without_nested_functions(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
        return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _walk_without_nested_functions(child)


def _function_info(node):
    params_count = len(getattr(node.args, "posonlyargs", [])) + len(node.args.args) + len(node.args.kwonlyargs)
    if node.args.vararg:
        params_count += 1
    if node.args.kwarg:
        params_count += 1
    defaults_count = len(node.args.defaults) + sum(1 for item in node.args.kw_defaults if item is not None)
    has_return = any(isinstance(child, ast.Return) for child in _function_body_walk(node))
    has_print = any(
        isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "print"
        for child in _function_body_walk(node)
    )
    return {
        "name": node.name,
        "arg_count": params_count,
        "defaults_count": defaults_count,
        "has_return": has_return,
        "print_without_return": has_print and not has_return,
    }


class AstStatsCollector(ast.NodeVisitor):
    def __init__(self):
        self.function_calls = {}
        self.method_calls = {}
        self.syntax_nodes = {}
        self.keyword_args = {}
        self.print_calls = []
        self.branch_features = {"else": 0, "elif": 0}
        self.try_features = {"try": 0, "except": 0, "else": 0, "finally": 0}
        self.forbidden_usage = {"import": 0, "eval": 0, "exec": 0, "open": 0, "os": 0, "subprocess": 0}
        self.assignment_count = 0
        self.parallel_assignment_count = 0
        self.chain_assignment_count = 0
        self.swap_assignment_count = 0
        self.variables_assigned = set()
        self.variable_assign_counts = {}
        self.variables_used = set()
        self.operators = {}
        self.aug_assign_operators = {}
        self.compare_operators = {}
        self.bool_operators = {}
        self.unary_operators = {}
        self.list_literals = 0
        self.list_calls = 0
        self.list_comprehensions = 0
        self.dict_literals = 0
        self.dict_calls = 0
        self.set_literals = 0
        self.set_calls = 0
        self.subscript_contexts = {"any": 0, "list": 0, "dict": 0}
        self.slice_count = 0
        self.iterate_collection = {"any": 0, "list": 0, "dict": 0}
        self.nested_for_count = 0
        self.function_defs = {}
        self.user_defined_function_names = set()
        self.imports = set()
        self.import_from = {}
        self.imported_names = {}
        self.name_origins = {}
        self.has_f_string = False
        self.format_specs = []
        self.percent_format_count = 0
        self.with_open_count = 0
        self.open_modes = []
        self.print_literal_outputs = []
        self.collection_name_kinds = {}
        self.exception_handlers = {}

    def _inc(self, bucket, key, amount=1):
        bucket[key] = int(bucket.get(key, 0)) + amount

    def _record_assigned_name(self, name):
        if not name:
            return
        self.variables_assigned.add(name)
        self._inc(self.variable_assign_counts, name)

    def _infer_collection_kind(self, node):
        if isinstance(node, ast.List):
            return "list"
        if isinstance(node, ast.ListComp):
            return "list"
        if isinstance(node, ast.Dict):
            return "dict"
        if isinstance(node, ast.Set):
            return "set"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"list", "dict", "set"}:
                return node.func.id
        return None

    def _expr_kind(self, node):
        direct_kind = self._infer_collection_kind(node)
        if direct_kind:
            return direct_kind
        if isinstance(node, ast.Name):
            return self.collection_name_kinds.get(node.id)
        return None

    def generic_visit(self, node):
        self._inc(self.syntax_nodes, node.__class__.__name__)
        super().generic_visit(node)

    def visit_Assign(self, node):
        self.assignment_count += 1
        if len(node.targets) > 1:
            self.chain_assignment_count += 1
        if any(self._is_parallel_target(target) for target in node.targets):
            self.parallel_assignment_count += 1
        if self._is_swap_assignment(node):
            self.swap_assignment_count += 1
        inferred_kind = self._infer_collection_kind(node.value)
        for target in node.targets:
            for name in _extract_store_names(target):
                self._record_assigned_name(name)
                if inferred_kind:
                    self.collection_name_kinds[name] = inferred_kind
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self.assignment_count += 1
        if self._is_parallel_target(node.target):
            self.parallel_assignment_count += 1
        inferred_kind = self._infer_collection_kind(node.value)
        for name in _extract_store_names(node.target):
            self._record_assigned_name(name)
            if inferred_kind:
                self.collection_name_kinds[name] = inferred_kind
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.assignment_count += 1
        self._inc(self.aug_assign_operators, node.op.__class__.__name__)
        for name in _extract_store_names(node.target):
            self._record_assigned_name(name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.variables_used.add(node.id)
            if node.id in {"os", "subprocess"}:
                self._inc(self.forbidden_usage, node.id)
        self.generic_visit(node)

    def visit_BinOp(self, node):
        op_name = node.op.__class__.__name__
        self._inc(self.operators, op_name)
        if op_name == "Mod" and _is_string_like(node.left):
            self.percent_format_count += 1
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            self._inc(self.compare_operators, op.__class__.__name__)
        if len(node.ops) >= 2:
            self._inc(self.compare_operators, "CHAINED")
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self._inc(self.bool_operators, node.op.__class__.__name__)
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        self._inc(self.unary_operators, node.op.__class__.__name__)
        self.generic_visit(node)

    def visit_If(self, node):
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self.branch_features["elif"] += 1
            else:
                self.branch_features["else"] += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.try_features["try"] += 1
        self.try_features["except"] += len(node.handlers)
        if node.orelse:
            self.try_features["else"] += 1
        if node.finalbody:
            self.try_features["finally"] += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if isinstance(node.type, ast.Name):
            self._inc(self.exception_handlers, node.type.id)
        elif isinstance(node.type, ast.Attribute):
            self._inc(self.exception_handlers, node.type.attr)
        self.generic_visit(node)

    def visit_Import(self, node):
        self.forbidden_usage["import"] += 1
        for alias in node.names:
            module_name = (alias.name or "").split(".")[0]
            if not module_name:
                continue
            self.imports.add(module_name)
            local_name = alias.asname or module_name
            self.name_origins[local_name] = module_name
            if module_name in {"os", "subprocess"}:
                self._inc(self.forbidden_usage, module_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.forbidden_usage["import"] += 1
        module_name = ((node.module or "").split(".")[0] if node.module else "")
        if module_name:
            self.import_from.setdefault(module_name, set())
            for alias in node.names:
                self.import_from[module_name].add(alias.name)
                self.imported_names[alias.asname or alias.name] = module_name
                self.name_origins[alias.asname or alias.name] = module_name
            if module_name in {"os", "subprocess"}:
                self._inc(self.forbidden_usage, module_name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.user_defined_function_names.add(node.name)
        self.function_defs.setdefault(node.name, []).append(_function_info(node))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.user_defined_function_names.add(node.name)
        self.function_defs.setdefault(node.name, []).append(_function_info(node))
        self.generic_visit(node)

    def visit_List(self, node):
        self.list_literals += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.list_comprehensions += 1
        self.generic_visit(node)

    def visit_Dict(self, node):
        self.dict_literals += 1
        self.generic_visit(node)

    def visit_Set(self, node):
        self.set_literals += 1
        self.generic_visit(node)

    def visit_Subscript(self, node):
        self.subscript_contexts["any"] += 1
        kind = self._expr_kind(node.value)
        if kind in {"list", "dict"}:
            self.subscript_contexts[kind] += 1
        if isinstance(node.slice, ast.Slice):
            self.slice_count += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.iterate_collection["any"] += 1
        iter_kind = self._expr_kind(node.iter)
        if iter_kind in {"list", "dict"}:
            self.iterate_collection[iter_kind] += 1
        if any(isinstance(child, (ast.For, ast.AsyncFor)) for statement in node.body for child in ast.walk(statement)):
            self.nested_for_count += 1
        self.generic_visit(node)

    def _is_parallel_target(self, target):
        if not isinstance(target, (ast.Tuple, ast.List)):
            return False
        names = _extract_store_names(target)
        return len(names) >= 2

    def _is_swap_assignment(self, node):
        if len(node.targets) != 1:
            return False
        target = node.targets[0]
        if not isinstance(target, (ast.Tuple, ast.List)):
            return False
        if not isinstance(node.value, (ast.Tuple, ast.List)):
            return False
        left_names = [item.id for item in target.elts if isinstance(item, ast.Name)]
        right_names = [item.id for item in node.value.elts if isinstance(item, ast.Name)]
        if len(left_names) < 2 or len(left_names) != len(target.elts):
            return False
        if len(right_names) != len(node.value.elts) or len(left_names) != len(right_names):
            return False
        return left_names != right_names and sorted(left_names) == sorted(right_names)

    def visit_JoinedStr(self, node):
        self.has_f_string = True
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                spec = _flatten_constant_string(value.format_spec)
                if spec:
                    self.format_specs.append(spec)
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            mode = _extract_open_mode(item.context_expr)
            if mode is not None:
                self.with_open_count += 1
                self.open_modes.append(mode)
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = None
        method_name = None

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self._inc(self.function_calls, func_name)
        elif isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            self._inc(self.method_calls, method_name)
            if isinstance(node.func.value, ast.Name):
                base_name = node.func.value.id
                origin = self.name_origins.get(base_name, base_name)
                if origin in {"os", "subprocess"}:
                    self._inc(self.forbidden_usage, origin)

        if func_name in {"eval", "exec", "open"}:
            self._inc(self.forbidden_usage, func_name)

        if func_name == "list":
            self.list_calls += 1
        elif func_name == "dict":
            self.dict_calls += 1
        elif func_name == "set":
            self.set_calls += 1

        if func_name == "open":
            mode = _extract_call_mode(node)
            self.open_modes.append(mode)

        if func_name == "print":
            call_info = {"arg_count": len(node.args), "keywords": {}, "keyword_names": []}
            for keyword in node.keywords:
                if not keyword.arg:
                    continue
                call_info["keyword_names"].append(keyword.arg)
                value = _literal_node_value(keyword.value)
                call_info["keywords"][keyword.arg] = value
                self.keyword_args.setdefault("print", {}).setdefault(keyword.arg, {"count": 0, "values": []})
                self.keyword_args["print"][keyword.arg]["count"] += 1
                self.keyword_args["print"][keyword.arg]["values"].append(value)
            self.print_calls.append(call_info)
            if len(node.args) == 1 and _is_string_like(node.args[0]):
                self.print_literal_outputs.append(_normalize_output_text(node.args[0].value))

        self.generic_visit(node)


def _extract_call_mode(node):
    if len(node.args) >= 2:
        mode_value = _literal_node_value(node.args[1])
        if isinstance(mode_value, str):
            return mode_value
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_value = _literal_node_value(keyword.value)
            if isinstance(mode_value, str):
                return mode_value
    return ""


def _extract_open_mode(node):
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name) and node.func.id == "open":
        return _extract_call_mode(node)
    return None


def _build_stats(collector):
    return {
        "function_calls": collector.function_calls,
        "method_calls": collector.method_calls,
        "syntax_nodes": collector.syntax_nodes,
        "operators": collector.operators,
        "aug_assign_operators": collector.aug_assign_operators,
        "compare_operators": collector.compare_operators,
        "bool_operators": collector.bool_operators,
        "unary_operators": collector.unary_operators,
        "variables_assigned": sorted(collector.variables_assigned),
        "variables_used": sorted(collector.variables_used),
        "function_defs": collector.function_defs,
        "imports": sorted(collector.imports),
        "import_from": {module: sorted(names) for module, names in collector.import_from.items()},
        "branch_features": collector.branch_features,
        "try_features": collector.try_features,
        "keyword_args": collector.keyword_args,
        "print_calls": collector.print_calls,
        "list_literals": collector.list_literals,
        "list_calls": collector.list_calls,
        "list_comprehensions": collector.list_comprehensions,
        "dict_literals": collector.dict_literals,
        "dict_calls": collector.dict_calls,
        "set_literals": collector.set_literals,
        "set_calls": collector.set_calls,
        "subscript_contexts": collector.subscript_contexts,
        "slice_count": collector.slice_count,
        "iterate_collection": collector.iterate_collection,
        "has_f_string": collector.has_f_string,
        "format_specs": collector.format_specs,
        "forbidden_usage": collector.forbidden_usage,
        "assignment_count": collector.assignment_count,
        "parallel_assignment_count": collector.parallel_assignment_count,
        "chain_assignment_count": collector.chain_assignment_count,
        "swap_assignment_count": collector.swap_assignment_count,
        "exception_handlers": collector.exception_handlers,
        "with_open_count": collector.with_open_count,
        "open_modes": collector.open_modes,
        "print_literal_outputs": collector.print_literal_outputs,
        "nested_for_count": collector.nested_for_count,
    }


def _rule_message(rule):
    return rule.get("fail_message") or build_rule_description(rule)


def _evaluate_rule(rule, collector):
    rule_type = rule.get("rule_type")
    target = rule.get("target")
    min_count = _safe_int(rule.get("min_count"))
    max_count = _safe_int(rule.get("max_count"))
    required_value = rule.get("required_value")
    params = rule.get("params") or {}

    if rule_type == "function_call":
        if target == "__user_defined__":
            actual_count = sum(collector.function_calls.get(name, 0) for name in collector.user_defined_function_names)
        else:
            actual_count = int(collector.function_calls.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "syntax_node":
        actual_count = int(collector.syntax_nodes.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "assign":
        return collector.assignment_count > 0

    if rule_type == "assign_count":
        return _compare_counts(collector.assignment_count, min_count, max_count)

    if rule_type == "parallel_assignment":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.parallel_assignment_count, min_count, max_count)

    if rule_type == "chain_assignment":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.chain_assignment_count, min_count, max_count)

    if rule_type == "swap_assignment":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.swap_assignment_count, min_count, max_count)

    if rule_type == "required_variable":
        variable_name = _first_param(params, "variable_name") or required_value or target
        return variable_name in collector.variables_assigned

    if rule_type == "forbid_variable":
        variable_name = _first_param(params, "variable_name") or required_value or target
        return variable_name not in collector.variables_assigned

    if rule_type == "operator":
        actual_count = int(collector.operators.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "aug_assign_operator":
        actual_count = int(collector.aug_assign_operators.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "compare_operator":
        actual_count = int(collector.compare_operators.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "chained_compare":
        actual_count = int(collector.compare_operators.get("CHAINED", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "bool_operator":
        actual_count = int(collector.bool_operators.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "unary_operator":
        actual_count = int(collector.unary_operators.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "method_call":
        actual_count = int(collector.method_calls.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "keyword_arg":
        function_name = params.get("function") or target or "print"
        keyword = params.get("keyword") or target
        info = collector.keyword_args.get(function_name, {}).get(keyword)
        if not info or int(info.get("count", 0)) <= 0:
            return False
        if required_value in (None, ""):
            return True
        return any(value == required_value for value in info.get("values") or [])

    if rule_type == "print_arg_count":
        arg_count = int(params.get("arg_count") or 1)
        comparison = params.get("comparison") or "gte"
        matched_calls = 0
        for call in collector.print_calls:
            current_count = int(call.get("arg_count", 0))
            if comparison == "eq" and current_count == arg_count:
                matched_calls += 1
            elif comparison != "eq" and current_count >= arg_count:
                matched_calls += 1
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(matched_calls, min_count, max_count)

    if rule_type == "branch_feature":
        actual_count = int(collector.branch_features.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "f_string":
        return bool(collector.has_f_string)

    if rule_type == "format_method":
        actual_count = int(collector.method_calls.get("format", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "percent_format":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.percent_format_count, min_count, max_count)

    if rule_type == "format_spec":
        expected_spec = str(required_value or params.get("format_spec") or "").strip()
        if not expected_spec:
            return bool(collector.format_specs)
        return any(expected_spec in (spec or "") for spec in collector.format_specs)

    if rule_type == "list_literal":
        return collector.list_literals > 0

    if rule_type == "list_call":
        return collector.list_calls > 0

    if rule_type == "dict_literal":
        return collector.dict_literals > 0

    if rule_type == "dict_call":
        return collector.dict_calls > 0

    if rule_type == "set_literal":
        return collector.set_literals > 0

    if rule_type == "set_call":
        return collector.set_calls > 0

    if rule_type == "subscript":
        actual_count = int(collector.subscript_contexts.get(target or "any", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "slice":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.slice_count, min_count, max_count)

    if rule_type == "list_comprehension":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.list_comprehensions, min_count, max_count)

    if rule_type == "iterate_collection":
        actual_count = int(collector.iterate_collection.get(target or "any", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "nested_for":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.nested_for_count, min_count, max_count)

    if rule_type == "function_def":
        actual_count = int(collector.syntax_nodes.get("FunctionDef", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "function_def_name":
        function_name = _first_param(params, "function_name") or required_value or target
        return function_name in collector.function_defs

    if rule_type == "function_args_count":
        function_name = _first_param(params, "function_name")
        if function_name:
            infos = collector.function_defs.get(function_name, [])
        else:
            infos = [item for values in collector.function_defs.values() for item in values]
        if not infos:
            return False
        return any(_compare_counts(int(info.get("arg_count", 0)), min_count, max_count) for info in infos)

    if rule_type == "default_args":
        function_name = _first_param(params, "function_name")
        if function_name:
            infos = collector.function_defs.get(function_name, [])
        else:
            infos = [item for values in collector.function_defs.values() for item in values]
        return any(int(info.get("defaults_count", 0)) > 0 for info in infos)

    if rule_type == "return_required":
        infos = [item for values in collector.function_defs.values() for item in values]
        if not infos:
            return False
        return all(bool(info.get("has_return")) for info in infos)

    if rule_type == "try_except":
        actual_count = int(collector.try_features.get(target, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "exception_handler":
        exception_name = _first_param(params, "exception_name") or required_value or target
        actual_count = int(collector.exception_handlers.get(exception_name, 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "with_statement":
        actual_count = int(collector.syntax_nodes.get("With", 0))
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(actual_count, min_count, max_count)

    if rule_type == "with_open":
        if min_count is None and max_count is None:
            min_count = 1
        return _compare_counts(collector.with_open_count, min_count, max_count)

    if rule_type == "open_mode":
        mode = str(required_value or params.get("mode") or target or "")
        return any(mode == current_mode for current_mode in collector.open_modes)

    if rule_type == "import_required":
        module_name = (_first_param(params, "module") or required_value or target or "").split(".")[0]
        return module_name in collector.imports

    if rule_type == "import_forbid":
        module_name = (_first_param(params, "module") or required_value or target or "").split(".")[0]
        return module_name not in collector.imports

    if rule_type == "import_from_required":
        module_name = (_first_param(params, "module") or required_value or target or "").split(".")[0]
        return module_name in collector.import_from

    if rule_type == "import_from_forbid":
        module_name = (_first_param(params, "module") or required_value or target or "").split(".")[0]
        return module_name not in collector.import_from

    if rule_type == "forbid_literal_output":
        forbidden_outputs = params.get("forbidden_outputs") or []
        normalized_forbidden = {_normalize_output_text(item) for item in forbidden_outputs if _normalize_output_text(item)}
        return not any(output in normalized_forbidden for output in collector.print_literal_outputs)

    if rule_type == "forbid":
        if target in {"os", "subprocess"}:
            return int(collector.forbidden_usage.get(target, 0)) == 0 and target not in collector.imports and target not in collector.import_from
        if target == "import":
            return int(collector.forbidden_usage.get("import", 0)) == 0
        return int(collector.forbidden_usage.get(target, 0)) == 0

    return False


def check_ast_rules(code, rules):
    enabled_rules = [rule for rule in (rules or []) if rule and rule.get("enabled", True)]
    if not enabled_rules:
        return {"passed": True, "failed_rules": [], "stats": {}}

    try:
        tree = ast.parse(code or "")
    except SyntaxError as exc:
        message = f"代码无法完成 AST 分析：第 {exc.lineno or '?'} 行附近存在 Python 语法错误。"
        return {
            "passed": False,
            "failed_rules": [
                {
                    "rule_id": None,
                    "description": "AST 语法检查无法完成",
                    "message": message,
                }
            ],
            "stats": {},
            "syntax_error": {
                "lineno": exc.lineno,
                "offset": exc.offset,
                "message": str(exc),
            },
        }

    collector = AstStatsCollector()
    collector.visit(tree)
    stats = _build_stats(collector)

    failed_rules = []
    for rule in enabled_rules:
        if _evaluate_rule(rule, collector):
            continue
        failed_rules.append(
            {
                "rule_id": rule.get("id"),
                "description": rule.get("description") or build_rule_description(rule),
                "message": _rule_message(rule),
            }
        )

    return {
        "passed": len(failed_rules) == 0,
        "failed_rules": failed_rules,
        "stats": stats,
    }
