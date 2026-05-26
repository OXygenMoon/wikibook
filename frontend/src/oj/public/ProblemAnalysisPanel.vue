<script setup>
import { computed } from 'vue';

const props = defineProps({
  analysis: { type: Object, default: null },
});

const summaryCards = computed(() => {
  const summary = props.analysis?.summary || {};
  const my = props.analysis?.my || {};
  return [
    {
      key: 'total',
      icon: 'fa-paper-plane',
      label: '总提交',
      value: summary.totalSubmissions ?? 0,
      detail: `${summary.participantCount ?? 0} 人参与`,
      tone: 'cyan',
    },
    {
      key: 'acceptedUsers',
      icon: 'fa-circle-check',
      label: '通过人数',
      value: summary.acceptedUsers ?? 0,
      detail: `用户通过率 ${summary.userPassRate ?? 0}%`,
      tone: 'emerald',
    },
    {
      key: 'passRate',
      icon: 'fa-chart-simple',
      label: '提交通过率',
      value: `${summary.submissionPassRate ?? 0}%`,
      detail: `${summary.acceptedSubmissions ?? 0} 次通过`,
      tone: 'blue',
    },
    {
      key: 'myBest',
      icon: 'fa-user-check',
      label: '我的最佳',
      value: my.bestStatus?.label || '未提交',
      detail: `${my.bestScore ?? 0} 分 · ${my.attempts ?? 0} 次提交`,
      tone: 'amber',
    },
  ];
});

const timedStats = computed(() => (props.analysis?.timeStats || []).filter((stat) => stat.key !== 'all'));
const maxTimedCount = computed(() => Math.max(1, ...timedStats.value.map((stat) => Number(stat.count) || 0)));
const statusTotal = computed(() => (props.analysis?.statusDistribution || []).reduce((total, item) => total + (Number(item.count) || 0), 0));
const failureTotal = computed(() => (props.analysis?.failureDistribution || []).reduce((total, item) => total + (Number(item.count) || 0), 0));
const maxTestcaseAttempts = computed(() => Math.max(1, ...(props.analysis?.testcaseAnalysis || []).map((item) => Number(item.attempts) || 0)));

function percent(count, total) {
  if (!total) return 0;
  return Math.round((Number(count || 0) / Number(total)) * 100);
}

function widthPercent(count, total) {
  if (!count) return '0%';
  return `${Math.max(6, percent(count, total))}%`;
}

function toneClass(tone) {
  return {
    success: 'bg-emerald-500',
    info: 'bg-blue-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    neutral: 'bg-stone-400',
  }[tone || 'neutral'] || 'bg-stone-400';
}

function dotToneClass(tone) {
  return {
    cyan: 'bg-cyan-500',
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    amber: 'bg-amber-500',
  }[tone] || 'bg-stone-400';
}
</script>

