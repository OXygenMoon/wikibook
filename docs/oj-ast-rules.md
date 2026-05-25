# OJ AST 语法规则系统

本文档总结当前 OJ AST 语法检查系统的整体架构、数据流、规则类型和内置规则目录，便于后续维护、扩展和教师配置题目。

## 1. 目标与判题语义

AST 语法检查只影响 `AC / PAC` 的区分，不影响程序输出是否正确。

- 输出错误：保持原状态，如 `WA / RE / TLE / CE`
- 输出正确，且题目没有启用 AST 规则：`PAC`
- 输出正确，且题目启用了 AST 规则但未全部满足：`AC`
- 输出正确，且题目启用了 AST 规则且全部满足：`PAC`

当前系统只支持“所有启用规则都必须满足”的执行方式，即 `all` 模式。

## 2. 核心文件

- AST 规则定义与检查器：`/Users/laozhenyu/Project/wikibook/utils/ast_checker.py`
- 规则模板与题目规则模型、保存校验、展示序列化：`/Users/laozhenyu/Project/wikibook/app.py`
- 判题结果接入 `AC / PAC`：`/Users/laozhenyu/Project/wikibook/judge_tasks.py`
- 题目编辑页 AST 配置：`/Users/laozhenyu/Project/wikibook/frontend/src/oj/admin/EditProblemWorkspace.vue`
- 题面“满星语法目标”展示：`/Users/laozhenyu/Project/wikibook/frontend/src/oj/public/ProblemDetailView.vue`
- 提交详情页 AST 反馈展示：`/Users/laozhenyu/Project/wikibook/frontend/src/oj/public/SubmissionDetailView.vue`

## 3. 数据结构

### 3.1 规则模板表 `ast_rule_templates`

用于保存系统内置 AST 规则模板，供教师在前端快速选择。

关键字段：

- `code`：模板唯一编码
- `name`：模板显示名称
- `category`：规则分类
- `rule_type`：底层规则类型
- `target`：检查目标
- `default_params`：默认参数 JSON
- `enabled`：模板是否启用
- `sort_order`：排序

### 3.2 题目规则表 `problem_ast_rules`

用于保存某道题启用的具体 AST 规则。

关键字段：

- `problem_id`
- `template_id`
- `rule_type`
- `target`
- `min_count`
- `max_count`
- `required_value`
- `params`
- `description`
- `fail_message`
- `enabled`
- `sort_order`

### 3.3 题目总开关

题目表使用 `ast_check_enabled` 作为 AST 检查总开关。

## 4. 配置与保存流程

1. 教师在题目编辑页打开 AST 配置区。
2. 前端从模板列表中按分类选择规则模板。
3. 前端根据模板 `default_params` 动态渲染参数输入项。
4. 前端实时生成中文描述预览。
5. 提交后，后端通过 `validate_problem_ast_rules()` 校验规则：
   - `rule_type` 必须受支持
   - `target` 不能为空
   - `min_count / max_count` 必须是非负整数或空
   - `min_count` 不能大于 `max_count`
   - `description` 为空时自动生成
6. 后端通过 `replace_problem_ast_rules()` 覆盖保存题目规则。

## 5. 判题接入流程

1. 原判题流程先执行程序并判断是否 `accepted`。
2. 若原状态不是 `accepted`，保持原状态。
3. 若原状态是 `accepted`：
   - 读取题目已启用 AST 规则
   - 注入公开样例输出、测试点输出等上下文参数
   - 调用 `check_ast_rules(code, rules)`
4. 根据 AST 结果：
   - `passed = True` -> `PAC`
   - `passed = False` -> `AC`

## 6. AST 检查器结构

### 6.1 一次遍历收集统计

`AstStatsCollector(ast.NodeVisitor)` 会对代码 AST 只遍历一次，统一收集以下统计，再统一判断规则。

主要统计项：

- `function_calls`
- `method_calls`
- `syntax_nodes`
- `keyword_args`
- `print_calls`
- `branch_features`
- `try_features`
- `forbidden_usage`
- `assignment_count`
- `parallel_assignment_count`
- `chain_assignment_count`
- `swap_assignment_count`
- `variables_assigned`
- `variable_assign_counts`
- `variables_used`
- `operators`
- `aug_assign_operators`
- `compare_operators`
- `bool_operators`
- `unary_operators`
- `list_literals`
- `list_calls`
- `list_comprehensions`
- `dict_literals`
- `dict_calls`
- `set_literals`
- `set_calls`
- `subscript_contexts`
- `slice_count`
- `iterate_collection`
- `nested_for_count`
- `function_defs`
- `user_defined_function_names`
- `imports`
- `import_from`
- `name_origins`
- `has_f_string`
- `format_specs`
- `percent_format_count`
- `with_open_count`
- `open_modes`
- `print_literal_outputs`
- `exception_handlers`

