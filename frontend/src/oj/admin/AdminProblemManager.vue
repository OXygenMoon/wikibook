<script setup>
import { computed, ref } from 'vue';
import { requestJson } from './api.js';
import DifficultyBadge from '../DifficultyBadge.vue';

const props = defineProps({
  initialProblems: {
    type: Array,
    default: () => [],
  },
  problemsUrl: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['navigateEdit', 'navigateFiles']);
const problems = ref([...props.initialProblems]);
const loading = ref(false);
const notice = ref(null);

const countText = computed(() => `当前共 ${problems.value.length} 道题。`);

function showNotice(message, category = 'success') {
  notice.value = { message, category };
  window.setTimeout(() => {
    if (notice.value?.message === message) notice.value = null;
  }, 2800);
}

async function refreshProblems() {
  loading.value = true;
  try {
    const data = await requestJson(props.problemsUrl);
    problems.value = data.problems || [];
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    loading.value = false;
  }
}

async function deleteProblem(problem) {
  if (!window.confirm(`确认删除这道 OJ 题目吗？\n${problem.code} ${problem.title}`)) return;

  loading.value = true;
  try {
    const data = await requestJson(problem.urls.delete, { method: 'POST' });
    problems.value = problems.value.filter((item) => item.id !== problem.id);
    showNotice(data.message || '题目已删除。');
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="oj-panel overflow-hidden">
    <div class="px-6 py-5 border-b border-stone-200/80 dark:border-white/10 flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">已有题目</h2>
        <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">{{ countText }}</p>
      </div>
      <button type="button" class="btn btn-sm btn-outline rounded-xl" :disabled="loading" @click="refreshProblems">
        <i class="fas fa-rotate-right" :class="{ 'fa-spin': loading }" aria-hidden="true"></i>
      </button>
    </div>

    <div v-if="notice" class="mx-6 mt-5 oj-vue-alert" :class="notice.category === 'error' ? 'oj-vue-alert--error' : 'oj-vue-alert--success'">
      {{ notice.message }}
    </div>

    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr class="text-stone-500 uppercase text-xs tracking-widest">
            <th>UID</th>
            <th>编号</th>
            <th>标题</th>
            <th>难度</th>
            <th>测试点</th>
            <th>文件</th>
            <th>语言</th>
            <th>状态</th>
            <th>更新时间</th>
            <th class="text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="problem in problems" :key="problem.id">
            <td class="font-mono font-bold text-stone-500">{{ problem.uid }}</td>
            <td class="font-mono font-black text-stone-800 dark:text-stone-100">{{ problem.code }}</td>
            <td>
              <div class="font-black text-stone-800 dark:text-stone-100">{{ problem.title }}</div>
              <div class="text-xs font-mono text-stone-400 mt-1">{{ problem.slug }}</div>
            </td>
            <td>
              <DifficultyBadge :difficulty="problem.difficulty" />
            </td>
            <td class="font-bold">{{ problem.testcaseCount }}</td>
            <td class="font-bold">{{ problem.fileCount }}</td>
            <td class="text-sm text-stone-500">{{ problem.allowedLanguages }}</td>
            <td>
              <span v-if="problem.visible" class="oj-pill bg-sky-100 text-sky-700">visible</span>
              <span v-else class="oj-pill bg-stone-200 text-stone-600">hidden</span>
            </td>
            <td class="text-sm text-stone-500">{{ problem.updatedAt }}</td>
            <td>
              <div class="flex justify-end gap-2 flex-wrap">
                <a :href="problem.urls.edit" class="btn btn-sm oj-action-btn" title="编辑题目" aria-label="编辑题目" @click.prevent="emit('navigateEdit', problem.id)">
                  <i class="fas fa-pen" aria-hidden="true"></i>
                </a>
                <a :href="problem.urls.files" class="btn btn-sm btn-outline oj-action-btn" title="文件管理" aria-label="文件管理" @click.prevent="emit('navigateFiles', problem.id)">
                  <i class="fas fa-folder-open" aria-hidden="true"></i>
                </a>
                <button type="button" class="btn btn-sm btn-error btn-outline oj-action-btn" title="删除题目" aria-label="删除题目" :disabled="loading" @click="deleteProblem(problem)">
                  <i class="fas fa-trash" aria-hidden="true"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!problems.length">
            <td colspan="10" class="text-center py-12 text-stone-400">还没有 OJ 题目，先创建第一道题吧。</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
