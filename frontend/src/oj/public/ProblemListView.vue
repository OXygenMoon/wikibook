<script setup>
import { reactive, ref, watch } from 'vue';
import DifficultyBadge from '../DifficultyBadge.vue';
import { DIFFICULTY_OPTIONS } from '../difficulty.js';

const props = defineProps({
  payload: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false },
  syncStudents: { type: Array, default: () => [] },
  syncConnected: { type: Boolean, default: false },
});

const emit = defineEmits(['filter', 'openProblem', 'openSubmissions', 'inviteSyncStudent']);
const filters = reactive({ q: '', difficulty: '', visibility: 'visible' });
const quickSearches = ['P', 'PF', 'Q'];
const syncPanelOpen = ref(false);

function syncFilters() {
  Object.assign(filters, props.payload.filters || {});
}

function difficultySelectClass() {
  if (filters.difficulty === 'easy') return 'bg-emerald-50 text-emerald-800 border-emerald-300 focus:border-emerald-500 dark:bg-emerald-950 dark:text-emerald-100 dark:border-emerald-700';
  if (filters.difficulty === 'medium') return 'bg-amber-50 text-amber-800 border-amber-300 focus:border-amber-500 dark:bg-amber-950 dark:text-amber-100 dark:border-amber-700';
  if (filters.difficulty === 'hard') return 'bg-rose-50 text-rose-800 border-rose-300 focus:border-rose-500 dark:bg-rose-950 dark:text-rose-100 dark:border-rose-700';
  if (filters.difficulty === 'extreme') return 'bg-red-950 text-red-50 border-red-700 focus:border-red-400';
  if (filters.difficulty === 'glitch') return 'bg-slate-950 text-cyan-100 border-cyan-500 focus:border-cyan-300';
  return '';
}

function statusClass(problem) {
  if (problem.myStatus?.perfectAccepted) return 'bg-emerald-100 text-emerald-700 border-emerald-200';
  if (problem.myStatus?.accepted) return 'bg-amber-100 text-amber-700 border-amber-200';
  if (problem.myStatus?.attempted) return 'bg-rose-100 text-rose-700 border-rose-200';
  return '';
}

function rowClass(problem) {
  if (problem.myStatus?.accepted) return 'problem-row is-accepted';
  if (problem.myStatus?.attempted) return 'problem-row is-attempted';
  return 'problem-row';
}

function buildUrl() {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.difficulty) params.set('difficulty', filters.difficulty);
  if (props.isAdmin && filters.visibility) params.set('visibility', filters.visibility);
  const query = params.toString();
  return `/oj/problems.json${query ? `?${query}` : ''}`;
}

function submitFilter() {
  emit('filter', buildUrl());
}

function tagFilter(tag) {
  filters.q = tag;
  submitFilter();
}

function quickSearch(term) {
  filters.q = term;
  submitFilter();
}

function difficultyFilter(difficulty) {
  filters.difficulty = difficulty;
  submitFilter();
}

function toggleSyncPanel() {
  syncPanelOpen.value = !syncPanelOpen.value;
}

function latestTaskMeta(student) {
  if (!student?.latestTask) return '尚未提交';
  if (student.latestTask.passedCount !== null && student.latestTask.totalCount !== null) {
    return `${student.latestTask.passedCount}/${student.latestTask.totalCount}`;
  }
  return student.latestTask.createdAt || '最近提交';
}

function trajectoryTitle(item) {
  return `第 ${item.attempt} 次 · ${item.statusLabel}`;
}

