<script setup>
import { ref } from 'vue';
import { requestJson } from './api.js';
import DifficultyBadge from '../DifficultyBadge.vue';

const props = defineProps({
  workspace: { type: Object, required: true },
});

const emit = defineEmits(['back', 'open-problem', 'open-code', 'open-submissions', 'open-submission', 'submitted']);

const activeLanguage = ref(props.workspace.defaultLanguage || props.workspace.problem.allowedLanguages[0] || 'python');
const sourceCode = ref(localStorage.getItem(storageKey(activeLanguage.value)) || props.workspace.initialCode?.[activeLanguage.value] || '');
const submitting = ref(false);
const notice = ref('');

function storageKey(language) {
  return `oj-submit-draft:${props.workspace.problem.slug}:${props.workspace.storageScope}:${language}`;
}

function syncDraft() {
  localStorage.setItem(storageKey(activeLanguage.value), sourceCode.value);
}

function changeLanguage(event) {
  syncDraft();
  activeLanguage.value = event.target.value;
  sourceCode.value = localStorage.getItem(storageKey(activeLanguage.value)) || props.workspace.initialCode?.[activeLanguage.value] || '';
}

function setNotice(text) {
  notice.value = text;
  window.setTimeout(() => {
    if (notice.value === text) notice.value = '';
  }, 3200);
}

async function submitCode() {
  if (submitting.value) return;
  if (!sourceCode.value.trim()) {
    setNotice('请先填写代码再提交。');
    return;
  }
  submitting.value = true;
  syncDraft();
  try {
    const data = await requestJson(props.workspace.urls.submit, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: activeLanguage.value,
        source_code: sourceCode.value,
      }),
    });
    emit('submitted', data.submissionDetail, data.redirectUrl, data.message);
  } catch (error) {
    setNotice(error.message || '提交失败，请稍后重试。');
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="grid grid-cols-1 xl:grid-cols-[1fr,22rem] gap-6 items-start">
    <main class="oj-panel p-6 md:p-8">
      <div class="border-b border-stone-200 dark:border-white/10 pb-6 mb-6">
        <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Submit {{ workspace.problem.code }} · UID {{ workspace.problem.uid }}</p>
        <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ workspace.problem.title }}</h1>
        <p class="text-stone-500 dark:text-stone-400 mt-3">这里是单独的提交通道。选择语言，粘贴代码，提交后直接进入评测结果。</p>
      </div>

      <div v-if="notice" class="oj-vue-alert oj-vue-alert--error mb-5">{{ notice }}</div>

      <div class="flex flex-col gap-5">
        <div class="grid grid-cols-1 md:grid-cols-[14rem,1fr] gap-4">
          <label class="form-control">
            <span class="label-text font-bold mb-2">语言</span>
            <select class="select select-bordered rounded-lg" :value="activeLanguage" @change="changeLanguage">
              <option v-for="language in workspace.problem.allowedLanguages" :key="language" :value="language">{{ language }}</option>
            </select>
          </label>
          <div class="rounded-lg bg-cyan-50 dark:bg-cyan-900/20 px-4 py-3 text-sm text-cyan-800 dark:text-cyan-100 leading-6">
            系统会使用当前题目的全部测试点进行评测。公开样例可以帮助你自测，隐藏数据会在后台一起运行。
          </div>
        </div>

        <label class="form-control">
          <span class="label-text font-bold mb-2">源代码</span>
          <textarea
            v-model="sourceCode"
            class="textarea source-editor w-full"
            spellcheck="false"
            required
            placeholder="# 在这里粘贴你的代码"
            @input="syncDraft"
          ></textarea>
        </label>

        <div class="flex items-center justify-between gap-4 flex-wrap">
          <div class="flex gap-2 flex-wrap">
            <button type="button" class="btn btn-ghost rounded-lg" @click="emit('back')">
              <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回题目
            </button>
            <a :href="workspace.urls.code" class="btn btn-outline rounded-lg" @click.prevent="emit('open-code', workspace.problem.slug, workspace.urls.code)">
              <i class="fas fa-code" aria-hidden="true"></i> 去在线编程
            </a>
            <a
              v-if="workspace.latestTask"
              :href="workspace.latestTask.url"
              class="btn btn-ghost rounded-lg"
              @click.prevent="emit('open-submission', workspace.latestTask.id, workspace.latestTask.url)"
            >
              最近提交 #{{ workspace.latestTask.id }}
            </a>
          </div>
          <button type="button" class="btn btn-primary rounded-lg px-8" :disabled="submitting" @click="submitCode">
            <i class="fas fa-paper-plane" aria-hidden="true"></i> {{ submitting ? '提交中...' : '提交并评测' }}
          </button>
        </div>
      </div>
    </main>

    <aside class="oj-panel p-5 sticky top-24">
      <h2 class="text-xl font-black text-stone-900 dark:text-stone-100 mb-4">题目信息</h2>
      <div class="flex flex-col gap-3 text-sm">
        <div class="meta-line"><span class="text-stone-500">UID</span><span class="font-mono font-bold">{{ workspace.problem.uid }}</span></div>
        <div class="meta-line"><span class="text-stone-500">编号</span><span class="font-mono font-bold">{{ workspace.problem.code }}</span></div>
        <div class="meta-line"><span class="text-stone-500">难度</span><DifficultyBadge :difficulty="workspace.problem.difficulty" /></div>
        <div class="meta-line"><span class="text-stone-500">时间限制</span><span class="font-bold">{{ workspace.problem.timeLimitMs }} ms</span></div>
        <div class="meta-line"><span class="text-stone-500">内存限制</span><span class="font-bold">{{ workspace.problem.memoryLimitMb }} MB</span></div>
        <div class="meta-line"><span class="text-stone-500">测试点</span><span class="font-bold">{{ workspace.problem.testcaseCount }}</span></div>
      </div>
    </aside>
  </div>
</template>
