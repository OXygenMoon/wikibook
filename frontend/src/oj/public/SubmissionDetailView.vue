<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { requestJson } from './api.js';

const props = defineProps({
  submission: { type: Object, required: true },
});

const emit = defineEmits(['back']);
const localSubmission = ref(props.submission);
let pollTimer = 0;

const isFinal = computed(() => !['queued', 'running'].includes(localSubmission.value?.status));
const hasCaseDetails = computed(() => Boolean(localSubmission.value?.canViewCaseDetails));
const sampleComparisons = computed(() => localSubmission.value?.sampleComparisons || []);
const hasSampleComparisons = computed(() => sampleComparisons.value.length > 0);
const sampleGroupFailed = computed(() => Boolean(localSubmission.value?.sampleGroupFailed));
const astFeedbackToneClass = computed(() => (
  localSubmission.value?.astFeedback?.isPerfect ? 'submission-feedback-card--success' : 'submission-feedback-card--warning'
));

function metricClass(score) {
  return Number(score || 0) > 0 ? 'metric-chip--success' : 'metric-chip--danger';
}

function compactCaseTitle(result) {
  return `测试点 ${result.caseIndex}`;
}

async function refreshSubmissionDetail() {
  const detailUrl = localSubmission.value?.urls?.detailJson;
  if (!detailUrl) return;
  const data = await requestJson(detailUrl);
  localSubmission.value = data.submissionDetail;
}

async function pollStatus() {
  if (isFinal.value || !localSubmission.value?.urls?.status) return;
  try {
    const status = await requestJson(localSubmission.value.urls.status);
    localSubmission.value = {
      ...localSubmission.value,
      status: status.status,
      statusLabel: status.status_label,
      statusTone: status.status_tone,
      passedCount: status.passed_count,
      totalCount: status.total_count,
      totalScore: status.total_score,
      errorMessage: status.error_message,
    };
    if (!['queued', 'running'].includes(status.status)) {
      await refreshSubmissionDetail();
      window.clearInterval(pollTimer);
    }
  } catch (error) {
    window.clearInterval(pollTimer);
  }
}

watch(() => props.submission, (nextSubmission) => {
  localSubmission.value = nextSubmission;
}, { immediate: true });

onMounted(() => {
  pollTimer = window.setInterval(pollStatus, 1800);
  pollStatus();
});

onUnmounted(() => {
  window.clearInterval(pollTimer);
});
</script>

