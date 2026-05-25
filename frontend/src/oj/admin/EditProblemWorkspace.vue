<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { postForm, requestJson } from './api.js';
import { DIFFICULTY_OPTIONS } from '../difficulty.js';

const props = defineProps({
  problem: {
    type: Object,
    required: true,
  },
  workspaceMode: {
    type: String,
    default: 'edit',
  },
});

const emit = defineEmits(['saved', 'navigateFiles']);
const form = reactive({});
const saving = ref(false);
const statementEditor = ref(null);
const selectedCategory = ref('');
const selectedTemplateId = ref('');
let easyMde = null;

const statLabels = [
  ['题目 UID', 'uid'],
  ['题号', 'code'],
  ['测试点', 'testcaseCount'],
  ['数据文件', 'dataFileCount'],
  ['附加文件', 'assetFileCount'],
  ['AST 规则', 'astRuleCount'],
];

const astRules = ref([]);
const isAstMode = computed(() => props.workspaceMode === 'ast');
const isEditMode = computed(() => props.workspaceMode === 'edit');

const astTemplates = computed(() => props.problem.astConfig?.templates || []);
const astTemplatesById = computed(() => {
  const mapped = new Map();
  astTemplates.value.forEach((template) => {
    mapped.set(String(template.id), template);
  });
  return mapped;
});

const groupedTemplates = computed(() => {
  const groups = new Map();
  astTemplates.value.forEach((template) => {
    const key = template.category || '未分类';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(template);
  });
  return Array.from(groups.entries())
    .map(([category, templates]) => ({
      category,
      templates: [...templates].sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0) || String(a.name).localeCompare(String(b.name), 'zh-Hans-CN')),
    }))
    .sort((a, b) => a.templates[0]?.sortOrder - b.templates[0]?.sortOrder);
});

const categoryOptions = computed(() => groupedTemplates.value.map((group) => group.category));
const filteredTemplates = computed(() => {
  const match = groupedTemplates.value.find((group) => group.category === selectedCategory.value);
  return match?.templates || [];
});

function resetForm(problem) {
  Object.assign(form, {
    problem_code: problem.code || '',
    title: problem.title || '',
    slug: problem.slug || '',
    difficulty: problem.difficulty || 'medium',
    is_visible: problem.visible ? '1' : '0',
    time_limit_ms: problem.timeLimitMs || 2000,
    memory_limit_mb: problem.memoryLimitMb || 256,
    source: problem.source || '',
    allowed_languages: problem.allowedLanguages || 'python, cpp, c',
    statement_md: problem.statementMd || '',
    ast_check_enabled: problem.astConfig?.enabled ? '1' : '0',
  });
  astRules.value = (problem.astConfig?.rules || []).map((rule, index) => hydrateRule(rule, index));
  if (easyMde) easyMde.value(form.statement_md);
}

function statValue(key) {
  if (key in props.problem) return props.problem[key];
  return props.problem.stats?.[key] ?? '-';
}

function templateFor(rule) {
  return astTemplatesById.value.get(String(rule.templateId || '')) || null;
}

function parseTemplateDefaults(template) {
  const defaults = template?.defaultParams || {};
  return {
    editableFields: defaults.editable_fields || [],
    fieldLabels: defaults.field_labels || {},
    fieldTypes: defaults.field_types || {},
    minCount: defaults.min_count ?? null,
    maxCount: defaults.max_count ?? null,
    requiredValue: defaults.required_value ?? '',
    params: Object.fromEntries(
      Object.entries(defaults).filter(([key]) => !['editable_fields', 'field_labels', 'field_types', 'min_count', 'max_count', 'required_value'].includes(key)),
    ),
  };
}

