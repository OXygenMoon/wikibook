<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { postForm, requestJson } from './api.js';

const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['saved']);
const form = reactive({});
const saving = ref(false);
const uploading = ref(false);
const descriptionEditor = ref(null);
const uploadInput = ref(null);
const classSearch = ref('');
const groupSearch = ref('');
const userSearch = ref('');
const managerSearch = ref('');
const problemSearch = ref('');
let easyMde = null;

function resetForm(workspace) {
  Object.assign(form, {
    title: workspace.form?.title || '',
    description_md: workspace.form?.descriptionMd || '',
    start_at: workspace.form?.startAt || '',
    end_at: workspace.form?.endAt || '',
    extension_days: workspace.form?.extensionDays || 0,
    visibility: workspace.form?.visibility || 'all',
    is_active: workspace.form?.isActive ? '1' : '0',
    selected_class_ids: [...(workspace.form?.selectedClassIds || [])],
    selected_group_ids: [...(workspace.form?.selectedGroupIds || [])],
    selected_user_ids: [...(workspace.form?.selectedUserIds || [])],
    selected_manager_ids: [...(workspace.form?.selectedManagerIds || [])],
    selected_problem_ids: [...(workspace.form?.selectedProblemIds || [])],
  });
  if (easyMde) easyMde.value(form.description_md);
}

async function initEditor() {
  await nextTick();
  if (!descriptionEditor.value || !window.EasyMDE || easyMde) return;
  easyMde = new window.EasyMDE({
    element: descriptionEditor.value,
    spellChecker: false,
    status: ['lines', 'words'],
    sideBySideFullscreen: false,
    renderingConfig: {
      singleLineBreaks: false,
      codeSyntaxHighlighting: true,
    },
    previewClass: ['editor-preview', 'prose', 'max-w-none'],
    placeholder: '在这里编写作业介绍 Markdown...',
  });
  easyMde.value(form.description_md || '');
  easyMde.codemirror.on('change', () => {
    form.description_md = easyMde.value();
  });
}

function matchesSearch(item, keyword, extra = []) {
  const q = keyword.trim().toLowerCase();
  if (!q) return true;
  return [item.label, ...(extra || [])]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(q));
}

const filteredClasses = computed(() =>
  (props.workspace.options?.classes || []).filter((item) => matchesSearch(item, classSearch.value)),
);
const filteredGroups = computed(() =>
  (props.workspace.options?.groups || []).filter((item) => matchesSearch(item, groupSearch.value)),
);
const filteredUsers = computed(() =>
  (props.workspace.options?.users || []).filter((item) => matchesSearch(item, userSearch.value, [item.username])),
);
const filteredManagers = computed(() =>
  (props.workspace.options?.users || []).filter((item) => matchesSearch(item, managerSearch.value, [item.username])),
);
const filteredProblems = computed(() =>
  (props.workspace.options?.problems || []).filter((item) => matchesSearch(item, problemSearch.value, [item.code, item.slug, item.difficulty])),
);

const selectedProblemCount = computed(() => form.selected_problem_ids.length);
const selectedScopeCount = computed(() => form.selected_class_ids.length + form.selected_group_ids.length + form.selected_user_ids.length);

function appendList(formData, name, values) {
  values.forEach((value) => formData.append(name, value));
}

async function saveAssignment() {
  saving.value = true;
  const formData = new FormData();
  formData.set('title', form.title || '');
  formData.set('description_md', form.description_md || '');
  formData.set('start_at', form.start_at || '');
  formData.set('end_at', form.end_at || '');
  formData.set('extension_days', form.extension_days ?? 0);
  formData.set('visibility', form.visibility || 'all');
  formData.set('is_active', form.is_active || '1');
  appendList(formData, 'class_ids', form.selected_class_ids);
  appendList(formData, 'group_ids', form.selected_group_ids);
  appendList(formData, 'user_ids', form.selected_user_ids);
  appendList(formData, 'manager_ids', form.selected_manager_ids);
  appendList(formData, 'problem_ids', form.selected_problem_ids);

  try {
    const data = await postForm(props.workspace.urls.submit, formData);
    if (data.assignmentForm) resetForm(data.assignmentForm);
    emit('saved', data);
  } catch (error) {
    if (error.data?.assignmentForm) resetForm(error.data.assignmentForm);
    window.alert(error.message);
  } finally {
    saving.value = false;
  }
}

