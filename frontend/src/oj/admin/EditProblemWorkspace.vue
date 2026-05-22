<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { postForm } from './api.js';

const props = defineProps({
  problem: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['saved', 'navigateFiles']);
const form = reactive({});
const saving = ref(false);
const statementEditor = ref(null);
let easyMde = null;

const statLabels = [
  ['题目 UID', 'uid'],
  ['题号', 'code'],
  ['测试点', 'testcaseCount'],
  ['数据文件', 'dataFileCount'],
  ['附加文件', 'assetFileCount'],
  ['下一组号', 'nextCaseNumber'],
];

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
  });
  if (easyMde) easyMde.value(form.statement_md);
}

function statValue(key) {
  if (key in props.problem) return props.problem[key];
  return props.problem.stats?.[key] ?? '-';
}

async function initEditor() {
  await nextTick();
  if (!statementEditor.value || !window.EasyMDE || easyMde) return;
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
  Object.entries(form).forEach(([key, value]) => {
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

watch(
  () => props.problem,
  (problem) => {
    resetForm(problem);
    initEditor();
  },
  { immediate: true },
);

onMounted(initEditor);

onBeforeUnmount(() => {
  if (easyMde) {
    easyMde.toTextArea();
    easyMde = null;
  }
});
</script>

<template>
  <form class="workbench-shell p-6 md:p-8 flex flex-col gap-8" @submit.prevent="saveProblem">
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

    <section class="bench-card p-5 flex flex-col gap-5">
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
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
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

    <section class="flex flex-col gap-4">
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
        <button type="button" class="btn btn-outline rounded-2xl px-6" @click="emit('navigateFiles', problem.id)">文件管理</button>
        <button type="submit" class="btn btn-primary rounded-2xl px-8" :disabled="saving">{{ saving ? '保存中...' : '保存题目基础配置' }}</button>
      </div>
    </div>
  </form>
</template>
