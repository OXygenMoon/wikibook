<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { requestJson } from './api.js';
import ProblemListView from './ProblemListView.vue';
import ProblemDetailView from './ProblemDetailView.vue';
import SubmissionListView from './SubmissionListView.vue';
import SubmissionDetailView from './SubmissionDetailView.vue';
import AssignmentListView from './AssignmentListView.vue';
import AssignmentDetailView from './AssignmentDetailView.vue';
import AssignmentScoreboardView from './AssignmentScoreboardView.vue';

const props = defineProps({
  initialView: { type: String, default: 'problems' },
  problemList: { type: Object, default: null },
  problemDetail: { type: Object, default: null },
  submissionList: { type: Object, default: null },
  submissionDetail: { type: Object, default: null },
  assignmentList: { type: Object, default: null },
  assignmentDetail: { type: Object, default: null },
  assignmentScoreboard: { type: Object, default: null },
  urls: { type: Object, default: () => ({}) },
  currentUser: { type: Object, default: () => ({}) },
});

const view = ref(props.initialView);
const problemList = ref(props.problemList);
const problemDetail = ref(props.problemDetail);
const submissionList = ref(props.submissionList);
const submissionDetail = ref(props.submissionDetail);
const assignmentList = ref(props.assignmentList);
const assignmentDetail = ref(props.assignmentDetail);
const assignmentScoreboard = ref(props.assignmentScoreboard);
const loading = ref(false);
const notice = ref(null);

const title = computed(() => {
  if (view.value === 'problemDetail') return problemDetail.value?.title || '题目详情';
  if (view.value === 'submissions') {
    if (submissionList.value?.selectedAssignment) return `${submissionList.value.selectedAssignment.title} · 提交记录`;
    return props.currentUser?.isAdmin ? '全站 OJ 提交' : '我的 OJ 提交';
  }
  if (view.value === 'submissionDetail') return `提交 #${submissionDetail.value?.id || ''}`;
  if (view.value === 'assignments') return 'OJ 作业清单';
  if (view.value === 'assignmentDetail') return assignmentDetail.value?.assignment?.title || 'OJ 作业';
  if (view.value === 'assignmentScoreboard') return `${assignmentScoreboard.value?.assignment?.title || '作业'} · 成绩表`;
  return 'OJ 题库';
});

function showNotice(message, category = 'error') {
  notice.value = { message, category };
  window.setTimeout(() => {
    if (notice.value?.message === message) notice.value = null;
  }, 3200);
}

function push(url, viewName) {
  window.history.pushState({ ojView: viewName }, '', url);
}

