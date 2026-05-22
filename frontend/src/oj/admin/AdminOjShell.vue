<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { requestJson } from './api.js';
import AdminProblemManager from './AdminProblemManager.vue';
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
  urls: {
    type: Object,
    default: () => ({}),
  },
});

const view = ref(props.initialView);
const currentProblemId = ref(props.currentProblemId);
const currentProblem = ref(props.problem);
const currentWorkspace = ref(props.workspace);
const loading = ref(false);
const notice = ref(null);

const activeTitle = computed(() => {
  if (view.value === 'edit') return currentProblem.value?.title || '编辑题目';
  if (view.value === 'files') return currentWorkspace.value?.problem?.title || currentProblem.value?.title || '文件管理';
  return '题库管理中心';
});

const activeEyebrow = computed(() => {
  if (view.value === 'edit') return 'Problem Workbench';
  if (view.value === 'files') return 'Problem Files';
  return 'OJ Authoring Layer';
});

const activeDescription = computed(() => {
  if (view.value === 'edit') return '这里专注维护题目的基础信息和 Markdown 题面。';
  if (view.value === 'files') return '这里专门处理 `.in/.out`、测试点同步和题面引用资源。';
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

function updateCurrentProblem(problem) {
  currentProblem.value = problem;
  currentProblemId.value = problem.id;
  showNotice('题目已保存。');
}

function updateCurrentWorkspace(workspace) {
  currentWorkspace.value = workspace;
}

function handlePopState() {
  const path = window.location.pathname;
  const problemId = problemIdFromPath(path);
  if (path.endsWith('/files') && problemId) {
    goFiles(problemId, { push: false });
  } else if (path.endsWith('/edit') && problemId) {
    goEdit(problemId, { push: false });
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
        <div v-if="currentProblemId && view !== 'list'" class="workspace-tabbar">
          <a href="#" class="workspace-tabbar__link" :class="{ 'workspace-tabbar__link--active': view === 'edit' }" @click.prevent="goEdit(currentProblemId)">编辑题目</a>
          <a href="#" class="workspace-tabbar__link" :class="{ 'workspace-tabbar__link--active': view === 'files' }" @click.prevent="goFiles(currentProblemId)">文件管理</a>
        </div>
        <button v-if="view !== 'list'" type="button" class="btn btn-ghost rounded-2xl" @click="goList()">返回题库</button>
        <a v-if="view === 'list'" :href="urls.publicList" class="btn btn-ghost rounded-2xl">返回题库</a>
        <a v-if="view === 'list'" :href="urls.createProblem" class="btn btn-primary rounded-2xl">新建题目</a>
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
  </div>
</template>