### 6.2 规则执行

`check_ast_rules(code, rules)` 的行为：

1. 过滤未启用规则
2. `ast.parse(code)`
3. 语法树交给 `AstStatsCollector`
4. 对每条规则执行 `_evaluate_rule(rule, collector)`
5. 返回：
   - `passed`
   - `failed_rules`
   - `stats`
   - `syntax_error`（若 AST 解析失败）

注意：`SyntaxError` 只用于 AST 分析反馈，不替代原有 `CE` 判题逻辑。

## 7. 当前底层规则类型

当前系统支持的 `rule_type` 如下：

- `assign`
- `assign_count`
- `bool_operator`
- `branch_feature`
- `chain_assignment`
- `chained_compare`
- `compare_operator`
- `default_args`
- `dict_call`
- `dict_literal`
- `exception_handler`
- `f_string`
- `forbid`
- `forbid_function`
- `forbid_method`
- `forbid_literal_output`
- `forbid_variable`
- `format_method`
- `format_spec`
- `function_args_count`
- `function_call`
- `function_def`
- `function_def_name`
- `import_forbid`
- `import_from_forbid`
- `import_from_required`
- `import_required`
- `iterate_collection`
- `keyword_arg`
- `list_call`
- `list_comprehension`
- `list_literal`
- `method_call`
- `open_mode`
- `operator`
- `parallel_assignment`
- `percent_format`
- `print_arg_count`
- `required_variable`
- `return_required`
- `set_call`
- `set_literal`
- `slice`
- `swap_assignment`
- `subscript`
- `syntax_node`
- `try_except`
- `unary_operator`
- `with_open`
- `with_statement`
- `aug_assign_operator`
- `nested_for`

## 8. 当前内置规则目录

### 8.1 输出函数

- 必须调用 `print()`
- `print` 调用次数至少 N 次
- `print` 调用次数至多 N 次
- 必须使用 `print` 的 `sep` 参数
- `print.sep` 必须等于指定值
- 必须使用 `print` 的 `end` 参数
- `print.end` 必须等于指定值
- 至少有一次 `print` 包含 N 个及以上输出对象
- 至多允许一次 `print` 包含 N 个及以上输出对象

### 8.2 输入函数

- 必须调用 `input()`
- `input` 调用次数至少 N 次
- `input` 调用次数至多 N 次
- 必须调用 `int()`
- 必须调用 `float()`
- 输入题必须使用 `input()`

### 8.3 变量赋值

- 必须使用变量赋值
- 变量赋值至少 N 次
- 变量赋值至多 N 次
- 变量赋值恰好 N 次
- 必须使用指定变量名
- 禁止使用指定变量名
- 必须使用同步赋值
- 同步赋值至少 N 次
- 同步赋值恰好 N 次
- 必须使用连锁赋值
- 必须使用交换赋值

### 8.4 运算符

- 必须使用加法 `+`
- 必须使用减法 `-`
- 必须使用乘法 `*`
- 必须使用除法 `/`
- 必须使用整除 `//`
- 必须使用取余 `%`
- 必须使用幂运算 `**`
- 必须使用复合赋值 `+=`
- 必须使用复合赋值 `-=`

### 8.5 比较运算符

- 必须使用 `==`
- 必须使用 `!=`
- 必须使用 `>`
- 必须使用 `>=`
- 必须使用 `<`
- 必须使用 `<=`
- 必须使用链式区间判断，例如 `60 <= score < 90`

### 8.6 逻辑运算符

- 必须使用 `and`
- 必须使用 `or`
- 必须使用 `not`

### 8.7 分支结构

- 必须使用 `if`
- `if` 至少出现 N 次
- `if` 至多出现 N 次
- `if` 恰好出现 N 次
- 必须使用 `else`
- 必须使用 `elif`

### 8.8 循环结构

