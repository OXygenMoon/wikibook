<script setup>
import { ref, watch } from 'vue';
import { postForm } from './api.js';

const props = defineProps({
  problem: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['saved']);
const pythonTemplate = ref(props.problem.pythonTemplate || '');
const saving = ref(false);
const notice = ref(null);

watch(
  () => props.problem,
  (problem) => {
    pythonTemplate.value = problem.pythonTemplate || '';
  },
);

function showNotice(message, category = 'success') {
  notice.value = { message, category };
  window.setTimeout(() => {
    if (notice.value?.message === message) notice.value = null;
  }, 2800);
}

async function saveTemplate() {
  saving.value = true;
  const formData = new FormData();
  formData.set('python_template', pythonTemplate.value || '');
  try {
    const data = await postForm(props.problem.urls.templateSave, formData);
    if (data.problem) emit('saved', data.problem);
    showNotice(data.message || '本题模板已保存。');
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    saving.value = false;
  }
}

function clearTemplate() {
  pythonTemplate.value = '';
}
</script>

<template>
  <form class="workbench-shell p-6 md:p-8 flex flex-col gap-8" @submit.prevent="saveTemplate">
    <div v-if="notice" class="oj-vue-alert" :class="notice.category === 'error' ? 'oj-vue-alert--error' : 'oj-vue-alert--success'">
      {{ notice.message }}
    </div>

    <section class="bench-card p-5 flex flex-col gap-5">
      <div>
        <p class="text-xs font-black tracking-[0.26em] uppercase text-cyan-600 mb-2">Problem Template</p>
        <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">本题 Python 模板</h2>
        <p class="text-sm text-stone-500 dark:text-stone-400 mt-2">
          本题模板优先级高于学生自己的 OJ 设置。留空时，未开始的新草稿会使用学生个人模板；学生也未设置时从空白编辑器开始。
        </p>
      </div>
      <textarea
        v-model="pythonTemplate"
        class="textarea textarea-bordered rounded-2xl mono-editor"
        spellcheck="false"
        placeholder="可选：填写这道题希望学生看到的 Python 起始代码"
      ></textarea>
    </section>

    <div class="flex items-center justify-between gap-4 flex-wrap pt-4 border-t border-stone-200 dark:border-white/10">
      <p class="text-sm text-stone-500 dark:text-stone-400 font-mono">uid={{ problem.uid }} / code={{ problem.code }} / slug={{ problem.slug }}</p>
      <div class="flex gap-3 flex-wrap">
        <button type="button" class="btn btn-outline rounded-2xl px-6" :disabled="saving" @click="clearTemplate">清空本题模板</button>
        <button type="submit" class="btn btn-primary rounded-2xl px-8" :disabled="saving">{{ saving ? '保存中...' : '保存本题模板' }}</button>
      </div>
    </div>
  </form>
</template>
