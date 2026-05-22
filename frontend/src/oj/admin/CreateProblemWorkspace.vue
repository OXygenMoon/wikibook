<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { postForm } from './api.js';

const props = defineProps({
  draft: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['created']);
const form = reactive({});
const creating = ref(false);
const importing = ref(false);
const statementEditor = ref(null);
const zipInput = ref(null);
let easyMde = null;

function resetForm(draft) {
  Object.assign(form, {
    problem_code: draft.code || '',
    title: draft.title || '',
    slug: draft.slug || '',
    difficulty: draft.difficulty || 'medium',
    is_visible: draft.visible ? '1' : '0',
    time_limit_ms: draft.timeLimitMs || 2000,
    memory_limit_mb: draft.memoryLimitMb || 256,
    source: draft.source || '',
    allowed_languages: draft.allowedLanguages || 'python,cpp,c',
    statement_md: draft.statementMd || '',
  });
  if (easyMde) easyMde.value(form.statement_md);
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
    placeholder: '在这里编写题面 Markdown...',
  });
  easyMde.value(form.statement_md || '');
  easyMde.codemirror.on('change', () => {
    form.statement_md = easyMde.value();
  });
}

async function createProblem() {
  creating.value = true;
  const formData = new FormData();
  Object.entries(form).forEach(([key, value]) => {
    formData.set(key, value ?? '');
  });

  try {
    const data = await postForm(props.draft.urls.create, formData);
    emit('created', data);
  } catch (error) {
    if (error.data?.draft) {
      resetForm(error.data.draft);
    }
    window.alert(error.message);
  } finally {
    creating.value = false;
  }
}

async function importZip() {
  const file = zipInput.value?.files?.[0];
  if (!file) {
    window.alert('先选择一个 zip 文件。');
    return;
  }

  importing.value = true;
  const formData = new FormData();
  formData.set('problem_zip', file);
  try {
    const data = await postForm(props.draft.urls.importZip, formData);
    emit('created', data);
  } catch (error) {
    window.alert(error.message);
  } finally {
    importing.value = false;
  }
}

watch(
  () => props.draft,
  (draft) => {
    resetForm(draft);
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
  <div class="flex flex-col gap-8">
    <section class="bench-card p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
      <div>
        <p class="text-xs font-black tracking-[0.26em] uppercase text-sky-600 mb-2">ZIP Import</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">从 zip 创建题目</h2>
        <p class="text-sm text-stone-500 dark:text-stone-400 mt-2">支持 `problem.json`、`statement.md`、以及 `testdata/1.in + 1.out` 这类测试数据文件对。</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
        <input ref="zipInput" type="file" accept=".zip,application/zip" class="file-input file-input-bordered rounded-2xl w-full sm:w-80">
        <button type="button" class="btn btn-info rounded-2xl px-6" :disabled="importing" @click="importZip">
          {{ importing ? '导入中...' : '导入 zip 并创建题目' }}
        </button>
      </div>
    </section>

    <form class="workbench-shell p-6 md:p-8 flex flex-col gap-8" @submit.prevent="createProblem">
      <div class="grid grid-cols-1 xl:grid-cols-[1.05fr,0.95fr] gap-8 items-start">
        <section class="bench-card p-5 flex flex-col gap-5">
          <div>
            <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Basic Meta</p>
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
              <span class="label-text font-bold mb-2">Slug（可选）</span>
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

        <section class="bench-card p-5 h-full flex flex-col justify-between gap-4">
          <div>
            <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Workflow</p>
            <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">创建后会发生什么</h2>
          </div>
          <div class="text-sm leading-8 text-stone-500 dark:text-stone-400">
            1. 先保存题目基础信息和 Markdown 题面。
            <br>2. 创建成功后跳转到题目工作台。
            <br>3. 再去“文件管理”批量创建 `1.in / 1.out`、上传图片和附件。
            <br>4. 数据文件写好后，会自动成为本题测试数据来源。
          </div>
          <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4 text-sm text-stone-500 dark:text-stone-400">
            题面里直接写样例即可。代码块语言标记使用 `input1 / output1`、`input2 / output2`，题目页会自动横向配对展示。
          </div>
        </section>
      </div>

      <section class="flex flex-col gap-4">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Markdown Statement</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">题面编辑器</h2>
        </div>
        <textarea ref="statementEditor" v-model="form.statement_md"></textarea>
      </section>

      <div class="flex items-center justify-between gap-4 flex-wrap pt-4 border-t border-stone-200 dark:border-white/10">
        <p class="text-sm text-stone-500 dark:text-stone-400 font-mono">create first, then split into edit + files workflow</p>
        <button type="submit" class="btn btn-primary rounded-2xl px-8" :disabled="creating">
          {{ creating ? '创建中...' : '创建题目并进入编辑页' }}
        </button>
      </div>
    </form>
  </div>
</template>
