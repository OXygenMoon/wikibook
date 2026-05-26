<script setup>
import { computed } from 'vue';

const props = defineProps({
  analysis: { type: Object, default: null },
});
const emit = defineEmits(['openSubmission']);

const trajectory = computed(() => props.analysis?.my?.trajectory || []);
</script>

<template>
  <section class="flex flex-col gap-4 text-sm">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-xl font-black text-stone-900 dark:text-stone-100">提交轨迹</h2>
        <p class="text-xs text-stone-500 mt-1">保留这道题的每次提交版本，看看自己怎样一步步修出来。</p>
      </div>
      <span class="text-xs font-bold text-stone-500">{{ trajectory.length }} 个版本</span>
    </div>

    <section class="min-w-0 rounded-lg border border-stone-200/80 bg-white/35 p-4 dark:border-white/10 dark:bg-white/5">
      <div v-if="trajectory.length" class="space-y-4">
        <div class="flex min-w-0 items-center gap-1.5 overflow-x-auto pb-1">
          <template v-for="(item, index) in trajectory" :key="`flow-${item.id}`">
            <a
              :href="item.url"
              class="status-chip shrink-0 text-xs transition-colors hover:border-cyan-400"
              :class="`status-chip--${item.statusTone}`"
              :title="`第 ${item.attempt} 次 · ${item.statusLabel}`"
              @click.prevent="emit('openSubmission', item.id, item.url)"
            >
              {{ item.code }}
            </a>
            <span v-if="index < trajectory.length - 1" class="shrink-0 text-stone-300">→</span>
          </template>
        </div>

        <div class="divide-y divide-stone-200/80 dark:divide-white/10">
          <a
            v-for="item in trajectory"
            :key="item.id"
            :href="item.url"
            class="grid min-w-0 grid-cols-[4.25rem,1fr,4.5rem,4rem] gap-3 py-2.5 text-xs transition-colors hover:bg-stone-50/80 dark:hover:bg-white/5"
            @click.prevent="emit('openSubmission', item.id, item.url)"
          >
            <span class="font-black text-stone-500">v{{ item.attempt }}</span>
            <span class="flex min-w-0 items-center gap-2">
              <span class="status-chip" :class="`status-chip--${item.statusTone}`">{{ item.statusLabel }}</span>
              <span class="truncate font-mono text-stone-500">#{{ item.id }} · {{ item.createdAt }}</span>
            </span>
            <span class="text-right font-black text-stone-900 dark:text-stone-100">{{ item.score }} 分</span>
            <span class="text-right font-mono font-bold text-stone-500">{{ item.passedCount }}/{{ item.totalCount }}</span>
          </a>
        </div>
      </div>
      <div v-else class="py-8 text-center text-stone-400">还没有提交版本。</div>
    </section>
  </section>
</template>