function buildRuleDescription(ruleLike) {
  const ruleType = ruleLike.ruleType || '';
  const target = ruleLike.target || '';
  const minCount = ruleLike.minCount;
  const maxCount = ruleLike.maxCount;
  const requiredValue = ruleLike.requiredValue;
  const params = ruleLike.params || {};

  const operatorLabels = {
    Add: '+',
    Sub: '-',
    Mult: '*',
    Div: '/',
    FloorDiv: '//',
    Mod: '%',
    Pow: '**',
    BitAnd: '&',
    BitOr: '|',
  };
  const compareLabels = { Eq: '==', NotEq: '!=', Gt: '>', GtE: '>=', Lt: '<', LtE: '<=' };
  const boolLabels = { And: 'and', Or: 'or' };

  if (ruleType === 'function_call') {
    if (target === '__user_defined__') return '本题要求调用自定义函数。';
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined && Number(minCount) === Number(maxCount)) {
      return `本题要求 ${target}() 恰好调用 ${minCount} 次。`;
    }
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined) {
      return `本题要求 ${target}() 调用次数在 ${minCount} 到 ${maxCount} 次之间。`;
    }
    if (minCount !== null && minCount !== undefined) {
      if (Number(minCount) <= 1) return `本题要求调用 ${target}()。`;
      return `本题要求至少调用 ${minCount} 次 ${target}()。`;
    }
    if (maxCount !== null && maxCount !== undefined) return `本题要求 ${target}() 调用次数不超过 ${maxCount} 次。`;
    return `本题要求调用 ${target}()。`;
  }

  if (ruleType === 'syntax_node') {
    const labels = {
      If: 'if 分支结构',
      For: 'for 循环',
      While: 'while 循环',
      FunctionDef: '函数定义',
      Return: 'return',
      Break: 'break',
      Continue: 'continue',
    };
    const label = labels[target] || target;
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined && Number(minCount) === Number(maxCount)) {
      return `本题要求 ${label} 恰好出现 ${minCount} 次。`;
    }
    if (minCount !== null && minCount !== undefined) {
      if (target === 'If' && Number(minCount) <= 1) return '本题要求使用 if 分支结构。';
      if (target === 'For' && Number(minCount) <= 1) return '本题要求使用 for 循环。';
      if (target === 'While' && Number(minCount) <= 1) return '本题要求使用 while 循环。';
      if (target === 'FunctionDef' && Number(minCount) <= 1) return '本题要求定义函数。';
      if (['Return', 'Break', 'Continue'].includes(target) && Number(minCount) <= 1) return `本题要求使用 ${label}。`;
      return `本题要求 ${label} 至少出现 ${minCount} 次。`;
    }
    if (maxCount !== null && maxCount !== undefined) return `本题要求 ${label} 至多出现 ${maxCount} 次。`;
    return `本题要求使用 ${label}。`;
  }

  if (ruleType === 'function_def') {
    if (minCount !== null && minCount !== undefined && Number(minCount) <= 1 && (maxCount === null || maxCount === undefined)) {
      return '本题要求定义函数。';
    }
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined) {
      return `本题要求函数定义数量在 ${minCount} 到 ${maxCount} 个之间。`;
    }
    if (minCount !== null && minCount !== undefined) return `本题要求至少定义 ${minCount} 个函数。`;
    if (maxCount !== null && maxCount !== undefined) return `本题要求函数定义数量不超过 ${maxCount} 个。`;
    return '本题要求定义函数。';
  }

  if (ruleType === 'assign' || ruleType === 'assign_count') {
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined && Number(minCount) === Number(maxCount)) {
      return `本题要求变量赋值恰好出现 ${minCount} 次。`;
    }
    if (minCount !== null && minCount !== undefined && Number(minCount) <= 1 && (maxCount === null || maxCount === undefined)) {
      return '本题要求使用变量保存数据。';
    }
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined) return `本题要求变量赋值次数在 ${minCount} 到 ${maxCount} 次之间。`;
    if (minCount !== null && minCount !== undefined) return `本题要求至少出现 ${minCount} 次变量赋值。`;
    if (maxCount !== null && maxCount !== undefined) return `本题要求变量赋值次数不超过 ${maxCount} 次。`;
    return '本题要求使用变量保存数据。';
  }

  if (ruleType === 'required_variable') return `本题要求使用变量名 ${params.variable_name || requiredValue || 'score'}。`;
  if (ruleType === 'forbid_variable') return `本题不允许使用变量名 ${params.variable_name || requiredValue || 'temp'}。`;
  if (ruleType === 'operator') return `本题要求使用 ${operatorLabels[target] || target} 运算符。`;
  if (ruleType === 'aug_assign_operator') return `本题要求使用复合赋值 ${operatorLabels[target] || target}=。`;
  if (ruleType === 'compare_operator') return `本题要求使用 ${compareLabels[target] || target} 比较运算符。`;
  if (ruleType === 'chained_compare') return '本题要求使用链式区间判断，例如 60 <= score < 90。';
  if (ruleType === 'bool_operator') return `本题要求使用 ${boolLabels[target] || target} 连接多个条件。`;
  if (ruleType === 'unary_operator') return '本题要求使用 not 进行取反判断。';

  if (ruleType === 'method_call') {
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined && Number(minCount) === Number(maxCount)) {
      return `本题要求 ${target}() 方法恰好调用 ${minCount} 次。`;
    }
    if (minCount !== null && minCount !== undefined) {
      if (Number(minCount) <= 1) return `本题要求使用 ${target}() 方法。`;
      return `本题要求至少使用 ${minCount} 次 ${target}() 方法。`;
    }
    if (maxCount !== null && maxCount !== undefined) return `本题要求 ${target}() 调用次数不超过 ${maxCount} 次。`;
    return `本题要求使用 ${target}() 方法。`;
  }

  if (ruleType === 'keyword_arg') {
    const keyword = params.keyword || 'sep';
    if (requiredValue !== '' && requiredValue !== null && requiredValue !== undefined) {
      return `本题要求使用 print() 的 ${keyword} 参数，且 ${keyword} 的值为 ${JSON.stringify(requiredValue)}。`;
    }
    return `本题要求使用 print() 的 ${keyword} 参数。`;
  }

  if (ruleType === 'print_arg_count') {
    const argCount = params.arg_count || 1;
    if (maxCount !== null && maxCount !== undefined) return `本题至多允许 ${maxCount} 次 print() 包含 ${argCount} 个及以上输出对象。`;
    return `本题要求至少有一次 print() 包含 ${argCount} 个及以上输出对象。`;
  }

  if (ruleType === 'branch_feature') {
    if (target === 'else') return '本题要求使用 else 分支。';
    if (target === 'elif') return '本题要求使用 elif 分支。';
  }

  if (ruleType === 'f_string') return '本题要求使用 f-string 完成格式化输出。';
  if (ruleType === 'format_method') return '本题要求使用 format() 完成格式化输出。';
  if (ruleType === 'percent_format') return '本题要求使用 % 格式化输出。';
  if (ruleType === 'format_spec') return `本题要求使用格式控制 ${requiredValue || params.format_spec || ''}。`;
  if (ruleType === 'list_literal') return '本题要求使用列表字面量 []。';
  if (ruleType === 'list_call') return '本题要求使用 list() 创建列表。';
  if (ruleType === 'dict_literal') return '本题要求使用字典字面量 {}。';
  if (ruleType === 'dict_call') return '本题要求使用 dict() 创建字典。';
  if (ruleType === 'set_literal') return '本题要求使用集合字面量创建集合。';
  if (ruleType === 'set_call') return '本题要求使用 set() 创建集合。';
  if (ruleType === 'subscript') return target === 'dict' ? '本题要求使用字典键访问内容。' : '本题要求使用列表下标访问元素。';
  if (ruleType === 'slice') return '本题要求使用切片。';
  if (ruleType === 'list_comprehension') return '本题要求使用列表推导式。';
  if (ruleType === 'iterate_collection') return target === 'dict' ? '本题要求使用 for 循环遍历字典。' : '本题要求使用 for 循环遍历列表。';
  if (ruleType === 'parallel_assignment') {
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined && Number(minCount) === Number(maxCount)) return `本题要求同步赋值恰好出现 ${minCount} 次。`;
    if (minCount !== null && minCount !== undefined && Number(minCount) <= 1 && (maxCount === null || maxCount === undefined)) return '本题要求使用同步赋值。';
    if (minCount !== null && minCount !== undefined) return `本题要求至少使用 ${minCount} 次同步赋值。`;
    if (maxCount !== null && maxCount !== undefined) return `本题要求同步赋值不超过 ${maxCount} 次。`;
    return '本题要求使用同步赋值。';
  }
  if (ruleType === 'chain_assignment') return '本题要求使用连锁赋值。';
  if (ruleType === 'swap_assignment') return '本题要求使用交换赋值，例如 a, b = b, a。';
  if (ruleType === 'nested_for') return '本题要求使用嵌套 for 循环。';
  if (ruleType === 'function_def_name') return `本题要求定义函数 ${params.function_name || requiredValue || 'check_score'}。`;
  if (ruleType === 'function_args_count') {
    if (minCount !== null && minCount !== undefined && maxCount !== null && maxCount !== undefined) return `本题要求函数参数数量在 ${minCount} 到 ${maxCount} 个之间。`;
    if (minCount !== null && minCount !== undefined) return `本题要求函数至少包含 ${minCount} 个参数。`;
    if (maxCount !== null && maxCount !== undefined) return `本题要求函数参数数量不超过 ${maxCount} 个。`;
  }
  if (ruleType === 'default_args') return '本题要求函数使用默认参数。';
  if (ruleType === 'return_required') return '本题要求函数使用 return 返回结果。';
  if (ruleType === 'try_except') {
    if (target === 'try') return '本题要求使用 try-except 处理异常。';
    if (target === 'except') return '本题要求使用 except 分支处理异常。';
    if (target === 'else') return '本题要求在异常处理中使用 else。';
    if (target === 'finally') return '本题要求在异常处理中使用 finally。';
  }
  if (ruleType === 'exception_handler') return `本题要求捕获 ${params.exception_name || requiredValue || target}。`;
  if (ruleType === 'with_statement') return '本题要求使用 with 语句。';
  if (ruleType === 'with_open') return '本题要求使用 with open()。';
  if (ruleType === 'open_mode') return `本题要求使用 open() 的 ${requiredValue || params.mode || target} 模式。`;
  if (ruleType === 'import_required') return `本题要求导入 ${(params.module || requiredValue || target)} 模块。`;
  if (ruleType === 'import_forbid') return `本题不允许导入 ${(params.module || requiredValue || target)} 模块。`;
  if (ruleType === 'import_from_required') return `本题要求使用 from ${(params.module || requiredValue || target)} import ...。`;
  if (ruleType === 'import_from_forbid') return `本题不允许使用 from ${(params.module || requiredValue || target)} import ...。`;
  if (ruleType === 'forbid_literal_output') return target === 'sample' ? '本题要求不要直接输出公开样例答案。' : '本题要求不要直接输出完整目标答案。';

  if (ruleType === 'forbid') {
    const labels = { import: 'import', eval: 'eval()', exec: 'exec()', open: 'open()', os: 'os 模块', subprocess: 'subprocess 模块' };
    return `本题要求不要使用 ${labels[target] || target}。`;
  }

  return '本题包含一条语法目标。';
}

