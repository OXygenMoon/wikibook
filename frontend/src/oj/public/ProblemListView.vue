<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({
  payload: { type: Object, required: true },
  isAdmin: { type: Boolean, default: false },
});

const emit = defineEmits(['filter', 'openProblem', 'openSubmissions']);
const filters = reactive({ q: '', difficulty: '', visibility: 'visible' });
let debounceTimer = 0;

function syncFilters() {
  Object.assign(filters, props.payload.filters || {});
}

function diffClass(difficulty) {
  if (difficulty === 'easy') return 'bg-emerald-100 text-emerald-700';
  if (difficulty === 'hard') return 'bg-rose-100 text-rose-700';
  return 'bg-amber-100 text-amber-700';
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

function scheduleFilter() {
  window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(submitFilter, 260);
}

function tagFilter(tag) {
  filters.q = tag;
  submitFilter();
}

watch(() => props.payload, syncFilters, { immediate: true });
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">Total</div>
        <div class="text-2xl font-black text-stone-900 dark:text-stone-100">{{ payload.stats.total }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">Easy</div>
        <div class="text-2xl font-black text-emerald-600">{{ payload.stats.easy }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">Medium</div>
        <div class="text-2xl font-black text-amber-600">{{ payload.stats.medium }}</div>
      </div>
      <div class="oj-panel p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-1">Hard</div>
        <div class="text-2xl font-black text-rose-600">{{ payload.stats.hard }}</div>
      </div>
    </div>

    <form class="oj-panel p-4 grid grid-cols-1 md:grid-cols-[1fr,12rem,12rem,auto] gap-3 items-end" @submit.prevent="submitFilter">
      <label class="form-control">
        <span class="label-text font-bold mb-1">搜索</span>
        <input v-model.trim="filters.q" type="text" class="input input-bordered rounded-lg" placeholder="编号、题目、标签" @input="scheduleFilter">
      </label>
      <label class="form-control">
        <span class="label-text font-bold mb-1">难度</span>
        <select v-model="filters.difficulty" class="select select-bordered rounded-lg" @change="submitFilter">
          <option value="">全部难度</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
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
    </form>

    <div class="oj-panel overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr class="text-xs uppercase tracking-widest text-stone-500">
              <th>编号</th>
              <th>题目</th>
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
                  <span v-if="problem.myStatus?.perfectAccepted" class="badge badge-success badge-outline font-black">满星通过</span>
                  <span v-else-if="problem.myStatus?.accepted" class="badge badge-success badge-outline font-black">通过</span>
                  <span v-else-if="problem.myStatus?.attempted" class="badge badge-error badge-outline font-black">未通过</span>
                </div>
                <span v-if="isAdmin && !problem.visible" class="badge badge-ghost mt-2">隐藏</span>
              </td>
              <td><span class="diff-pill" :class="diffClass(problem.difficulty)">{{ problem.difficulty }}</span></td>
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
              <td colspan="6" class="text-center py-14 text-stone-400">当前没有匹配的题目。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
