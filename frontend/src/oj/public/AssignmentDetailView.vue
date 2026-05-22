<script setup>
const props = defineProps({
  payload: { type: Object, required: true },
});

const emit = defineEmits(['back', 'openProblem', 'openSubmissions', 'openSubmission', 'openScoreboard']);
</script>

<template>
  <div class="grid grid-cols-1 xl:grid-cols-[1fr,20rem] gap-6 items-start">
    <main class="flex flex-col gap-6">
      <section class="oj-panel p-6 md:p-8">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Assignment {{ payload.assignment.id }}</p>
            <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ payload.assignment.title }}</h1>
            <p class="text-stone-500 dark:text-stone-400 mt-3">{{ payload.assignment.targetText }}</p>
          </div>
          <div class="flex gap-2 flex-wrap">
            <span v-if="payload.assignment.isActive" class="status-chip status-chip--success">进行中</span>
            <span v-else class="status-chip status-chip--neutral">已关闭</span>
            <span class="metric-chip metric-chip--success">{{ payload.scoreSummary.acceptedCount }}/{{ payload.scoreSummary.problemCount }} AC</span>
          </div>
        </div>
      </section>

      <section class="oj-panel p-6 md:p-8">
        <div class="text-stone-400 text-sm uppercase tracking-widest mb-4">作业介绍</div>
        <div class="assignment-prose" v-html="payload.descriptionHtml"></div>
      </section>

      <section class="oj-panel overflow-hidden">
        <div class="px-6 pt-6">
          <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100">题目清单</h2>
          <p class="text-stone-500 dark:text-stone-400 mt-2">状态基于你在这份作业中的最近提交。</p>
        </div>
        <div class="overflow-x-auto mt-4">
          <table class="table">
            <thead>
              <tr class="text-xs uppercase tracking-widest text-stone-500">
                <th>状态</th>
                <th>最后提交于</th>
                <th>题目</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in payload.rows" :key="row.problem.id">
                <td>
                  <span v-if="row.accepted" class="status-chip status-chip--success">AC</span>
                  <span v-else-if="row.task" class="status-chip" :class="`status-chip--${row.task.statusTone}`">{{ row.task.statusLabel }}</span>
                  <span v-else class="status-chip status-chip--neutral">未提交</span>
                </td>
                <td>
                  <a
                    v-if="row.task"
                    :href="row.task.url"
                    class="font-mono text-stone-700 dark:text-stone-200 hover:text-cyan-600"
                    @click.prevent="emit('openSubmission', row.task.id, row.task.url)"
                  >
                    {{ row.task.createdAt }}
                  </a>
                  <span v-else class="text-stone-400">-</span>
                </td>
                <td>
                  <a
                    :href="row.problem.url"
                    class="font-black text-stone-900 dark:text-stone-100 hover:text-cyan-600"
                    @click.prevent="emit('openProblem', row.problem.slug, row.problem.url)"
                  >
                    {{ row.problem.code }} {{ row.problem.title }}
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <aside class="oj-panel p-5 sticky top-24 flex flex-col gap-5">
      <div class="flex flex-col gap-2">
        <button type="button" class="btn btn-outline rounded-lg justify-start" @click="emit('back')">
          <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回作业清单
        </button>
        <a
          :href="payload.assignment.urls.scoreboard"
          class="btn btn-outline rounded-lg justify-start"
          @click.prevent="emit('openScoreboard', payload.assignment.id, payload.assignment.urls.scoreboard)"
        >
          <i class="fas fa-chart-column" aria-hidden="true"></i> 成绩表
        </a>
        <a
          :href="payload.assignment.urls.submissions"
          class="btn btn-outline rounded-lg justify-start"
          @click.prevent="emit('openSubmissions', payload.assignment.urls.submissions.replace('/oj/submissions', '/oj/submissions.json'))"
        >
          <i class="fas fa-flag" aria-hidden="true"></i> 所有提交
        </a>
        <a v-if="payload.isAdmin && payload.assignment.urls.edit" :href="payload.assignment.urls.edit" class="btn btn-outline rounded-lg justify-start">
          <i class="fas fa-pen" aria-hidden="true"></i> 编辑作业
        </a>
      </div>

      <div>
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-3">成绩概览</div>
        <div class="grid grid-cols-2 gap-3">
          <div class="mini-stat is-success">
            <div class="mini-stat-label">通过题目</div>
            <div class="mini-stat-value">{{ payload.scoreSummary.acceptedCount }}</div>
          </div>
          <div class="mini-stat is-info">
            <div class="mini-stat-label">完成度</div>
            <div class="mini-stat-value">{{ payload.scoreSummary.completionPercent }}%</div>
          </div>
        </div>
      </div>

      <div class="border-t border-stone-200 dark:border-white/10 pt-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-3">本次作业</div>
        <div class="space-y-3 text-sm">
          <div class="meta-line"><span class="text-stone-500">题目</span><span class="font-black">{{ payload.scoreSummary.problemCount }}</span></div>
          <div class="meta-line"><span class="text-stone-500">已尝试</span><span class="font-black">{{ payload.scoreSummary.attemptedCount }}</span></div>
          <div class="meta-line"><span class="text-stone-500">提交总数</span><span class="font-black">{{ payload.scoreSummary.totalSubmissions }}</span></div>
          <div class="meta-line"><span class="text-stone-500">开始时间</span><span class="font-black text-right">{{ payload.assignment.startAt }}</span></div>
          <div class="meta-line"><span class="text-stone-500">截止时间</span><span class="font-black text-right">{{ payload.assignment.endAt }}</span></div>
          <div class="meta-line"><span class="text-stone-500">延长期限</span><span class="font-black">{{ payload.assignment.extensionDays }} 天</span></div>
        </div>
      </div>

      <div v-if="payload.recentSubmissions.length" class="border-t border-stone-200 dark:border-white/10 pt-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-3">最近提交</div>
        <div class="flex flex-col gap-2">
          <a
            v-for="task in payload.recentSubmissions"
            :key="task.id"
            :href="task.url"
            class="mini-link-card"
            @click.prevent="emit('openSubmission', task.id, task.url)"
          >
            <div class="flex items-center justify-between gap-3">
              <span class="font-mono text-sm">#{{ task.id }}</span>
              <span class="status-chip" :class="`status-chip--${task.statusTone}`">{{ task.statusLabel }}</span>
            </div>
            <div class="text-xs text-stone-400 mt-1">{{ task.problemCode }} · {{ task.createdShort }}</div>
          </a>
        </div>
      </div>
    </aside>
  </div>
</template>
