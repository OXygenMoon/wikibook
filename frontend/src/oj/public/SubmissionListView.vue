<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { requestJson } from './api.js';

const props = defineProps({
  payload: { type: Object, required: true },
});

const emit = defineEmits(['filter', 'openProblem', 'openSubmission']);
const filters = reactive({
  status: '',
  language: '',
  user: '',
  problem: '',
  problemId: null,
  assignmentId: null,
  mine: false,
});

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'queued', label: '排队中' },
  { value: 'running', label: '评测中' },
  { value: 'PAC', label: '满星通过' },
  { value: 'AC', label: '通过' },
  { value: 'failed', label: '未通过' },
  { value: 'system_error', label: '系统错误' },
];

const timeStats = computed(() => props.payload.submissionTimeStats || props.payload.submissionProblemStats || []);
const totalSubmissions = computed(() => timeStats.value.find((stat) => stat.key === 'all')?.count ?? 0);
const timedStats = computed(() => timeStats.value.filter((stat) => stat.key !== 'all'));
const maxTimedStatCount = computed(() => Math.max(1, ...timedStats.value.map((stat) => Number(stat.count) || 0)));
const deletingSubmissionId = ref(null);

function syncFilters() {
  Object.assign(filters, props.payload.filters || {});
}

function statPercent(stat) {
  const count = Number(stat.count) || 0;
  if (!count) return '0%';
  return `${Math.max(6, Math.round((count / maxTimedStatCount.value) * 100))}%`;
}

function buildUrl(reset = false) {
  if (reset) return '/oj/submissions.json';
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.language) params.set('language', filters.language);
  if (filters.user && props.payload.isAdmin) params.set('user', filters.user);
  if (filters.problemId) params.set('problem_id', filters.problemId);
  else if (filters.problem) params.set('problem', filters.problem);
  if (filters.assignmentId) params.set('assignment_id', filters.assignmentId);
  if (filters.mine) params.set('mine', '1');
  const query = params.toString();
  return `/oj/submissions.json${query ? `?${query}` : ''}`;
}

function submitFilter() {
  emit('filter', buildUrl());
}

function resetFilter() {
  emit('filter', buildUrl(true));
}

async function deleteSubmission(row) {
  if (!row?.deleteUrl || deletingSubmissionId.value) return;
  if (!window.confirm(`确认删除提交 #${row.id}？此操作不可恢复。`)) return;

  deletingSubmissionId.value = row.id;
  try {
    await requestJson(row.deleteUrl, { method: 'DELETE' });
    emit('filter', buildUrl());
  } catch (error) {
    window.alert(error.message || '删除失败，请稍后再试。');
  } finally {
    deletingSubmissionId.value = null;
  }
}

watch(() => props.payload, syncFilters, { immediate: true });
</script>

