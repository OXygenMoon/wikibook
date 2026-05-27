<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { requestJson } from './api.js';
import { useCodeSyncInvites } from './useCodeSyncInvites.js';
import ProblemListView from './ProblemListView.vue';
import ProblemDetailView from './ProblemDetailView.vue';
import ProblemCodeView from './ProblemCodeView.vue';
import ProblemSubmitView from './ProblemSubmitView.vue';
import SubmissionListView from './SubmissionListView.vue';
import SubmissionDetailView from './SubmissionDetailView.vue';
import AssignmentListView from './AssignmentListView.vue';
import AssignmentDetailView from './AssignmentDetailView.vue';
import AssignmentScoreboardView from './AssignmentScoreboardView.vue';
import OjLeaderboardView from './OjLeaderboardView.vue';

const props = defineProps({
  initialView: { type: String, default: 'problems' },
  problemList: { type: Object, default: null },
  problemDetail: { type: Object, default: null },
  problemCode: { type: Object, default: null },
  problemSubmit: { type: Object, default: null },
  submissionList: { type: Object, default: null },
  submissionDetail: { type: Object, default: null },
  assignmentList: { type: Object, default: null },
  assignmentDetail: { type: Object, default: null },
  assignmentScoreboard: { type: Object, default: null },
  leaderboard: { type: Object, default: null },
  urls: { type: Object, default: () => ({}) },
  currentUser: { type: Object, default: () => ({}) },
  syncConfig: { type: Object, default: () => ({}) },
});

const view = ref(props.initialView);
const problemList = ref(props.problemList);
const problemDetail = ref(props.problemDetail);
const problemCode = ref(props.problemCode);
const problemSubmit = ref(props.problemSubmit);
const submissionList = ref(props.submissionList);
const submissionDetail = ref(props.submissionDetail);
const assignmentList = ref(props.assignmentList);
const assignmentDetail = ref(props.assignmentDetail);
const assignmentScoreboard = ref(props.assignmentScoreboard);
const leaderboard = ref(props.leaderboard);
const loading = ref(false);
const notice = ref(null);
const initialSubmissionListUrl = (() => {
  if (props.initialView === 'submissions' && typeof window !== 'undefined') {
    return `/oj/submissions.json${window.location.search}`;
  }
  return props.urls.submissionListJson || '/oj/submissions.json';
})();
const lastSubmissionListUrl = ref(initialSubmissionListUrl);
const syncInvites = useCodeSyncInvites({
  currentUser: props.currentUser,
  inviteUrl: props.syncConfig?.inviteUrl || props.problemCode?.collaboration?.inviteUrl || props.syncConfig?.signalingUrl || props.problemCode?.collaboration?.signalingUrl || '',
  serverUrl: props.syncConfig?.serverUrl || props.problemCode?.collaboration?.serverUrl || '',
});
const syncInviteState = reactive(syncInvites);

