<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({
  payload: { type: Object, required: true },
});

const emit = defineEmits(['filter']);
const filters = reactive({ period: 'weekly', metric: 'solved' });

function syncFilters() {
  Object.assign(filters, props.payload.filters || {});
}

function buildUrl() {
  const params = new URLSearchParams();
  if (filters.period) params.set('period', filters.period);
  if (filters.metric) params.set('metric', filters.metric);
  const query = params.toString();
  return `/oj/leaderboard.json${query ? `?${query}` : ''}`;
}

function choosePeriod(period) {
  filters.period = period;
  emit('filter', buildUrl());
}

function chooseMetric(metric) {
  filters.metric = metric;
  emit('filter', buildUrl());
}

function rankClass(rank) {
  if (rank === 1) return 'bg-amber-100 text-amber-700 border-amber-200';
  if (rank === 2) return 'bg-slate-100 text-slate-700 border-slate-200';
  if (rank === 3) return 'bg-orange-100 text-orange-700 border-orange-200';
  return 'bg-stone-100 text-stone-600 border-stone-200 dark:bg-white/10 dark:text-stone-200 dark:border-white/10';
}

watch(() => props.payload, syncFilters, { immediate: true });
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="oj-panel p-4 md:p-5">
      <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-5">
        <div>
          <h2 class="text-xl font-black text-stone-900 dark:text-stone-100">OJ 排行榜</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">
            {{ payload.activePeriod.label }} · {{ payload.activeMetric.description }}
          </p>
        </div>
        <div class="flex flex-col md:flex-row gap-3">
          <div class="join">
            <button
              v-for="period in payload.periods"
              :key="period.key"
              type="button"
              class="btn btn-sm join-item"
              :class="filters.period === period.key ? 'btn-primary' : 'btn-outline'"
              @click="choosePeriod(period.key)"
            >
              {{ period.label }}
            </button>
          </div>
          <div class="join">
            <button
              v-for="metric in payload.metrics"
              :key="metric.key"
              type="button"
              class="btn btn-sm join-item"
              :class="filters.metric === metric.key ? 'btn-secondary' : 'btn-outline'"
              @click="chooseMetric(metric.key)"
            >
              <i class="fas" :class="metric.icon" aria-hidden="true"></i>
              {{ metric.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <div class="mini-stat">
          <div class="mini-stat-label">上榜人数</div>
          <div class="mini-stat-value">{{ payload.summary.participantCount }}</div>
        </div>
        <div class="mini-stat is-info">
          <div class="mini-stat-label">提交总数</div>
          <div class="mini-stat-value">{{ payload.summary.submissionCount }}</div>
        </div>
        <div class="mini-stat is-success">
          <div class="mini-stat-label">通过题目</div>
          <div class="mini-stat-value">{{ payload.summary.solvedProblemCount }}</div>
        </div>
        <div class="mini-stat is-warning">
          <div class="mini-stat-label">满星题目</div>
          <div class="mini-stat-value">{{ payload.summary.perfectProblemCount }}</div>
        </div>
      </div>
    </section>

    <section v-if="payload.myRank" class="oj-panel p-4 md:p-5">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-3 min-w-0">
          <span class="inline-flex items-center justify-center w-12 h-12 rounded-xl border font-black" :class="rankClass(payload.myRank.rank)">
            #{{ payload.myRank.rank }}
          </span>
          <div class="min-w-0">
            <div class="text-sm text-stone-500 dark:text-stone-400">我的位置</div>
            <div class="font-black text-stone-900 dark:text-stone-100 truncate">
              {{ payload.myRank.name }}
            </div>
          </div>
        </div>
        <div class="text-right">
          <div class="text-2xl font-black text-cyan-700 dark:text-cyan-200">
            {{ payload.myRank.primaryScore }}{{ payload.myRank.unit }}
          </div>
          <div class="text-xs text-stone-400">
            <span v-if="payload.gapToNext > 0">距上一名 {{ payload.gapToNext }}{{ payload.myRank.unit }}</span>
            <span v-else>保持这个节奏</span>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-[22rem,1fr] gap-6 items-start">
      <div class="oj-panel p-4 md:p-5">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-4">Top Three</div>
        <div class="flex flex-col gap-3">
          <a
            v-for="row in payload.topThree"
            :key="row.userId"
            :href="row.profileUrl"
            class="rounded-xl border border-stone-200/80 dark:border-white/10 bg-stone-50/80 dark:bg-white/5 p-4 hover:border-cyan-400 transition-colors"
          >
            <div class="flex items-center gap-3">
              <span class="inline-flex items-center justify-center w-10 h-10 rounded-xl border font-black" :class="rankClass(row.rank)">
                {{ row.rank }}
              </span>
              <div class="w-11 h-11 rounded-xl bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-100 flex items-center justify-center font-black">
                {{ row.initial }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="font-black text-stone-900 dark:text-stone-100 truncate">{{ row.name }}</div>
                <div class="text-xs text-stone-400 truncate">{{ row.className }} · @{{ row.username }}</div>
              </div>
            </div>
            <div class="mt-4 flex items-end justify-between">
              <span class="text-xs text-stone-400">{{ payload.activeMetric.label }}</span>
              <span class="text-2xl font-black text-cyan-700 dark:text-cyan-200">{{ row.primaryScore }}{{ row.unit }}</span>
            </div>
          </a>
          <div v-if="!payload.topThree.length" class="text-center py-10 text-stone-400">这个榜单还没有数据。</div>
        </div>
      </div>

      <div class="oj-panel overflow-hidden">
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr class="text-xs uppercase tracking-widest text-stone-500">
                <th>排名</th>
                <th>用户</th>
                <th>{{ payload.activeMetric.label }}</th>
                <th>解题</th>
                <th>满星</th>
                <th>总分</th>
                <th>提交</th>
                <th>通过率</th>
                <th>最近提交</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in payload.rows" :key="row.userId" class="submission-row" :class="row.isCurrentUser ? 'bg-cyan-50/70 dark:bg-cyan-900/10' : ''">
                <td>
                  <span class="inline-flex items-center justify-center min-w-10 rounded-lg border px-2 py-1 font-black" :class="rankClass(row.rank)">
                    #{{ row.rank }}
                  </span>
                </td>
                <td>
                  <a :href="row.profileUrl" class="font-black text-stone-900 dark:text-stone-100 hover:text-cyan-600">{{ row.name }}</a>
                  <div class="text-xs text-stone-400 mt-1">{{ row.className }} · @{{ row.username }}</div>
                </td>
                <td class="font-mono font-black text-cyan-700 dark:text-cyan-200">{{ row.primaryScore }}{{ row.unit }}</td>
                <td class="font-mono font-bold">{{ row.solvedCount }}</td>
                <td class="font-mono font-bold">{{ row.perfectCount }}</td>
                <td class="font-mono font-bold">{{ row.totalScore }}</td>
                <td class="font-mono font-bold">{{ row.submissionCount }}</td>
                <td>
                  <span class="metric-chip" :class="row.successRate >= 50 ? 'metric-chip--success' : 'metric-chip--danger'">
                    {{ row.successRate }}%
                  </span>
                </td>
                <td class="font-mono text-sm text-stone-500">{{ row.latestAt }}</td>
              </tr>
              <tr v-if="!payload.rows.length">
                <td colspan="9" class="text-center py-14 text-stone-400">这个榜单还没有数据。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>
