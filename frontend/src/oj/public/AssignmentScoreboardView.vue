<script setup>
const props = defineProps({
  payload: { type: Object, required: true },
});

const emit = defineEmits(['backAssignment', 'openProblem', 'openSubmissions', 'openSubmission']);
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="flex items-end justify-between gap-4 flex-wrap">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 flex-1">
        <div class="oj-panel p-4">
          <div class="metric-label">参与人数</div>
          <div class="text-2xl font-black text-stone-900 dark:text-stone-100">{{ payload.stats.participantCount }}</div>
        </div>
        <div class="oj-panel p-4">
          <div class="metric-label">题目数</div>
          <div class="text-2xl font-black text-stone-900 dark:text-stone-100">{{ payload.stats.problemCount }}</div>
        </div>
        <div class="oj-panel p-4">
          <div class="metric-label">开始时间</div>
          <div class="text-lg font-black text-stone-900 dark:text-stone-100">{{ payload.stats.startAt }}</div>
        </div>
        <div class="oj-panel p-4">
          <div class="metric-label">截止时间</div>
          <div class="text-lg font-black text-stone-900 dark:text-stone-100">{{ payload.stats.endAt }}</div>
        </div>
      </div>
      <div class="flex gap-2 flex-wrap">
        <a
          :href="payload.assignment.urls.detail"
          class="btn btn-outline rounded-lg"
          @click.prevent="emit('backAssignment', payload.assignment.id, payload.assignment.urls.detail)"
        >
          <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回作业
        </a>
        <a
          :href="payload.assignment.urls.submissions"
          class="btn btn-ghost rounded-lg"
          @click.prevent="emit('openSubmissions', payload.assignment.urls.submissions.replace('/oj/submissions', '/oj/submissions.json'))"
        >
          <i class="fas fa-flag" aria-hidden="true"></i> 当前作业提交
        </a>
      </div>
    </section>

    <section class="oj-panel overflow-hidden">
      <div class="px-5 py-4 border-b border-stone-200 dark:border-white/10">
        <div class="text-sm text-stone-500 dark:text-stone-400">这里只统计当前这份作业中的提交，不会混入普通 OJ 题库提交。</div>
      </div>
      <div class="scoreboard-table-wrapper">
        <table class="table scoreboard-table sticky-head">
          <thead>
            <tr class="text-xs uppercase tracking-widest text-stone-500">
              <th>排名</th>
              <th>用户</th>
              <th>班级</th>
              <th>分数</th>
              <th>AC</th>
              <th>已尝试</th>
              <th v-for="link in payload.problemLinks" :key="link.id" class="problem-col">
                <a
                  :href="link.problem.url"
                  class="font-black hover:text-cyan-600"
                  @click.prevent="emit('openProblem', link.problem.slug, link.problem.url)"
                >
                  {{ link.problem.code }}
                </a>
                <div class="text-[11px] font-normal normal-case tracking-normal text-stone-400 mt-1">{{ link.problem.title }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in payload.rows" :key="row.user.id">
              <td class="font-black text-stone-900 dark:text-stone-100">#{{ row.rank }}</td>
              <td>
                <div class="font-black text-stone-900 dark:text-stone-100">{{ row.user.name }}</div>
                <div class="text-xs text-stone-400">@{{ row.user.username }}</div>
              </td>
              <td class="text-sm text-stone-500">{{ row.user.className }}</td>
              <td class="font-black text-cyan-700 dark:text-cyan-300">{{ row.score }}</td>
              <td class="font-black text-emerald-700 dark:text-emerald-300">{{ row.acceptedCount }}/{{ payload.problemLinks.length }}</td>
              <td class="font-black text-amber-700 dark:text-amber-300">{{ row.submissionCount }}</td>
              <td v-for="cell in row.cells" :key="cell.problem.id" class="problem-col">
                <div class="cell-stack">
                  <a
                    v-if="cell.task"
                    :href="cell.task.url"
                    class="status-chip"
                    :class="`status-chip--${cell.task.statusTone}`"
                    @click.prevent="emit('openSubmission', cell.task.id, cell.task.url)"
                  >
                    {{ cell.accepted ? (cell.task.statusLabel || '通过') : cell.task.statusLabel }}
                  </a>
                  <a
                    v-else
                    :href="cell.problem.url"
                    class="status-chip status-chip--neutral"
                    @click.prevent="emit('openProblem', cell.problem.slug, cell.problem.url)"
                  >
                    未提交
                  </a>
                  <div class="text-xs text-stone-400">{{ cell.task?.createdShort || '-' }}</div>
                </div>
              </td>
            </tr>
            <tr v-if="!payload.rows.length">
              <td :colspan="6 + payload.problemLinks.length" class="text-center py-14 text-stone-400">这份作业还没有可展示的成绩数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
