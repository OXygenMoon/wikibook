<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { requestJson } from './api.js';
import AdminProblemManager from './AdminProblemManager.vue';
import AssignmentFormWorkspace from './AssignmentFormWorkspace.vue';
import CreateProblemWorkspace from './CreateProblemWorkspace.vue';
import EditProblemWorkspace from './EditProblemWorkspace.vue';
import ProblemFilesWorkspace from './ProblemFilesWorkspace.vue';

const props = defineProps({
  initialView: {
    type: String,
    default: 'list',
  },
  currentProblemId: {
    type: Number,
    default: null,
  },
  initialProblems: {
    type: Array,
    default: () => [],
  },
  problemsUrl: {
    type: String,
    required: true,
  },
  problem: {
    type: Object,
    default: null,
  },
  workspace: {
    type: Object,
    default: null,
  },
  createDraft: {
    type: Object,
    default: null,
  },
  assignmentForm: {
    type: Object,
    default: null,
  },
  urls: {
    type: Object,
    default: () => ({}),
  },
});

const view = ref(props.initialView);
const currentProblemId = ref(props.currentProblemId);
const currentProblem = ref(props.problem);
const currentWorkspace = ref(props.workspace);
const currentCreateDraft = ref(props.createDraft);
const currentAssignmentForm = ref(props.assignmentForm);
const loading = ref(false);
const notice = ref(null);

const activeTitle = computed(() => {
  if (view.value === 'createProblem') return '新建 OJ 题目';
  if (view.value === 'edit') return currentProblem.value?.title || '编辑题目';
  if (view.value === 'files') return currentWorkspace.value?.problem?.title || currentProblem.value?.title || '文件管理';
  if (view.value === 'assignmentForm') return currentAssignmentForm.value?.assignment?.title || '新建 OJ 作业';
  return '题库管理中心';
});

const activeEyebrow = computed(() => {
  if (view.value === 'createProblem') return 'Problem Create';
  if (view.value === 'edit') return 'Problem Workbench';
  if (view.value === 'files') return 'Problem Files';
  if (view.value === 'assignmentForm') return 'OJ Assignment';
  return 'OJ Authoring Layer';
});

const activeDescription = computed(() => {
  if (view.value === 'createProblem') return '先把题目骨架和 Markdown 题面写好，再切进编辑题目 / 文件管理工作流。';
  if (view.value === 'edit') return '这里专注维护题目的基础信息和 Markdown 题面。';
  if (view.value === 'files') return '这里专门处理 `.in/.out`、测试点同步和题面引用资源。';
  if (view.value === 'assignmentForm') return '这里维护 OJ 作业的题单、开放范围、管理员和 Markdown 介绍。';
  return '先创建题目。之后把“题面编辑”和“文件/测试数据管理”分开处理，工作流会更清晰。';
});

function showNotice(message, category = 'success') {
  notice.value = { message, category };
  window.setTimeout(() => {
    if (notice.value?.message === message) notice.value = null;
  }, 2800);
}

function problemIdFromPath(pathname = window.location.pathname) {
  const match = pathname.match(/\/admin\/oj\/problems\/(\d+)/);
  return match ? Number(match[1]) : null;
}

function assignmentIdFromPath(pathname = window.location.pathname) {
  const match = pathname.match(/\/admin\/oj\/assignments\/(\d+)/);
  return match ? Number(match[1]) : null;
}

function replaceStateFor(viewName, url) {
  window.history.pushState({ ojAdminView: viewName }, '', url);
}

async function loadProblem(problemId) {
  loading.value = true;
  try {
    const data = await requestJson(`/admin/oj/problems/${problemId}.json`);
    currentProblem.value = data.problem;
    currentProblemId.value = problemId;
    return data.problem;
  } catch (error) {
    showNotice(error.message, 'error');
    return null;
  } finally {
    loading.value = false;
  }
}