<template>
  <div class="submission-detail">
    <section class="oj-panel p-5 md:p-6">
      <div class="submission-detail__hero">
        <div class="min-w-0">
          <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">提交 #{{ localSubmission.id }}</p>
          <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">
            {{ localSubmission.problem?.title || 'OJ 提交详情' }}
          </h1>
        </div>
        <div class="flex gap-2 flex-wrap">
          <a v-if="localSubmission.problem" :href="localSubmission.problem.url" class="btn btn-outline rounded-lg">
            <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回题目
          </a>
          <button type="button" class="btn btn-ghost rounded-lg" @click="emit('back')">
            <i class="fas fa-history" aria-hidden="true"></i> 提交记录
          </button>
        </div>
      </div>

      <div class="submission-summary-grid">
        <div class="submission-summary-cell submission-summary-cell--status">
          <div class="metric-label">状态</div>
          <span class="status-chip" :class="`status-chip--${localSubmission.statusTone}`">{{ localSubmission.statusLabel }}</span>
        </div>
        <div class="submission-summary-cell">
          <div class="metric-label">通过</div>
          <div class="font-mono font-black">{{ localSubmission.passedCount }}/{{ localSubmission.totalCount }}</div>
        </div>
        <div class="submission-summary-cell">
          <div class="metric-label">得分</div>
          <div class="font-mono font-black">{{ localSubmission.totalScore }}</div>
        </div>
        <div class="submission-summary-cell">
          <div class="metric-label">语言</div>
          <div class="font-bold">{{ localSubmission.language }}</div>
        </div>
        <div class="submission-summary-cell">
          <div class="metric-label">时限</div>
          <div class="font-mono font-bold">{{ localSubmission.timeLimitMs }} ms</div>
        </div>
        <div class="submission-summary-cell">
          <div class="metric-label">内存</div>
          <div class="font-mono font-bold">{{ localSubmission.memoryLimitMb }} MB</div>
        </div>
      </div>
    </section>

    <section v-if="localSubmission.failureFeedback" class="submission-feedback-card submission-feedback-card--danger">
      <div class="font-black text-lg">{{ localSubmission.failureFeedback.title }}</div>
      <p class="mt-2 leading-relaxed">{{ localSubmission.failureFeedback.message }}</p>
      <pre v-if="localSubmission.failureFeedback.detail" class="failure-detail">{{ localSubmission.failureFeedback.detail }}</pre>
    </section>

    <section v-if="localSubmission.astFeedback" class="submission-feedback-card" :class="astFeedbackToneClass">
      <div class="font-black text-lg">{{ localSubmission.astFeedback.title }}</div>
      <p class="mt-2 leading-relaxed">{{ localSubmission.astFeedback.message }}</p>
      <div v-if="localSubmission.astFeedback.failedRules?.length" class="mt-4">
        <div class="font-bold mb-2">未完成的满星目标</div>
        <ol class="list-decimal pl-5 space-y-2">
          <li v-for="item in localSubmission.astFeedback.failedRules" :key="`${item.rule_id || 'rule'}-${item.description}`">{{ item.message || item.description }}</li>
        </ol>
      </div>
    </section>

    <section class="oj-panel submission-code-panel">
      <div class="submission-code-panel__header">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100">提交代码</h2>
        <span class="metric-chip">{{ localSubmission.language }}</span>
      </div>
      <pre class="judge-code judge-code--submission">{{ localSubmission.sourceCode || '暂无代码' }}</pre>
    </section>

    <section v-if="localSubmission.errorMessage" class="failure-card error">
      <div class="font-black">系统消息</div>
      <pre class="failure-detail">{{ localSubmission.errorMessage }}</pre>
    </section>

    <section v-if="hasSampleComparisons" class="oj-panel p-5 md:p-6">
      <div class="flex items-center justify-between gap-4 flex-wrap mb-4">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100">公开样例对比</h2>
        <span
          v-if="sampleGroupFailed"
          class="status-chip status-chip--danger sample-alert-chip"
        >
          全部未通过
        </span>
      </div>

      <div v-if="sampleGroupFailed" class="sample-failure-callout mb-4">
        <div class="font-black text-lg">公开样例全部未通过</div>
        <p class="mt-1 leading-relaxed">请先对照本题输出和标准输出，修正输出格式或核心逻辑后再看隐藏测试点。</p>
      </div>

      <div class="flex flex-col gap-3">
        <article
          v-for="sample in sampleComparisons"
          :key="`sample-${sample.sampleIndex}-${sample.caseIndex}`"
          class="sample-comparison-row"
          :class="{ 'sample-comparison-row--failed': sampleGroupFailed }"
        >
          <div class="flex items-center justify-between gap-3 flex-wrap mb-3">
            <div class="font-black text-stone-900 dark:text-stone-100">样例 {{ sample.sampleIndex }}</div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="status-chip" :class="`status-chip--${sample.meta.tone}`">{{ sample.meta.label }}</span>
              <span class="metric-chip" :class="metricClass(sample.score)">{{ sample.score }} 分</span>
              <span class="metric-chip">{{ sample.timeMs }} ms</span>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <div>
              <div class="case-label">输入</div>
              <pre class="judge-output">{{ sample.inputData || '（空）' }}</pre>
            </div>
            <div>
              <div class="case-label">标准输出</div>
              <pre class="judge-output judge-output--expected">{{ sample.expectedOutput || '（空）' }}</pre>
            </div>
            <div>
              <div class="case-label">本题输出</div>
              <pre class="judge-output" :class="{ 'judge-output--actual-danger': sampleGroupFailed }">{{ sample.actualOutput || '（空）' }}</pre>
            </div>
            <div v-if="sample.stderrText" class="lg:col-span-3">
              <div class="case-label">标准错误</div>
              <pre class="judge-output">{{ sample.stderrText }}</pre>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="oj-panel p-5 md:p-6">
      <div class="flex items-center justify-between gap-4 flex-wrap mb-4">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100">测试点结果</h2>
        <p v-if="!hasCaseDetails" class="text-sm text-stone-500">普通用户只显示每个测试点的判定、得分和耗时。</p>
      </div>

      <div class="flex flex-col gap-2">
        <article v-for="result in localSubmission.results" :key="result.caseIndex" class="case-row">
          <div class="flex items-center justify-between gap-3 flex-wrap">
            <div class="font-black text-stone-900 dark:text-stone-100">{{ compactCaseTitle(result) }}</div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="status-chip" :class="`status-chip--${result.meta.tone}`">{{ result.meta.label }}</span>
              <span class="metric-chip" :class="metricClass(result.score)">{{ result.score }} 分</span>
              <span class="metric-chip">{{ result.timeMs }} ms</span>
            </div>
          </div>

          <div v-if="hasCaseDetails" class="grid grid-cols-1 lg:grid-cols-3 gap-3 mt-3">
            <div>
              <div class="case-label">输入</div>
              <pre class="judge-output">{{ result.inputData || '（空）' }}</pre>
            </div>
            <div>
              <div class="case-label">期望输出</div>
              <pre class="judge-output">{{ result.expectedOutput || '（空）' }}</pre>
            </div>
            <div>
              <div class="case-label">实际输出</div>
              <pre class="judge-output">{{ result.actualOutput || '（空）' }}</pre>
            </div>
            <div v-if="result.stderrText" class="lg:col-span-3">
              <div class="case-label">标准错误</div>
              <pre class="judge-output">{{ result.stderrText }}</pre>
            </div>
          </div>
        </article>

        <div v-if="!localSubmission.results.length" class="case-note">
          评测结果还没有写入，页面会自动等待队列更新。
        </div>
      </div>
    </section>
  </div>
</template>