- 必须使用 `for`
- `for` 至少出现 N 次
- `for` 至多出现 N 次
- `for` 恰好出现 N 次
- 必须使用 `while`
- `while` 至少出现 N 次
- `while` 至多出现 N 次
- `while` 恰好出现 N 次
- 必须使用 `break`
- 必须使用 `continue`
- 必须使用嵌套 `for`

### 8.9 字符串

- 必须调用 `str()`
- 必须调用 `len()`
- 必须使用 `f-string`
- 必须使用 `format()`
- 必须使用 `%` 格式化
- 必须使用保留小数格式，例如 `.2f`
- 必须使用补零格式，例如 `03d`
- 必须使用百分比格式，例如 `.2%`
- 必须使用 `split()`
- 必须使用 `join()`
- 必须使用 `strip()`
- 必须使用 `replace()`
- 必须使用 `find()`
- 必须使用 `count()`
- 必须使用 `upper()`
- 必须使用 `lower()`
- 必须使用 `startswith()`
- 必须使用 `endswith()`

### 8.10 列表

- 必须创建列表
- 必须使用列表字面量 `[]`
- 必须使用 `list()`
- 必须使用列表索引
- 必须使用列表切片
- 必须遍历列表
- 必须使用列表推导式
- 必须使用 `sorted()`
- 必须使用 `append()`
- 必须使用 `insert()`
- 必须使用 `pop()`
- 必须使用 `remove()`
- 必须使用 `sort()`

### 8.11 字典

- 必须创建字典
- 必须使用字典字面量 `{}`
- 必须使用 `dict()`
- 必须使用字典键访问
- 必须使用 `get()`
- 必须使用 `keys()`
- 必须使用 `values()`
- 必须使用 `items()`
- 必须遍历字典

### 8.12 集合

- 必须创建集合
- 必须使用 `set()`
- 必须使用集合去重
- 必须使用交集 `&`
- 必须使用并集 `|`
- 必须使用差集 `-`

### 8.13 函数定义

- 必须定义函数 `def`
- 函数定义至少 N 个
- 函数定义至多 N 个
- 函数定义恰好 N 个
- 必须使用 `return`
- 必须定义指定名称的函数
- 必须调用自定义函数
- 函数参数至少 N 个
- 函数参数至多 N 个
- 必须使用默认参数
- 禁止函数中只 `print` 不 `return`

### 8.14 异常处理

- 必须使用 `try-except`
- 必须使用 `except`
- 必须使用 `try-else`
- 必须使用 `finally`
- 必须捕获 `ValueError`
- 必须捕获 `ZeroDivisionError`

### 8.15 文件操作

- 必须使用 `with`
- 必须使用 `with open()`
- 必须使用 `open()`
- 必须使用 `read()`
- 必须使用 `readline()`
- 必须使用 `readlines()`
- 必须使用 `write()`
- 必须使用 `open(..., mode=\"a\")`

### 8.16 禁止写法

- 禁止 `import`
- 禁止 `eval()`
- 禁止 `exec()`
- 禁止 `open()`
- 禁止使用 `os`
- 禁止使用 `subprocess`
- 禁止直接输出完整目标答案
- 禁止直接输出公开样例答案
- 禁止使用指定函数
- 禁止使用指定方法

### 8.17 import 与模块

- 必须 `import` 指定模块
- 禁止 `import` 指定模块
- 必须 `from ... import ...`
- 禁止 `from ... import ...`

## 9. 提交结果展示语义

当学生输出正确但 AST 不满足时，提交详情页会显示：

- 标题：通过
- 提示：你已通过本题，但未满星
- 列出未完成的满星目标

当学生输出正确且 AST 满足时，提交详情页会显示：

- 标题：满星通过
- 提示：输出正确且完成了本题的语法目标

## 10. 当前边界与限制

- “遍历列表 / 遍历字典”依赖静态推断，不是完整类型系统。
- “禁止使用某变量”当前主要检查赋值时出现的变量名。
- “禁止直接输出答案”当前主要识别 `print("完整固定答案")` 这种字面量输出。
- AST 禁止类规则只是教学型检查，不替代沙箱安全限制。
- 当前只支持规则“全部满足”模式，尚未启用 `any` 模式。

## 11. 后续扩展建议

- 为规则组合补充 `logic_mode`
- 为某些规则增加系统默认建议文案
- 为“禁止硬编码答案”补充更强的字符串拼接识别
- 为教师端增加模板搜索、批量启停、规则复制
- 为学生端增加 AST 统计可视化调试信息