async function loadWorkspace(problemId) {
  loading.value = true;
  try {
    const data = await requestJson(`/admin/oj/problems/${problemId}/files.json`);
    currentWorkspace.value = data.workspace;
    currentProblemId.value = problemId;
    return data.workspace;
  } catch (error) {
    showNotice(error.message, 'error');
    return null;
  } finally {
    loading.value = false;
  }
}

function goList({ push = true } = {}) {
  view.value = 'list';
  currentProblemId.value = null;
  if (push) replaceStateFor('list', props.urls.adminList || '/admin/oj/problems');
}

async function goEdit(problemOrId, { push = true } = {}) {
  const problemId = typeof problemOrId === 'object' ? problemOrId.id : problemOrId;
  const problem = typeof problemOrId === 'object' && problemOrId.statementMd ? problemOrId : await loadProblem(problemId);
  if (!problem) return;
  currentProblem.value = problem;
  currentProblemId.value = problem.id;
  view.value = 'edit';
  if (push) replaceStateFor('edit', problem.urls.edit);
}

async function goFiles(problemOrId, { push = true } = {}) {
  const problemId = typeof problemOrId === 'object' ? problemOrId.id : problemOrId;
  const workspace = await loadWorkspace(problemId);
  if (!workspace) return;
  view.value = 'files';
  if (push) replaceStateFor('files', workspace.problem.filesUrl);
}

async function goCreateProblem({ push = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson('/admin/oj/problems/new.json');
    currentCreateDraft.value = data.draft;
    view.value = 'createProblem';
    currentProblemId.value = null;
    if (push) replaceStateFor('createProblem', props.urls.createProblem || '/admin/oj/problems/new');
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    loading.value = false;
  }
}

async function goCreateAssignment({ push = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson('/admin/oj/assignments/new.json');
    currentAssignmentForm.value = data.assignmentForm;
    view.value = 'assignmentForm';
    if (push) replaceStateFor('assignmentForm', props.urls.createAssignment || '/admin/oj/assignments/new');
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    loading.value = false;
  }
}

async function goAssignmentEdit(assignmentId, { push = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(`/admin/oj/assignments/${assignmentId}.json`);
    currentAssignmentForm.value = data.assignmentForm;
    view.value = 'assignmentForm';
    if (push) replaceStateFor('assignmentForm', data.assignmentForm.assignment?.urls?.edit || `/admin/oj/assignments/${assignmentId}/edit`);
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    loading.value = false;
  }
}

function updateCurrentProblem(problem) {
  currentProblem.value = problem;
  currentProblemId.value = problem.id;
  showNotice('题目已保存。');
}

function updateCurrentWorkspace(workspace) {
  currentWorkspace.value = workspace;
}

function handleProblemCreated(payload) {
  if (payload.message) showNotice(payload.message);
  if (!payload.problem) return;
  currentProblem.value = payload.problem;
  currentProblemId.value = payload.problem.id;
  view.value = 'edit';
  replaceStateFor('edit', payload.redirectUrl || payload.problem.urls?.edit || `/admin/oj/problems/${payload.problem.id}/edit`);
}

function handleAssignmentSaved(payload) {
  if (payload.message) showNotice(payload.message);
  if (!payload.assignmentForm) return;
  currentAssignmentForm.value = payload.assignmentForm;
  view.value = 'assignmentForm';
  const nextUrl = payload.redirectUrl || payload.assignmentForm.assignment?.urls?.edit;
  if (nextUrl) replaceStateFor('assignmentForm', nextUrl);
}