watch(() => props.payload, syncFilters, { immediate: true });
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">全部</div>
        <div class="text-2xl font-black text-stone-900 dark:text-stone-100">{{ payload.stats.total }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">简单</div>
        <div class="text-2xl font-black text-emerald-600">{{ payload.stats.easy }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">中等</div>
        <div class="text-2xl font-black text-amber-600">{{ payload.stats.medium }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">困难</div>
        <div class="text-2xl font-black text-rose-600">{{ payload.stats.hard }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">特难</div>
        <div class="text-2xl font-black text-red-800 dark:text-red-300">{{ payload.stats.extreme }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">???</div>
        <div class="text-2xl font-black text-cyan-600">{{ payload.stats.glitch }}</div>
      </div>
    </div>

    <form class="oj-panel p-4 flex flex-col gap-3" @submit.prevent="submitFilter">
      <div
        class="grid grid-cols-1 gap-3 items-end"
        :class="isAdmin ? 'md:grid-cols-[1fr,12rem,12rem,auto]' : 'md:grid-cols-[1fr,12rem,auto]'"
      >
        <label class="form-control">
          <span class="label-text font-bold mb-1">搜索</span>
          <input v-model.trim="filters.q" type="text" class="input input-bordered rounded-lg" placeholder="编号、题目、标签">
        </label>
        <label class="form-control">
          <span class="label-text font-bold mb-1">难度</span>
          <select v-model="filters.difficulty" class="select select-bordered rounded-lg font-black transition-colors" :class="difficultySelectClass()" @change="submitFilter">
            <option value="">全部难度</option>
            <option v-for="option in DIFFICULTY_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label v-if="isAdmin" class="form-control">
          <span class="label-text font-bold mb-1">可见性</span>
          <select v-model="filters.visibility" class="select select-bordered rounded-lg" @change="submitFilter">
            <option value="visible">公开题</option>
            <option value="hidden">隐藏题</option>
            <option value="all">全部</option>
          </select>
        </label>
        <button type="submit" class="btn btn-primary rounded-lg">
          <i class="fas fa-search" aria-hidden="true"></i> 筛选
        </button>
      </div>
      <div class="flex flex-wrap items-center gap-2 border-t border-stone-200/80 pt-3 dark:border-white/10">
        <span class="text-xs font-black uppercase tracking-widest text-stone-400">快速搜索</span>
        <button
          v-for="term in quickSearches"
          :key="term"
          type="button"
          class="btn btn-sm rounded-lg"
          :class="filters.q === term ? 'btn-secondary' : 'btn-outline'"
          @click="quickSearch(term)"
        >
          包含 {{ term }}
        </button>
        <button
          v-if="isAdmin"
          type="button"
          class="btn btn-sm rounded-lg ml-auto"
          :class="syncPanelOpen ? 'btn-secondary' : 'btn-outline'"
          @click="toggleSyncPanel"
        >
          <i class="fas fa-link" aria-hidden="true"></i>
          同步
        </button>
      </div>
    </form>

    <section v-if="isAdmin && syncPanelOpen" class="oj-panel p-4 sync-admin-panel">
      <div class="sync-admin-panel__header">
        <div>
          <div class="sync-admin-panel__title">在线编程学生</div>
          <div class="sync-admin-panel__meta">
            {{ syncStudents.length }} 人正在普通题代码页
            <span v-if="!syncConnected"> · 同步服务连接中</span>
          </div>
        </div>
      </div>
      <div v-if="syncStudents.length" class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr class="text-xs uppercase tracking-widest text-stone-500">
              <th>学生</th>
              <th>正在编写</th>
              <th>上次提交</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in syncStudents" :key="student.id" class="submission-row">
              <td>
                <div class="font-black text-stone-900 dark:text-stone-100">{{ student.name }}</div>
                <div class="text-xs text-stone-400">@{{ student.username || student.id }}</div>
              </td>
              <td>
                <div class="font-black text-stone-900 dark:text-stone-100">{{ student.problem.code }}</div>
                <div class="text-sm text-stone-500 dark:text-stone-300">{{ student.problem.title }}</div>
              </td>
              <td>
                <div class="sync-student-trajectory">
                  <div class="sync-student-trajectory__meta">
                    <span class="text-xs font-black text-stone-500 dark:text-stone-300">{{ student.submissionCount || 0 }} 次提交</span>
                    <span
                      v-if="student.latestTask"
                      class="status-chip"
                      :class="`status-chip--${student.latestTask.statusTone || 'neutral'}`"
                    >
                      {{ student.latestTask.statusLabel }}
                    </span>
                    <span v-else class="status-chip status-chip--neutral">未提交</span>
                  </div>
                  <div v-if="student.submissionTrajectory?.length" class="sync-student-trajectory__flow">
                    <template v-for="(item, index) in student.submissionTrajectory" :key="item.id">
                      <span
                        class="status-chip shrink-0 text-xs"
                        :class="`status-chip--${item.statusTone}`"
                        :title="trajectoryTitle(item)"
                      >
                        {{ item.code }}
                      </span>
                      <span v-if="index < student.submissionTrajectory.length - 1" class="shrink-0 text-stone-300">→</span>
                    </template>
                  </div>
                  <div v-else class="text-xs text-stone-400">{{ latestTaskMeta(student) }}</div>
                </div>
              </td>
              <td class="text-right">
                <button
                  type="button"
                  class="btn btn-sm btn-primary rounded-lg"
                  :disabled="!syncConnected"
                  @click="emit('inviteSyncStudent', student)"
                >
                  <i class="fas fa-link" aria-hidden="true"></i>
                  同步
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-sm font-bold text-stone-400">当前没有学生在普通题在线编程。</div>
    </section>

    <div class="oj-panel overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr class="text-xs uppercase tracking-widest text-stone-500">
              <th>编号</th>
              <th>题目</th>
              <th>状态</th>
              <th>难度</th>
              <th>标签</th>
              <th>AC/尝试</th>
              <th>作者</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="problem in payload.problems" :key="problem.id" :class="rowClass(problem)">
              <td class="font-mono font-black text-stone-900 dark:text-stone-100">{{ problem.code }}</td>
              <td>
                <div class="flex items-center gap-2 flex-wrap">
                  <a :href="problem.urls.detail" class="font-black text-stone-900 dark:text-stone-100 hover:text-cyan-600" @click.prevent="emit('openProblem', problem.slug, problem.urls.detail)">
                    {{ problem.title }}
                  </a>
                </div>
                <span v-if="isAdmin && !problem.visible" class="badge badge-ghost mt-2">隐藏</span>
              </td>
              <td>
                <a
                  v-if="problem.myStatus?.perfectAccepted"
                  :href="problem.urls.submissions"
                  class="diff-pill hover:opacity-80"
                  :class="statusClass(problem)"
                  @click.prevent="emit('openSubmissions', `/oj/submissions.json?problem_id=${problem.id}`)"
                >满星通过</a>
                <a
                  v-else-if="problem.myStatus?.accepted"
                  :href="problem.urls.submissions"
                  class="diff-pill hover:opacity-80"
                  :class="statusClass(problem)"
                  @click.prevent="emit('openSubmissions', `/oj/submissions.json?problem_id=${problem.id}`)"
                >通过</a>
                <a
                  v-else-if="problem.myStatus?.attempted"
                  :href="problem.urls.submissions"
                  class="diff-pill hover:opacity-80"
                  :class="statusClass(problem)"
                  @click.prevent="emit('openSubmissions', `/oj/submissions.json?problem_id=${problem.id}`)"
                >未通过</a>
                <span v-else class="text-stone-400">-</span>
              </td>
              <td>
                <button type="button" class="hover:opacity-80" @click="difficultyFilter(problem.difficulty)">
                  <DifficultyBadge :difficulty="problem.difficulty" />
                </button>
              </td>
              <td>
                <button v-for="tag in problem.tags" :key="tag" type="button" class="badge badge-outline hover:border-cyan-500 hover:text-cyan-600 mr-1" @click="tagFilter(tag)">
                  {{ tag }}
                </button>
                <span v-if="!problem.tags.length" class="text-stone-400">-</span>
              </td>
              <td>
                <a :href="problem.urls.submissions" class="font-mono font-black text-stone-700 dark:text-stone-200 hover:text-cyan-600" @click.prevent="emit('openSubmissions', `/oj/submissions.json?problem_id=${problem.id}`)">
                  {{ problem.submissionStat.accepted }}/{{ problem.submissionStat.attempts }}
                </a>
              </td>
              <td class="text-sm font-bold text-stone-500">{{ problem.author }}</td>
            </tr>
            <tr v-if="!payload.problems.length">
              <td colspan="7" class="text-center py-14 text-stone-400">当前没有匹配的题目。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