function syncAutoText(rule) {
  const generated = buildRuleDescription(rule);
  if (rule._descriptionAuto) rule.description = generated;
  if (rule._failMessageAuto) rule.failMessage = generated;
}

function hydrateRule(rule, index = 0) {
  const hydrated = {
    id: rule.id ?? null,
    templateId: rule.templateId ? String(rule.templateId) : '',
    ruleType: rule.ruleType || '',
    target: rule.target || '',
    minCount: rule.minCount ?? null,
    maxCount: rule.maxCount ?? null,
    requiredValue: rule.requiredValue ?? '',
    params: { ...(rule.params || {}) },
    description: rule.description || '',
    failMessage: rule.failMessage || '',
    enabled: rule.enabled !== false,
    sortOrder: rule.sortOrder ?? index,
    _descriptionAuto: false,
    _failMessageAuto: false,
  };
  const generated = buildRuleDescription(hydrated);
  hydrated._descriptionAuto = !hydrated.description || hydrated.description === generated;
  hydrated._failMessageAuto = !hydrated.failMessage || hydrated.failMessage === hydrated.description || hydrated.failMessage === generated;
  syncAutoText(hydrated);
  return hydrated;
}

function buildRuleFromTemplate(template) {
  const defaults = parseTemplateDefaults(template);
  const rule = hydrateRule({
    templateId: String(template.id),
    ruleType: template.ruleType,
    target: template.target,
    minCount: defaults.minCount,
    maxCount: defaults.maxCount,
    requiredValue: defaults.requiredValue,
    params: defaults.params,
    enabled: true,
  }, astRules.value.length);
  return rule;
}