function handlePopState() {
  const path = window.location.pathname;
  const problemId = problemIdFromPath(path);
  const assignmentId = assignmentIdFromPath(path);
  if (path.endsWith('/files') && problemId) {
    goFiles(problemId, { push: false });
  } else if (path.endsWith('/edit') && problemId) {
    goEdit(problemId, { push: false });
  } else if (path.endsWith('/problems/new')) {
    goCreateProblem({ push: false });
  } else if (path.endsWith('/assignments/new')) {
    goCreateAssignment({ push: false });
  } else if (path.endsWith('/edit') && assignmentId) {
    goAssignmentEdit(assignmentId, { push: false });
  } else {
    goList({ push: false });
  }
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState);
});

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState);
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-10 flex flex-col gap-8">
    <header class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <p class="text-xs font-black tracking-[0.32em] uppercase text-cyan-600 mb-2">{{ activeEyebrow }}</p>
        <h1 class="text-3xl md:text-4xl font-black text-stone-800 dark:text-stone-100">{{ activeTitle }}</h1>
        <p class="text-stone-500 dark:text-stone-400 mt-2">{{ activeDescription }}</p>
      </div>
      <div class="flex gap-3 flex-wrap items-center">
        <div v-if="currentProblemId && (view === 'edit' || view === 'files')" class="workspace-tabbar">
          <a href="#" class="workspace-tabbar__link" :class="{ 'workspace-tabbar__link--active': view === 'edit' }" @click.prevent="goEdit(currentProblemId)">编辑题目</a>
          <a href="#" class="workspace-tabbar__link" :class="{ 'workspace-tabbar__link--active': view === 'files' }" @click.prevent="goFiles(currentProblemId)">文件管理</a>
        </div>
        <button v-if="view !== 'list' && view !== 'assignmentForm'" type="button" class="btn btn-ghost rounded-2xl" @click="goList()">返回题库</button>
        <a v-if="view === 'assignmentForm'" :href="urls.assignmentList" class="btn btn-ghost rounded-2xl">作业列表</a>
        <a v-if="view === 'assignmentForm' && currentAssignmentForm?.assignment?.urls?.detail" :href="currentAssignmentForm.assignment.urls.detail" class="btn btn-outline rounded-2xl">查看作业</a>
        <a v-if="view === 'list'" :href="urls.publicList" class="btn btn-ghost rounded-2xl">返回题库</a>
        <a v-if="view === 'list' && urls.astTemplateManager" :href="urls.astTemplateManager" class="btn btn-outline rounded-2xl">AST 模板</a>
        <a v-if="view === 'list' && urls.createAssignment" :href="urls.createAssignment" class="btn btn-outline rounded-2xl" @click.prevent="goCreateAssignment()">新建作业</a>
        <a v-if="view === 'list' && urls.createProblem" :href="urls.createProblem" class="btn btn-primary rounded-2xl" @click.prevent="goCreateProblem()">新建题目</a>
      </div>
    </header>

    <div v-if="notice" class="oj-vue-alert" :class="notice.category === 'error' ? 'oj-vue-alert--error' : 'oj-vue-alert--success'">
      {{ notice.message }}
    </div>

    <div v-if="loading" class="bench-card p-8 text-center text-stone-400">加载中...</div>
    <AdminProblemManager
      v-else-if="view === 'list'"
      :initial-problems="initialProblems"
      :problems-url="problemsUrl"
      @navigate-edit="goEdit"
      @navigate-files="goFiles"
    />
    <CreateProblemWorkspace
      v-else-if="view === 'createProblem' && currentCreateDraft"
      :draft="currentCreateDraft"
      @created="handleProblemCreated"
    />
    <EditProblemWorkspace
      v-else-if="view === 'edit' && currentProblem"
      :problem="currentProblem"
      @saved="updateCurrentProblem"
      @navigate-files="goFiles"
    />
    <ProblemFilesWorkspace
      v-else-if="view === 'files' && currentWorkspace"
      :workspace="currentWorkspace"
      :workspace-url="`/admin/oj/problems/${currentProblemId}/files.json`"
      @workspace-updated="updateCurrentWorkspace"
    />
    <AssignmentFormWorkspace
      v-else-if="view === 'assignmentForm' && currentAssignmentForm"
      :workspace="currentAssignmentForm"
      @saved="handleAssignmentSaved"
    />
  </div>
</template>