<template>
  <section v-if="analysis" class="flex flex-col gap-4 text-sm">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-xl font-black text-stone-900 dark:text-stone-100">题目分析</h2>
        <p class="text-xs text-stone-500 mt-1">统计范围：{{ analysis.scopeLabel }}</p>
      </div>
      <div v-if="analysis.summary?.perfectSubmissions" class="metric-chip metric-chip--success text-xs">
        满星通过 {{ analysis.summary.perfectSubmissions }} 次 · {{ analysis.summary.perfectRate }}%
      </div>
    </div>

    <div class="grid grid-cols-2 xl:grid-cols-4 gap-2">
      <article
        v-for="card in summaryCards"
        :key="card.key"
        class="rounded-lg border border-stone-200/80 bg-white/45 p-3 dark:border-white/10 dark:bg-white/5"
      >
        <div class="flex items-center gap-2 text-xs font-black text-stone-500">
          <span class="h-2 w-2 rounded-full" :class="dotToneClass(card.tone)"></span>
          <span>{{ card.label }}</span>
        </div>
        <div class="mt-2 text-xl font-black text-stone-900 dark:text-stone-50">{{ card.value }}</div>
        <div class="mt-1 text-xs font-bold text-stone-500">{{ card.detail }}</div>
      </article>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <section class="rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
        <div class="flex items-center justify-between gap-3 mb-3">
          <h3 class="text-base font-black text-stone-900 dark:text-stone-100">提交结果</h3>
          <span class="text-xs font-bold text-stone-500">{{ statusTotal }} 次</span>
        </div>
        <div v-if="analysis.statusDistribution?.length" class="space-y-3">
          <div v-for="item in analysis.statusDistribution" :key="item.key">
            <div class="flex items-center justify-between gap-3 text-xs font-bold mb-1.5">
              <span class="text-stone-700 dark:text-stone-200">{{ item.label }}</span>
              <span class="text-stone-500">{{ item.count }} · {{ percent(item.count, statusTotal) }}%</span>
            </div>
            <div class="h-1.5 rounded-full bg-stone-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full rounded-full" :class="toneClass(item.tone)" :style="{ width: widthPercent(item.count, statusTotal) }"></div>
            </div>
          </div>
        </div>
        <div v-else class="py-8 text-center text-stone-400">暂无提交数据。</div>
      </section>

      <section class="rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
        <div class="flex items-center justify-between gap-3 mb-3">
          <h3 class="text-base font-black text-stone-900 dark:text-stone-100">我的表现</h3>
          <span class="status-chip" :class="`status-chip--${analysis.my?.bestStatus?.tone || 'neutral'}`">{{ analysis.my?.bestStatus?.label || '未提交' }}</span>
        </div>
        <div class="divide-y divide-stone-200/80 dark:divide-white/10">
          <div class="flex items-center justify-between gap-4 py-2">
            <span class="font-bold text-stone-500">提交次数</span>
            <span class="font-black text-stone-900 dark:text-stone-100">{{ analysis.my?.attempts ?? 0 }}</span>
          </div>
          <div class="flex items-center justify-between gap-4 py-2">
            <span class="font-bold text-stone-500">最高得分</span>
            <span class="font-black text-stone-900 dark:text-stone-100">{{ analysis.my?.bestScore ?? 0 }}</span>
          </div>
          <div class="flex items-center justify-between gap-4 py-2">
            <span class="font-bold text-stone-500">首次通过</span>
            <span class="font-black text-stone-900 dark:text-stone-100">{{ analysis.my?.firstAcceptedAttempt ? `第 ${analysis.my.firstAcceptedAttempt} 次` : '-' }}</span>
          </div>
          <div class="flex items-center justify-between gap-4 py-2">
            <span class="font-bold text-stone-500">耗时</span>
            <span class="font-black text-stone-900 dark:text-stone-100">{{ analysis.my?.timeToFirstAccepted || '-' }}</span>
          </div>
        </div>
        <div v-if="analysis.my?.latestTask" class="mt-3 rounded-lg bg-stone-50/80 p-3 dark:bg-white/5">
          <div class="text-xs font-black text-stone-500 mb-1.5">最近一次提交</div>
          <div class="flex items-center justify-between gap-3">
            <span class="status-chip" :class="`status-chip--${analysis.my.latestTask.statusTone}`">{{ analysis.my.latestTask.statusLabel }}</span>
            <span class="font-mono text-xs text-stone-500">{{ analysis.my.latestTask.createdAt }}</span>
          </div>
        </div>
      </section>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <section class="rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
        <h3 class="text-base font-black text-stone-900 dark:text-stone-100 mb-3">错误类型</h3>
        <div v-if="analysis.failureDistribution?.length" class="space-y-2.5">
          <div v-for="item in analysis.failureDistribution" :key="item.key">
            <div class="flex items-center justify-between gap-3 text-xs font-bold mb-1.5">
              <span class="text-stone-700 dark:text-stone-200">{{ item.label }}</span>
              <span class="text-stone-500">{{ item.count }}</span>
            </div>
            <div class="h-1.5 rounded-full bg-stone-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full rounded-full" :class="toneClass(item.tone)" :style="{ width: widthPercent(item.count, failureTotal) }"></div>
            </div>
          </div>
        </div>
        <div v-else class="py-8 text-center text-stone-400">暂无错误数据。</div>
      </section>

      <section class="rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
        <h3 class="text-base font-black text-stone-900 dark:text-stone-100 mb-3">近期热度</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div v-for="stat in timedStats" :key="stat.key" class="rounded-md bg-stone-50/80 px-3 py-2 dark:bg-white/5">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-black text-stone-500">{{ stat.label }}</span>
              <span class="text-sm font-black text-stone-900 dark:text-stone-100">{{ stat.count }}</span>
            </div>
            <div class="mt-1.5 h-1 rounded-full bg-stone-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-cyan-500" :style="{ width: widthPercent(stat.count, maxTimedCount) }"></div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section v-if="analysis.canViewTestcaseAnalysis" class="rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
      <h3 class="text-base font-black text-stone-900 dark:text-stone-100 mb-3">测试点表现</h3>
      <div v-if="analysis.testcaseAnalysis?.length" class="space-y-2.5">
        <div v-for="item in analysis.testcaseAnalysis" :key="item.caseIndex" class="grid grid-cols-[3.5rem,1fr,8.5rem] gap-3 items-center">
          <div class="font-black text-stone-700 dark:text-stone-200">#{{ item.caseIndex }}</div>
          <div>
            <div class="h-1.5 rounded-full bg-stone-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: widthPercent(item.accepted, item.attempts) }"></div>
            </div>
            <div class="mt-1 text-xs text-stone-500">通过 {{ item.accepted }}/{{ item.attempts }} · 样本 {{ percent(item.attempts, maxTestcaseAttempts) }}%</div>
          </div>
          <div class="text-right text-xs font-bold text-stone-500">{{ item.avgTimeMs }}ms · {{ item.avgMemoryKb }}KB</div>
        </div>
      </div>
      <div v-else class="py-8 text-center text-stone-400">暂无测试点数据。</div>
    </section>
  </section>
</template>