async function uploadFiles() {
  const files = uploadInput.value?.files;
  if (!files?.length || !props.workspace.urls.uploadFiles) {
    window.alert('先选择要上传的文件。');
    return;
  }
  uploading.value = true;
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append('files', file));
  try {
    const data = await postForm(props.workspace.urls.uploadFiles, formData);
    emit('saved', data);
    if (uploadInput.value) uploadInput.value.value = '';
  } catch (error) {
    window.alert(error.message);
  } finally {
    uploading.value = false;
  }
}

async function deleteFile(file) {
  if (!window.confirm(`确认删除文件吗？\n${file.filename}`)) return;
  try {
    const data = await requestJson(file.urls.delete, { method: 'POST' });
    emit('saved', data);
  } catch (error) {
    window.alert(error.message);
  }
}

watch(
  () => props.workspace,
  (workspace) => {
    resetForm(workspace);
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
  <form class="workbench-shell p-6 md:p-8 flex flex-col gap-8" @submit.prevent="saveAssignment">
    <section v-if="workspace.assignment" class="bench-card p-5 flex flex-col gap-5">
      <div>
        <p class="text-xs font-black tracking-[0.2em] text-stone-400 mb-2">状态概览</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">作业当前状态</h2>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-4">
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">作业编号</div>
          <div class="text-[2.2rem] leading-none whitespace-nowrap font-black text-stone-800 dark:text-stone-100 font-mono">{{ workspace.assignment.id }}</div>
        </div>
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">题目数</div>
          <div class="text-[2.2rem] leading-none whitespace-nowrap font-black text-stone-800 dark:text-stone-100 font-mono">{{ workspace.assignment.problemCount }}</div>
        </div>
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">文件数</div>
          <div class="text-[2.2rem] leading-none whitespace-nowrap font-black text-stone-800 dark:text-stone-100 font-mono">{{ workspace.assignment.fileCount }}</div>
        </div>
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">可见范围</div>
          <div class="text-lg font-black text-stone-800 dark:text-stone-100">{{ workspace.assignment.targetText }}</div>
        </div>
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">状态</div>
          <div class="text-lg font-black" :class="workspace.assignment.isActive ? 'text-emerald-600' : 'text-stone-500'">
            {{ workspace.assignment.isActive ? '启用中' : '已关闭' }}
          </div>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 xl:grid-cols-[1.05fr,0.95fr] gap-8 items-start">
      <section class="bench-card p-5 flex flex-col gap-5">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Basic Meta</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">基础信息</h2>
        </div>

        <label class="form-control">
          <span class="label-text font-bold mb-2">标题</span>
          <input v-model="form.title" type="text" class="input input-bordered rounded-2xl font-bold text-lg" placeholder="例如：循环结构训练营（一）" required>
        </label>

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <label class="form-control">
            <span class="label-text font-bold mb-2">开始时间</span>
            <input v-model="form.start_at" type="datetime-local" class="input input-bordered rounded-2xl">
          </label>
          <label class="form-control">
            <span class="label-text font-bold mb-2">结束时间</span>
            <input v-model="form.end_at" type="datetime-local" class="input input-bordered rounded-2xl">
          </label>
          <label class="form-control">
            <span class="label-text font-bold mb-2">最长延期（日）</span>
            <input v-model.number="form.extension_days" type="number" min="0" class="input input-bordered rounded-2xl">
          </label>
          <label class="form-control">
            <span class="label-text font-bold mb-2">状态</span>
            <select v-model="form.is_active" class="select select-bordered rounded-2xl">
              <option value="1">启用</option>
              <option value="0">关闭</option>
            </select>
          </label>
        </div>

        <label class="form-control">
          <span class="label-text font-bold mb-2">可见范围</span>
          <select v-model="form.visibility" class="select select-bordered rounded-2xl">
            <option value="all">全部学生</option>
            <option value="restricted">指定班级 / 小组 / 学生</option>
          </select>
        </label>
      </section>

      <section class="bench-card p-5 flex flex-col gap-4">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Workflow</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">使用说明</h2>
        </div>
        <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4 text-sm leading-7 text-stone-500 dark:text-stone-400">
          1. 题单、开放范围、管理员和作业介绍都在这里集中维护。
          <br>2. 介绍支持 Markdown，可先保存再上传图片素材。
          <br>3. 隐藏题也可以放进作业里，学生会通过作业入口访问。
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
            <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2">已选题目</div>
            <div class="text-[2rem] leading-none font-black text-stone-800 dark:text-stone-100 font-mono">{{ selectedProblemCount }}</div>
          </div>
          <div class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
            <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2">指定范围</div>
            <div class="text-[2rem] leading-none font-black text-stone-800 dark:text-stone-100 font-mono">{{ selectedScopeCount }}</div>
          </div>
        </div>
      </section>
    </div>

    <section class="bench-card p-5 flex flex-col gap-6">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Targets</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">分配范围与管理员</h2>
        </div>
        <div class="text-sm text-stone-500 dark:text-stone-400">只有 `指定范围` 时，班级 / 小组 / 学生配置才会生效。</div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="flex flex-col gap-3">
          <label class="form-control">
            <span class="label-text font-bold mb-2">班级</span>
            <input v-model="classSearch" type="text" class="input input-bordered rounded-2xl" placeholder="筛选班级">
          </label>
          <div class="rounded-2xl border border-stone-200 dark:border-white/10 p-4 max-h-64 overflow-y-auto grid gap-3">
            <label v-for="item in filteredClasses" :key="`class-${item.id}`" class="flex items-center gap-3 text-sm font-semibold text-stone-700 dark:text-stone-200">
              <input v-model="form.selected_class_ids" type="checkbox" class="checkbox checkbox-sm" :value="item.id">
              <span>{{ item.label }}</span>
            </label>
            <div v-if="!filteredClasses.length" class="text-sm text-stone-400">没有匹配的班级。</div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <label class="form-control">
            <span class="label-text font-bold mb-2">小组</span>
            <input v-model="groupSearch" type="text" class="input input-bordered rounded-2xl" placeholder="筛选小组">
          </label>
          <div class="rounded-2xl border border-stone-200 dark:border-white/10 p-4 max-h-64 overflow-y-auto grid gap-3">
            <label v-for="item in filteredGroups" :key="`group-${item.id}`" class="flex items-center gap-3 text-sm font-semibold text-stone-700 dark:text-stone-200">
              <input v-model="form.selected_group_ids" type="checkbox" class="checkbox checkbox-sm" :value="item.id">
              <span>{{ item.label }}</span>
            </label>
            <div v-if="!filteredGroups.length" class="text-sm text-stone-400">没有匹配的小组。</div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <label class="form-control">
            <span class="label-text font-bold mb-2">指定学生</span>
            <input v-model="userSearch" type="text" class="input input-bordered rounded-2xl" placeholder="按姓名或用户名筛选">
          </label>
          <div class="rounded-2xl border border-stone-200 dark:border-white/10 p-4 max-h-72 overflow-y-auto grid gap-3">
            <label v-for="item in filteredUsers" :key="`user-${item.id}`" class="flex items-center gap-3 text-sm font-semibold text-stone-700 dark:text-stone-200">
              <input v-model="form.selected_user_ids" type="checkbox" class="checkbox checkbox-sm" :value="item.id">
              <span>{{ item.label }}</span>
              <span class="text-xs text-stone-400">@{{ item.username }}</span>
            </label>
            <div v-if="!filteredUsers.length" class="text-sm text-stone-400">没有匹配的学生。</div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <label class="form-control">
            <span class="label-text font-bold mb-2">作业管理员</span>
            <input v-model="managerSearch" type="text" class="input input-bordered rounded-2xl" placeholder="按姓名或用户名筛选">
          </label>
          <div class="rounded-2xl border border-stone-200 dark:border-white/10 p-4 max-h-72 overflow-y-auto grid gap-3">
            <label v-for="item in filteredManagers" :key="`manager-${item.id}`" class="flex items-center gap-3 text-sm font-semibold text-stone-700 dark:text-stone-200">
              <input v-model="form.selected_manager_ids" type="checkbox" class="checkbox checkbox-sm" :value="item.id">
              <span>{{ item.label }}</span>
              <span class="text-xs text-stone-400">@{{ item.username }}</span>
            </label>
            <div v-if="!filteredManagers.length" class="text-sm text-stone-400">没有匹配的管理员。</div>
          </div>
        </div>
      </div>
    </section>

    <section class="bench-card p-5 flex flex-col gap-4">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Problem Set</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">题目清单</h2>
        </div>
        <div class="text-sm text-stone-500 dark:text-stone-400">已选 {{ selectedProblemCount }} 道题</div>
      </div>
      <label class="form-control">
        <span class="label-text font-bold mb-2">筛选题目</span>
        <input v-model="problemSearch" type="text" class="input input-bordered rounded-2xl" placeholder="输入题号、标题或 slug">
      </label>
      <div class="rounded-2xl border border-stone-200 dark:border-white/10 p-4 max-h-96 overflow-y-auto grid gap-3">
        <label v-for="item in filteredProblems" :key="`problem-${item.id}`" class="flex items-center gap-3 text-sm font-semibold text-stone-700 dark:text-stone-200">
          <input v-model="form.selected_problem_ids" type="checkbox" class="checkbox checkbox-sm" :value="item.id">
          <span class="font-mono">{{ item.code }}</span>
          <span>{{ item.title }}</span>
          <span class="oj-pill" :class="item.difficulty === 'easy' ? 'bg-emerald-100 text-emerald-700' : item.difficulty === 'hard' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'">
            {{ item.difficulty }}
          </span>
        </label>
        <div v-if="!filteredProblems.length" class="text-sm text-stone-400">没有匹配的题目。</div>
      </div>
    </section>

    <section class="flex flex-col gap-4">
      <div>
        <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Markdown Intro</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">作业介绍</h2>
      </div>
      <textarea ref="descriptionEditor" v-model="form.description_md"></textarea>
    </section>

    <section class="bench-card p-5 flex flex-col gap-4">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.26em] uppercase text-stone-400 mb-2">Files</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">文件空间</h2>
        </div>
        <span class="text-sm text-stone-500 dark:text-stone-400">{{ workspace.files?.length || 0 }} 个文件</span>
      </div>

      <div v-if="workspace.urls.uploadFiles" class="flex flex-col sm:flex-row gap-3">
        <input ref="uploadInput" type="file" multiple class="file-input file-input-bordered rounded-2xl flex-1">
        <button type="button" class="btn btn-secondary rounded-2xl" :disabled="uploading" @click="uploadFiles">
          {{ uploading ? '上传中...' : '上传文件' }}
        </button>
      </div>
      <div v-else class="rounded-2xl bg-amber-50 dark:bg-amber-900/20 p-4 text-sm text-amber-700 dark:text-amber-300">
        先创建作业，再启用文件空间上传图片和附件。
      </div>

      <div class="grid gap-3">
        <div v-for="file in workspace.files || []" :key="file.id" class="file-row p-4 flex items-start justify-between gap-4">
          <div class="min-w-0">
            <div class="font-black text-stone-900 dark:text-stone-100 break-all">{{ file.filename }}</div>
            <div class="text-xs text-stone-400 mt-1">Markdown：<code>{{ file.markdownEmbed }}</code></div>
            <div class="text-xs text-stone-400 mt-1">{{ file.fileSizeKb }} KB · {{ file.uploadedAt }}</div>
          </div>
          <button type="button" class="btn btn-sm btn-error btn-outline rounded-xl" @click="deleteFile(file)">删除</button>
        </div>
        <div v-if="!(workspace.files || []).length" class="text-sm text-stone-400">还没有上传任何作业文件。</div>
      </div>
    </section>

    <div class="flex items-center justify-between gap-4 flex-wrap pt-4 border-t border-stone-200 dark:border-white/10">
      <p class="text-sm text-stone-500 dark:text-stone-400 font-mono">assignment + permissions + problems + markdown intro</p>
      <button type="submit" class="btn btn-primary rounded-2xl px-8" :disabled="saving">
        {{ saving ? '保存中...' : workspace.mode === 'edit' ? '保存作业' : '创建作业' }}
      </button>
    </div>
  </form>
</template>