function applyTemplate(rule, templateId) {
  const template = astTemplatesById.value.get(String(templateId));
  if (!template) return;
  const defaults = parseTemplateDefaults(template);
  rule.templateId = String(template.id);
  rule.ruleType = template.ruleType;
  rule.target = template.target;
  rule.minCount = defaults.minCount;
  rule.maxCount = defaults.maxCount;
  rule.requiredValue = defaults.requiredValue;
  rule.params = defaults.params;
  rule.enabled = true;
  rule._descriptionAuto = true;
  rule._failMessageAuto = true;
  syncAutoText(rule);
}

function addSelectedTemplate() {
  const template = astTemplatesById.value.get(String(selectedTemplateId.value || ''));
  if (!template) return;
  astRules.value.push(buildRuleFromTemplate(template));
  selectedTemplateId.value = '';
  refreshSortOrder();
}

function removeRule(index) {
  astRules.value.splice(index, 1);
  refreshSortOrder();
}

function moveRule(index, offset) {
  const nextIndex = index + offset;
  if (nextIndex < 0 || nextIndex >= astRules.value.length) return;
  const [item] = astRules.value.splice(index, 1);
  astRules.value.splice(nextIndex, 0, item);
  refreshSortOrder();
}

function refreshSortOrder() {
  astRules.value.forEach((rule, index) => {
    rule.sortOrder = index;
  });
}