const title = computed(() => {
  if (view.value === 'problemDetail') return problemDetail.value?.title || '题目详情';
  if (view.value === 'problemCode') return `${problemCode.value?.problem?.title || '题目'} · 在线编码`;
  if (view.value === 'problemSubmit') return `${problemSubmit.value?.problem?.title || '题目'} · 提交代码`;
  if (view.value === 'submissions') {
    if (submissionList.value?.selectedAssignment) return `${submissionList.value.selectedAssignment.title} · 提交记录`;
    return props.currentUser?.isAdmin ? '全站 OJ 提交' : '我的 OJ 提交';
  }
  if (view.value === 'submissionDetail') return `提交 #${submissionDetail.value?.id || ''}`;
  if (view.value === 'assignments') return 'OJ 作业清单';
  if (view.value === 'assignmentDetail') return assignmentDetail.value?.assignment?.title || 'OJ 作业';
  if (view.value === 'assignmentScoreboard') return `${assignmentScoreboard.value?.assignment?.title || '作业'} · 成绩表`;
  if (view.value === 'leaderboard') return 'OJ 排行榜';
  return 'OJ 题库';
});
const currentSyncSession = computed(() => {
  if (!problemCode.value?.problem?.id || !syncInvites.activeSession.value) return null;
  return syncInvites.activeSession.value.problem?.id === problemCode.value.problem.id ? syncInvites.activeSession.value : null;
});
const currentSyncRequest = computed(() => {
  if (!problemCode.value?.problem?.id) return null;
  return syncInvites.outgoingForProblem(problemCode.value.problem.id);
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

async function goProblemCode(slug, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const search = new URL(url, window.location.origin).search;
    const data = await requestJson(`/oj/problems/${slug}/code.json${search}`);
    problemCode.value = data.problemCode;
    view.value = 'problemCode';
    if (pushState) push(url, 'problemCode');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

async function goProblemSubmit(slug, url, { pushState = true } = {}) {
  loading.value = true;
  try {
    const search = new URL(url, window.location.origin).search;
    const data = await requestJson(`/oj/problems/${slug}/submit.json${search}`);
    problemSubmit.value = data.problemSubmit;
    view.value = 'problemSubmit';
    if (pushState) push(url, 'problemSubmit');
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
    lastSubmissionListUrl.value = url;
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

async function loadLeaderboard(url = props.urls.leaderboardJson || '/oj/leaderboard.json', { pushState = true } = {}) {
  loading.value = true;
  try {
    const data = await requestJson(url);
    leaderboard.value = data.leaderboard;
    view.value = 'leaderboard';
    if (pushState) push(url.replace('/oj/leaderboard.json', '/oj/leaderboard'), 'leaderboard');
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading.value = false;
  }
}

function showSubmissionDetail(nextSubmission, redirectUrl, message = '') {
  submissionDetail.value = nextSubmission;
  view.value = 'submissionDetail';
  push(redirectUrl, 'submissionDetail');
  if (message) showNotice(message, 'success');
}

function handleCodeSyncRequest(payload) {
  const result = syncInvites.requestAdminSync(payload.problem);
  if (!result.ok && result.message) showNotice(result.message);
}

function handleStudentSyncInvite(student) {
  syncInvites.inviteStudent(student);
}

async function openAcceptedSession(session) {
  if (!session?.problem?.slug || !session.problem.codeUrl) return;
  if (view.value !== 'problemCode' || problemCode.value?.problem?.id !== session.problem.id) {
    await goProblemCode(session.problem.slug, session.problem.codeUrl);
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
  const problemCodeMatch = path.match(/^\/oj\/problems\/([^/]+)\/code$/);
  if (problemCodeMatch) {
    goProblemCode(problemCodeMatch[1], `${path}${window.location.search}`, { pushState });
    return;
  }
  const problemSubmitMatch = path.match(/^\/oj\/problems\/([^/]+)\/submit$/);
  if (problemSubmitMatch) {
    goProblemSubmit(problemSubmitMatch[1], `${path}${window.location.search}`, { pushState });
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
  if (path === '/oj/leaderboard') {
    loadLeaderboard(`/oj/leaderboard.json${window.location.search}`, { pushState });
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
  syncInvites.connect();
});

onUnmounted(() => {
  window.removeEventListener('popstate', onPopState);
  syncInvites.disconnect();
});

watch(
  () => [view.value, problemCode.value?.problem?.id],
  () => {
    if (view.value === 'problemCode' && problemCode.value?.problem) {
      syncInvites.setCodeContext({
        problem: {
          ...problemCode.value.problem,
          codeUrl: problemCode.value.urls.code,
        },
        codeUrl: problemCode.value.urls.code,
        latestTask: problemCode.value.latestTask || null,
        submissionCount: problemCode.value.submissionCount || 0,
        submissionTrajectory: problemCode.value.submissionTrajectory || [],
      });
    } else {
      syncInvites.setCodeContext(null);
    }
  },
  { immediate: true },
);

watch(
  () => syncInvites.activeSession.value,
  (session) => {
    if (session) openAcceptedSession(session);
  },
  { deep: true },
);
</script>

<template>
  <div class="oj-page min-h-[calc(100vh-4rem)] pt-6 pb-16" :class="{ 'oj-page--code': view === 'problemCode' }">
    <div class="oj-public-shell max-w-7xl mx-auto px-4 md:px-8 flex flex-col gap-6" :class="{ 'oj-public-shell--code': view === 'problemCode' }">
      <header class="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Online Judge</p>
          <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ title }}</h1>
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
        :sync-students="syncInviteState.codingStudents"
        :sync-connected="syncInviteState.socketState === 'connected'"
        @filter="loadProblems"
        @open-problem="goProblem"
        @open-submissions="loadSubmissions"
        @invite-sync-student="handleStudentSyncInvite"
      />
      <ProblemDetailView
        v-else-if="view === 'problemDetail' && problemDetail"
        :problem="problemDetail"
        @back="loadProblems('/oj/problems.json')"
        @open-code="goProblemCode"
        @open-submit="goProblemSubmit"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
      />
      <ProblemCodeView
        v-else-if="view === 'problemCode' && problemCode"
        :key="problemCode.urls.code"
        :workspace="problemCode"
        :current-user="currentUser"
        :sync-session="currentSyncSession"
        :sync-request="currentSyncRequest"
        @back="goProblem(problemCode.problem.slug, problemCode.urls.detail)"
        @open-problem="goProblem"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
        @submitted="showSubmissionDetail"
        @request-sync="handleCodeSyncRequest"
        @sync-ended="syncInvites.clearActiveSession"
      />
      <ProblemSubmitView
        v-else-if="view === 'problemSubmit' && problemSubmit"
        :key="problemSubmit.urls.submit"
        :workspace="problemSubmit"
        @back="goProblem(problemSubmit.problem.slug, problemSubmit.urls.detail)"
        @open-problem="goProblem"
        @open-code="goProblemCode"
        @open-submissions="loadSubmissions"
        @open-submission="goSubmission"
        @submitted="showSubmissionDetail"
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
        @back="loadSubmissions(lastSubmissionListUrl)"
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
      <OjLeaderboardView
        v-else-if="view === 'leaderboard' && leaderboard"
        :payload="leaderboard"
        @filter="loadLeaderboard"
      />
    </div>

    <div class="oj-sync-toast-stack" aria-live="polite">
      <section v-if="syncInviteState.notice" class="oj-sync-toast oj-sync-toast--notice">
        <i class="fas fa-circle-info" aria-hidden="true"></i>
        <span>{{ syncInviteState.notice }}</span>
      </section>

      <section v-for="invite in syncInviteState.incomingInvites" :key="invite.id" class="oj-sync-toast">
        <div class="oj-sync-toast__icon">
          <i class="fas fa-code-branch" aria-hidden="true"></i>
        </div>
        <div class="oj-sync-toast__body">
          <div class="oj-sync-toast__title">{{ invite.fromUser.name }} 邀请同步</div>
          <div class="oj-sync-toast__meta">{{ invite.problem.code }} · {{ invite.problem.title }}</div>
          <div class="oj-sync-toast__actions">
            <button type="button" class="btn btn-xs btn-primary rounded-lg" @click="syncInviteState.acceptInvite(invite)">接受</button>
            <button type="button" class="btn btn-xs btn-ghost rounded-lg" @click="syncInviteState.declineInvite(invite)">稍后</button>
          </div>
        </div>
      </section>

      <section v-if="syncInviteState.pickerOpen" class="oj-sync-picker">
        <div class="oj-sync-picker__header">
          <div>
            <div class="oj-sync-toast__title">选择同步学生</div>
            <div class="oj-sync-toast__meta">{{ syncInviteState.codingStudents.length }} 人正在编码</div>
          </div>
          <button type="button" class="btn btn-xs btn-ghost rounded-lg" @click="syncInviteState.closePicker">
            <i class="fas fa-xmark" aria-hidden="true"></i>
          </button>
        </div>
        <div v-if="syncInviteState.codingStudents.length" class="oj-sync-student-list">
          <button
            v-for="student in syncInviteState.codingStudents"
            :key="student.id"
            type="button"
            class="oj-sync-student"
            @click="syncInviteState.inviteStudent(student)"
          >
            <span class="oj-sync-student__avatar">{{ (student.name || '?').slice(0, 1) }}</span>
            <span class="oj-sync-student__main">
              <span class="oj-sync-student__name">{{ student.name }}</span>
              <span class="oj-sync-student__problem">{{ student.problem.code }} · {{ student.problem.title }}</span>
            </span>
          </button>
        </div>
        <div v-else class="oj-sync-empty">当前没有学生在普通题编码页。</div>
      </section>
    </div>
  </div>
</template>
