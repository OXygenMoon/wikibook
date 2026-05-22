<script setup>
const props = defineProps({
  payload: { type: Object, required: true },
  urls: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['openAssignment']);
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="oj-panel p-6 md:p-8">
      <div class="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <p class="text-sm text-stone-500">这里会显示你当前有权限进入的 OJ 作业。</p>
          <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100 mt-2">当前共 {{ payload.count }} 份作业</h2>
        </div>
        <a v-if="payload.isAdmin && urls.createAssignment" :href="urls.createAssignment" class="btn btn-primary rounded-lg">
          <i class="fas fa-plus" aria-hidden="true"></i> 新建作业
        </a>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <a
        v-for="assignment in payload.assignments"
        :key="assignment.id"
        :href="assignment.urls.detail"
        class="assignment-card"
        @click.prevent="emit('openAssignment', assignment.id, assignment.urls.detail)"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="text-xs font-black tracking-[0.24em] uppercase text-stone-400 mb-2">Assignment #{{ assignment.id }}</div>
            <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100">{{ assignment.title }}</h2>
          </div>
          <span v-if="assignment.isActive" class="status-chip status-chip--success">进行中</span>
          <span v-else class="status-chip status-chip--neutral">已关闭</span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5 text-sm">
          <div class="mini-stat">
            <div class="mini-stat-label">题目数</div>
            <div class="mini-stat-value">{{ assignment.problemCount }}</div>
          </div>
          <div class="mini-stat is-success">
            <div class="mini-stat-label">已通过</div>
            <div class="mini-stat-value">{{ assignment.acceptedCount }}</div>
          </div>
          <div class="mini-stat is-warning">
            <div class="mini-stat-label">已尝试</div>
            <div class="mini-stat-value">{{ assignment.attemptedCount }}</div>
          </div>
          <div class="mini-stat is-info">
            <div class="mini-stat-label">可延长</div>
            <div class="mini-stat-value">{{ assignment.extensionDays }} 天</div>
          </div>
        </div>

        <div class="flex items-center justify-between gap-4 mt-5 text-sm text-stone-500 dark:text-stone-400">
          <span>{{ assignment.targetText }}</span>
          <span v-if="assignment.lastTask">最近提交 {{ assignment.lastTask.createdShort }}</span>
          <span v-else-if="assignment.endShort">截止 {{ assignment.endShort }}</span>
          <span v-else>暂无截止时间</span>
        </div>
      </a>

      <div v-if="!payload.assignments.length" class="oj-panel p-10 text-center text-stone-400 xl:col-span-2">
        当前还没有你可见的 OJ 作业。
      </div>
    </section>
  </div>
</template>