function numericValueOrNull(value) {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function updateRuleNumber(rule, key, value) {
  rule[key] = value === '' ? null : Number(value);
  syncAutoText(rule);
}

function updateRuleParam(rule, key, value) {
  rule.params = { ...rule.params, [key]: value };
  syncAutoText(rule);
}

function editableFields(rule) {
  return parseTemplateDefaults(templateFor(rule)).editableFields || [];
}

function fieldLabel(rule, field) {
  const defaults = parseTemplateDefaults(templateFor(rule));
  const labels = {
    min_count: '最少次数',
    max_count: '最多次数',
    exact_count: '精确次数',
    required_value: '指定值',
    arg_count: '输出对象数量阈值',
    variable_name: '变量名',
    function_name: '函数名',
    module: '模块名',
    exception_name: '异常类型',
  };
  return defaults.fieldLabels?.[field] || labels[field] || field;
}

function fieldType(rule, field) {
  const defaults = parseTemplateDefaults(templateFor(rule));
  if (defaults.fieldTypes?.[field]) return defaults.fieldTypes[field];
  return ['min_count', 'max_count', 'exact_count', 'arg_count'].includes(field) ? 'number' : 'text';
}

function fieldValue(rule, field) {
  if (field === 'min_count') return rule.minCount ?? '';
  if (field === 'max_count') return rule.maxCount ?? '';
  if (field === 'exact_count') {
    if (rule.minCount !== null && rule.minCount !== undefined && rule.maxCount !== null && rule.maxCount !== undefined && Number(rule.minCount) === Number(rule.maxCount)) {
      return rule.minCount;
    }
    return rule.params?.exact_count ?? '';
  }
  if (field === 'required_value') return rule.requiredValue ?? '';
  return rule.params?.[field] ?? '';
}

function updateEditableField(rule, field, rawValue) {
  if (field === 'min_count') {
    updateRuleNumber(rule, 'minCount', rawValue);
    return;
  }
  if (field === 'max_count') {
    updateRuleNumber(rule, 'maxCount', rawValue);
    return;
  }
  if (field === 'required_value') {
    rule.requiredValue = rawValue;
    syncAutoText(rule);
    return;
  }
  if (field === 'exact_count') {
    const nextValue = rawValue === '' ? null : Number(rawValue);
    rule.minCount = nextValue;
    rule.maxCount = nextValue;
    rule.params = { ...(rule.params || {}), exact_count: nextValue };
    syncAutoText(rule);
    return;
  }
  const nextValue = fieldType(rule, field) === 'number'
    ? (rawValue === '' ? null : Number(rawValue))
    : rawValue;
  updateRuleParam(rule, field, nextValue);
}

function serializeRulesForSave() {
  return astRules.value.map((rule, index) => ({
    templateId: rule.templateId ? Number(rule.templateId) : null,
    ruleType: rule.ruleType,
    target: rule.target,
    minCount: numericValueOrNull(rule.minCount),
    maxCount: numericValueOrNull(rule.maxCount),
    requiredValue: rule.requiredValue === '' ? null : rule.requiredValue,
    params: rule.params || {},
    description: (rule.description || '').trim(),
    failMessage: (rule.failMessage || '').trim(),
    enabled: rule.enabled !== false,
    sortOrder: index,
  }));
}

async function initEditor() {
  await nextTick();
  if (!isEditMode.value || !statementEditor.value || !window.EasyMDE || easyMde) return;
  easyMde = new window.EasyMDE({
    element: statementEditor.value,
    spellChecker: false,
    status: ['lines', 'words'],
    sideBySideFullscreen: false,
    renderingConfig: {
      singleLineBreaks: false,
      codeSyntaxHighlighting: true,
    },
    previewClass: ['editor-preview', 'prose', 'max-w-none'],
    placeholder: '在这里维护题面 Markdown...',
  });
  easyMde.value(form.statement_md || '');
  easyMde.codemirror.on('change', () => {
    form.statement_md = easyMde.value();
  });
}

async function saveProblem() {
  saving.value = true;
  const formData = new FormData();
  [
    'problem_code',
    'title',
    'slug',
    'difficulty',
    'is_visible',
    'time_limit_ms',
    'memory_limit_mb',
    'source',
    'allowed_languages',
    'statement_md',
  ].forEach((key) => {
    const value = form[key];
    formData.set(key, value ?? '');
  });

  try {
    const data = await postForm(props.problem.urls.edit, formData);
    if (data.problem) {
      emit('saved', data.problem);
      resetForm(data.problem);
    }
  } catch (error) {
    window.alert(error.message);
  } finally {
    saving.value = false;
  }
}

async function saveAstRules() {
  saving.value = true;
  try {
    const data = await requestJson(props.problem.astConfig.urls.save, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        enabled: form.ast_check_enabled === '1',
        rules: serializeRulesForSave(),
      }),
    });
    if (data.rules) {
      astRules.value = data.rules.map((rule, index) => hydrateRule(rule, index));
    }
    emit('saved', {
      ...props.problem,
      astConfig: {
        ...props.problem.astConfig,
        enabled: data.enabled,
        rules: data.rules || [],
      },
      stats: {
        ...props.problem.stats,
        astRuleCount: (data.rules || []).filter((rule) => rule.enabled !== false).length,
      },
    });
  } catch (error) {
    window.alert(error.message);
  } finally {
    saving.value = false;
  }
}