async function loadProblems(url = props.urls.problemListJson || '/oj/problems.json', { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(url);
    problemList.value = data.problemList;
    view.value = 'problems';
    if (pushState) push(url.replace('/oj/problems.json', '/oj/problems'), 'problems');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function goProblem(slug, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(`/oj/problems/${slug}.json${new URL(url, window.location.origin).search}`);
    problemDetail.value = data.problemDetail;
    view.value = 'problemDetail';
    if (pushState) push(url, 'problemDetail');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function loadSubmissions(url = props.urls.submissionListJson || '/oj/submissions.json', { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(url);
    submissionList.value = data.submissionList;
    view.value = 'submissions';
    if (pushState) push(url.replace('/oj/submissions.json', '/oj/submissions'), 'submissions');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function goSubmission(taskId, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(`/oj/submissions/${taskId}.json`);
    submissionDetail.value = data.submissionDetail;
    view.value = 'submissionDetail';
    if (pushState) push(url, 'submissionDetail');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function loadAssignments(url = props.urls.assignmentListJson || '/oj/assignments.json', { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(url);
    assignmentList.value = data.assignmentList;
    view.value = 'assignments';
    if (pushState) push(url.replace('/oj/assignments.json', '/oj/assignments'), 'assignments');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function goAssignment(assignmentId, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(`/oj/assignments/${assignmentId}.json`);
    assignmentDetail.value = data.assignmentDetail;
    view.value = 'assignmentDetail';
    if (pushState) push(url, 'assignmentDetail');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function goAssignmentScoreboard(assignmentId, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(`/oj/assignments/${assignmentId}/scoreboard.json`);
    assignmentScoreboard.value = data.assignmentScoreboard;
    view.value = 'assignmentScoreboard';
    if (pushState) push(url, 'assignmentScoreboard');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

function routeFromLocation({ pushState = false } = {}) {
  const path = window.location.pathname;
  if (path === '/oj/problems') {
    loadProblems(`/oj/problems.json${window.location.search}`, { pushState });
    return;
  }
  const problemMatch = path.match(/^\/oj\/problems\/([^/]+)$/);
  if (problemMatch) {
    goProblem(problemMatch[1], `${path}${window.location.search}`, { pushState });
    return;
  }
  if (path === '/oj/submissions') {
    loadSubmissions(`/oj/submissions.json${window.location.search}`, { pushState });
    return;
  }
  const submissionMatch = path.match(/^\/oj\/submissions\/(\d+)$/);
  if (submissionMatch) {
    goSubmission(Number(submissionMatch[1]), path, { pushState });
    return;
  }
  if (path === '/oj/assignments') {
    loadAssignments(`/oj/assignments.json${window.location.search}`, { pushState });
    return;
  }
  const assignmentScoreboardMatch = path.match(/^\/oj\/assignments\/(\d+)\/scoreboard$/);
  if (assignmentScoreboardMatch) {
    goAssignmentScoreboard(Number(assignmentScoreboardMatch[1]), path, { pushState });
    return;
  }
  const assignmentMatch = path.match(/^\/oj\/assignments\/(\d+)$/);
  if (assignmentMatch) {
    goAssignment(Number(assignmentMatch[1]), path, { pushState });
  }
}

function onPopState() {
  routeFromLocation({ pushState: false });
}

onMounted(() => {
  window.addEventListener('popstate', onPopState);
});

onUnmounted(() => {
  window.removeEventListener('popstate', onPopState);
});
</script>

<template>
  <div class="oj-page min-h-[calc(100vh-4rem)] pt-6 pb-16">
    <div class="max-w-7xl mx-auto px-4 md:px-8 flex flex-col gap-6">
      <header class="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Online Judge</p>
          <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ title }}</h1>
        </div>
        <div class="flex gap-2 flex-wrap">
          <button type="button" class="btn btn-ghost rounded-lg" @click="loadProblems('/oj/problems.json')">
            <i class="fas fa-code" aria-hidden="true"></i> 题库
          </button>
          <button type="button" class="btn btn-outline rounded-lg" @click="loadSubmissions('/oj/submissions.json')">
            <i class="fas fa-history" aria-hidden="true"></i> 提交记录
          </button>
          <a v-if="urls.assignmentList" :href="urls.assignmentList" class="btn btn-ghost rounded-lg" @click.prevent="loadAssignments('/oj/assignments.json')">
            <i class="fas fa-clipboard-list" aria-hidden="true"></i> 作业
          </a>
          <a v-if="urls.adminProblems" :href="urls.adminProblems" class="btn btn-outline rounded-lg">
            <i class="fas fa-sliders-h" aria-hidden="true"></i> 管理题库
          </a>
        </div>
      </header>

      <div v-if="notice" class="oj-vue-alert" :class="notice.category === 'error' ? 'oj-vue-alert--error' : 'oj-vue-alert--success'">
        {{ notice.message }}
      </div>
      <div v-if="loading" class="oj-panel p-8 text-center text-stone-400">加载中...</div>

      <ProblemListView
        v-else-if="view === 'problems' && problemList"
        :payload="problemList"
        :is-admin="currentUser?.isAdmin"
        @filter="loadProblems"
        @open-problem="goProblem"
        @open-submissions="loadSubmissions"
      />
      <ProblemDetailView
        v-else-if="view === 'problemDetail' && problemDetail"
        :problem="problemDetail"
        @back="loadProblems('/oj/problems.json')"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
      />
      <SubmissionListView
        v-else-if="view === 'submissions' && submissionList"
        :payload="submissionList"
        @filter="loadSubmissions"
        @open-problem="goProblem"
        @open-submission="goSubmission"
      />
      <SubmissionDetailView
        v-else-if="view === 'submissionDetail' && submissionDetail"
        :submission="submissionDetail"
        @back="loadSubmissions('/oj/submissions.json')"
      />
      <AssignmentListView
        v-else-if="view === 'assignments' && assignmentList"
        :payload="assignmentList"
        :urls="urls"
        @open-assignment="goAssignment"
      />
      <AssignmentDetailView
        v-else-if="view === 'assignmentDetail' && assignmentDetail"
        :payload="assignmentDetail"
        @back="loadAssignments('/oj/assignments.json')"
        @open-problem="goProblem"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
        @open-scoreboard="goAssignmentScoreboard"
      />
      <AssignmentScoreboardView
        v-else-if="view === 'assignmentScoreboard' && assignmentScoreboard"
        :payload="assignmentScoreboard"
        @back-assignment="goAssignment"
        @open-problem="goProblem"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
      />
    </div>
  </div>
</template>