<template>
  <div class="flex flex-col gap-6">
    <section v-if="timeStats.length" class="oj-panel p-4 md:p-5">
      <div class="flex flex-col xl:flex-row gap-4">
        <div class="rounded-xl bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-100 dark:border-cyan-800/70 p-4 xl:w-52">
          <div class="text-xs text-cyan-700 dark:text-cyan-200 uppercase tracking-widest mb-2">全部</div>
          <div class="text-3xl font-black text-cyan-700 dark:text-cyan-100">{{ totalSubmissions }}</div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 flex-1">
          <div v-for="stat in timedStats" :key="stat.key" class="rounded-xl border border-stone-200/80 dark:border-white/10 bg-stone-50/80 dark:bg-white/5 p-3">
            <div class="flex items-baseline justify-between gap-2">
              <span class="text-xs font-black text-stone-500 dark:text-stone-400">{{ stat.label }}</span>
              <span class="text-lg font-black text-stone-900 dark:text-stone-100">{{ stat.count }}</span>
            </div>
            <div class="mt-2 h-1.5 rounded-full bg-stone-200 dark:bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-cyan-500" :style="{ width: statPercent(stat) }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="oj-panel p-4 md:p-5">
      <div class="flex items-center justify-between gap-4 flex-wrap mb-4">
        <div>
          <h2 class="text-xl font-black text-stone-900 dark:text-stone-100">提交筛选</h2>
          <p class="text-sm text-stone-500 mt-1">当前显示 {{ payload.count }} 条记录。</p>
        </div>
        <a v-if="payload.selectedAssignment" :href="payload.selectedAssignment.url" class="btn btn-outline rounded-lg">
          <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回作业
        </a>
      </div>

      <form class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3 items-end" @submit.prevent="submitFilter">
        <label v-if="payload.isAdmin" class="form-control">
          <span class="label-text font-bold mb-1">用户</span>
          <input v-model.trim="filters.user" type="text" class="input input-bordered rounded-lg" placeholder="用户名、姓名或 UID">
        </label>

        <div v-if="payload.selectedAssignment" class="form-control">
          <span class="label-text font-bold mb-1">作业</span>
          <div class="filter-static">{{ payload.selectedAssignment.title }}</div>
        </div>

        <div v-if="payload.selectedProblem" class="form-control">
          <span class="label-text font-bold mb-1">题目</span>
          <div class="filter-static">{{ payload.selectedProblem.code }} · {{ payload.selectedProblem.title }}</div>
        </div>
        <label v-else class="form-control">
          <span class="label-text font-bold mb-1">题目</span>
          <input v-model.trim="filters.problem" type="text" class="input input-bordered rounded-lg" placeholder="题号、标题或 Slug">
        </label>

        <label class="form-control">
          <span class="label-text font-bold mb-1">语言</span>
          <select v-model="filters.language" class="select select-bordered rounded-lg" @change="submitFilter">
            <option value="">全部语言</option>
            <option v-for="language in payload.availableLanguages" :key="language" :value="language">{{ language }}</option>
          </select>
        </label>

        <label class="form-control">
          <span class="label-text font-bold mb-1">状态</span>
          <select v-model="filters.status" class="select select-bordered rounded-lg" @change="submitFilter">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>

        <div class="flex gap-2">
          <button type="submit" class="btn btn-primary rounded-lg flex-1">
            <i class="fas fa-filter" aria-hidden="true"></i> 筛选
          </button>
          <button type="button" class="btn btn-ghost rounded-lg" @click="resetFilter">重置</button>
        </div>
      </form>
    </section>

    <section class="oj-panel overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr class="text-xs uppercase tracking-widest text-stone-500">
              <th>ID</th>
              <th>题目</th>
              <th>来源</th>
              <th v-if="payload.isAdmin">用户</th>
              <th>语言</th>
              <th>状态</th>
              <th>得分</th>
              <th>时间</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in payload.submissions" :key="row.id" class="submission-row">
              <td class="font-mono font-black">#{{ row.id }}</td>
              <td>
                <a
                  v-if="row.problem"
                  :href="row.problem.url"
                  class="font-black text-stone-900 dark:text-stone-100 hover:text-cyan-600"
                  @click.prevent="emit('openProblem', row.problem.slug, row.problem.url)"
                >
                  {{ row.problem.code }} · {{ row.problem.title }}
                </a>
                <span v-else class="text-stone-400">-</span>
              </td>
              <td>
                <a
                  v-if="row.assignment"
                  :href="row.assignment.url"
                  class="badge badge-outline border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-200"
                >
                  {{ row.assignment.title }}
                </a>
                <span v-else class="badge badge-outline">题库</span>
              </td>
              <td v-if="payload.isAdmin" class="font-bold text-stone-500">{{ row.user }}</td>
              <td><span class="badge badge-outline">{{ row.language }}</span></td>
              <td><span class="status-chip" :class="`status-chip--${row.statusTone}`">{{ row.statusLabel }}</span></td>
              <td>
                <span class="metric-chip" :class="row.totalScore > 0 ? 'metric-chip--success' : 'metric-chip--danger'">
                  {{ row.totalScore }} 分
                </span>
              </td>
              <td class="font-mono text-sm text-stone-500">{{ row.createdAt }}</td>
              <td>
                <div class="flex justify-end gap-2">
                  <a :href="row.url" class="btn btn-sm btn-outline rounded-lg" @click.prevent="emit('openSubmission', row.id, row.url)">
                    查看
                  </a>
                  <button
                    v-if="payload.isAdmin && row.deleteUrl"
                    type="button"
                    class="btn btn-sm btn-outline text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300 dark:text-red-300 dark:border-red-900/70 dark:hover:bg-red-950/40 rounded-lg"
                    :disabled="deletingSubmissionId === row.id"
                    @click="deleteSubmission(row)"
                  >
                    <i class="fas fa-trash" aria-hidden="true"></i>
                    {{ deletingSubmissionId === row.id ? '删除中...' : '删除' }}
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!payload.submissions.length">
              <td :colspan="payload.isAdmin ? 9 : 8" class="text-center py-14 text-stone-400">暂无匹配的提交记录。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