watch(
  () => props.problem,
  (problem) => {
    resetForm(problem);
    if (isEditMode.value) initEditor();
  },
  { immediate: true },
);

onMounted(() => {
  if (isEditMode.value) initEditor();
});

watch(
  () => props.workspaceMode,
  (mode) => {
    if (mode === 'edit') initEditor();
  },
);

onBeforeUnmount(() => {
  if (easyMde) {
    easyMde.toTextArea();
    easyMde = null;
  }
});
</script>

<template>
  <form class="workbench-shell p-6 md:p-8 flex flex-col gap-8" @submit.prevent="isAstMode ? saveAstRules() : saveProblem()">
    <section class="bench-card p-5 flex flex-col gap-5">
      <div>
        <p class="text-xs font-black tracking-[0.2em] text-stone-400 mb-2">状态概览</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">题目当前状态</h2>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <div v-for="[label, key] in statLabels" :key="key" class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">{{ label }}</div>
          <div class="text-[2.6rem] leading-none whitespace-nowrap font-black text-stone-800 dark:text-stone-100 font-mono">{{ statValue(key) }}</div>
        </div>
      </div>
      <p class="text-sm text-stone-500 dark:text-stone-400">最近更新：{{ problem.updatedAt }}</p>
    </section>

    <section v-if="isEditMode" class="bench-card p-5 flex flex-col gap-5">
      <div>
        <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Core Meta</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">基础信息</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="form-control">
          <span class="label-text font-bold mb-2">题目编号</span>
          <input v-model="form.problem_code" type="text" class="input input-bordered rounded-2xl font-mono font-black text-lg uppercase" required>
          <span class="text-xs text-stone-400 mt-2">必填且唯一，例如 P1000、P1001、Q1001。</span>
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">题目标题</span>
          <input v-model="form.title" type="text" class="input input-bordered rounded-2xl font-bold text-lg" required>
        </label>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="form-control">
          <span class="label-text font-bold mb-2">Slug</span>
          <input v-model="form.slug" type="text" class="input input-bordered rounded-2xl font-mono">
        </label>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <label class="form-control">
          <span class="label-text font-bold mb-2">难度</span>
          <select v-model="form.difficulty" class="select select-bordered rounded-2xl">
            <option v-for="option in DIFFICULTY_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">可见性</span>
          <select v-model="form.is_visible" class="select select-bordered rounded-2xl">
            <option value="1">公开</option>
            <option value="0">隐藏</option>
          </select>
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">时限(ms)</span>
          <input v-model.number="form.time_limit_ms" type="number" min="100" class="input input-bordered rounded-2xl">
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">内存(MB)</span>
          <input v-model.number="form.memory_limit_mb" type="number" min="16" class="input input-bordered rounded-2xl">
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">来源</span>
          <input v-model="form.source" type="text" class="input input-bordered rounded-2xl">
        </label>
      </div>
      <label class="form-control">
        <span class="label-text font-bold mb-2">允许语言</span>
        <input v-model="form.allowed_languages" type="text" class="input input-bordered rounded-2xl">
      </label>
    </section>

    <section v-if="isAstMode" class="bench-card p-5 flex flex-col gap-5">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-emerald-600 mb-2">Teaching AST</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">教学语法检查 AST</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-2">输出正确后，未满足这些语法目标会判为 AC；全部满足或无规则时判为 PAC。</p>
        </div>
        <label class="flex items-center gap-3 rounded-2xl bg-stone-100 dark:bg-white/5 px-4 py-3">
          <input v-model="form.ast_check_enabled" type="checkbox" true-value="1" false-value="0" class="toggle toggle-success">
          <span class="font-bold text-stone-700 dark:text-stone-200">启用 AST 检查</span>
        </label>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-[16rem,1fr,auto] gap-3 items-end">
        <label class="form-control">
          <span class="label-text font-bold mb-2">规则分类</span>
          <select v-model="selectedCategory" class="select select-bordered rounded-2xl">
            <option value="">请先选择分类</option>
            <option v-for="category in categoryOptions" :key="category" :value="category">{{ category }}</option>
          </select>
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-2">添加内置规则模板</span>
          <select v-model="selectedTemplateId" class="select select-bordered rounded-2xl">
            <option value="">请选择一条规则模板</option>
            <option v-for="template in filteredTemplates" :key="template.id" :value="String(template.id)">{{ template.name }}</option>
          </select>
        </label>
        <button type="button" class="btn btn-success rounded-2xl px-6" :disabled="!selectedTemplateId || !selectedCategory" @click="addSelectedTemplate">添加规则</button>
      </div>

      <div v-if="astRules.length" class="flex flex-col gap-4">
        <article v-for="(rule, index) in astRules" :key="`${rule.templateId}-${index}-${rule.id || 'new'}`" class="rounded-3xl border border-stone-200 dark:border-white/10 bg-stone-50/70 dark:bg-white/5 p-5 flex flex-col gap-4">
          <div class="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div class="text-xs uppercase tracking-[0.22em] text-stone-400 font-black">Rule {{ index + 1 }}</div>
              <div class="text-lg font-black text-stone-800 dark:text-stone-100">{{ templateFor(rule)?.name || '自定义规则' }}</div>
              <div class="text-sm text-stone-500 mt-1">{{ templateFor(rule)?.category || rule.ruleType }}</div>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <label class="flex items-center gap-2 text-sm font-bold text-stone-500">
                <input v-model="rule.enabled" type="checkbox" class="toggle toggle-sm toggle-success">
                启用
              </label>
              <button type="button" class="btn btn-sm btn-outline rounded-xl" :disabled="index === 0" @click="moveRule(index, -1)">上移</button>
              <button type="button" class="btn btn-sm btn-outline rounded-xl" :disabled="index === astRules.length - 1" @click="moveRule(index, 1)">下移</button>
              <button type="button" class="btn btn-sm btn-error btn-outline rounded-xl" @click="removeRule(index)">删除</button>
            </div>
          </div>

          <label class="form-control">
            <span class="label-text font-bold mb-2">规则模板</span>
            <select :value="rule.templateId" class="select select-bordered rounded-2xl" @change="applyTemplate(rule, $event.target.value)">
              <option value="">请选择规则模板</option>
              <optgroup v-for="group in groupedTemplates" :key="group.category" :label="group.category">
                <option v-for="template in group.templates" :key="template.id" :value="String(template.id)">{{ template.name }}</option>
              </optgroup>
            </select>
          </label>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label v-for="field in editableFields(rule)" :key="field" class="form-control">
              <span class="label-text font-bold mb-2">{{ fieldLabel(rule, field) }}</span>
              <input
                :value="fieldValue(rule, field)"
                :type="fieldType(rule, field)"
                :min="fieldType(rule, field) === 'number' ? 0 : null"
                class="input input-bordered rounded-2xl"
                @input="updateEditableField(rule, field, $event.target.value)"
              >
            </label>
          </div>

          <label class="form-control">
            <span class="label-text font-bold mb-2">展示给学生的中文描述</span>
            <textarea v-model="rule.description" rows="2" class="textarea textarea-bordered rounded-2xl" @input="rule._descriptionAuto = false"></textarea>
            <span class="text-xs text-stone-400 mt-2">如果不手动改，系统会根据模板和参数自动生成。</span>
          </label>

          <label class="form-control">
            <span class="label-text font-bold mb-2">未满足时的中文提示</span>
            <textarea v-model="rule.failMessage" rows="2" class="textarea textarea-bordered rounded-2xl" @input="rule._failMessageAuto = false"></textarea>
          </label>
        </article>
      </div>

      <div v-else class="rounded-2xl border border-dashed border-stone-300 dark:border-white/10 p-5 text-sm text-stone-500 dark:text-stone-400">
        还没有添加 AST 规则。若保持为空，学生输出正确时会直接获得 PAC。
      </div>
    </section>

    <section v-if="isEditMode" class="flex flex-col gap-4">
      <div>
        <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Markdown Statement</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">题面编辑器</h2>
        <p class="text-sm text-stone-500 dark:text-stone-400 mt-2">样例请直接写在题面里，代码块语言标记使用 `input1` / `output1`、`input2` / `output2`。</p>
      </div>
      <textarea ref="statementEditor" v-model="form.statement_md"></textarea>
    </section>

    <div class="flex items-center justify-between gap-4 flex-wrap pt-4 border-t border-stone-200 dark:border-white/10">
      <p class="text-sm text-stone-500 dark:text-stone-400 font-mono">uid={{ problem.uid }} / code={{ problem.code }} / slug={{ problem.slug }}</p>
      <div class="flex gap-3 flex-wrap">
        <button v-if="isEditMode" type="button" class="btn btn-outline rounded-2xl px-6" @click="emit('navigateFiles', problem.id)">文件管理</button>
        <button type="submit" class="btn btn-primary rounded-2xl px-8" :disabled="saving">
          {{ saving ? '保存中...' : (isAstMode ? '保存 AST 规则' : '保存题目基础配置') }}
        </button>
      </div>
    </div>
  </form>
</template>
