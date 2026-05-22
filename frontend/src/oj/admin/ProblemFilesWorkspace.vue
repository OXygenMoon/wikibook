<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { postForm, requestJson } from './api.js';

const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
  workspaceUrl: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['workspaceUpdated']);
const workspace = ref(props.workspace);
const notice = ref(null);
const busy = ref(false);
const pairForm = reactive({
  caseIndex: props.workspace.stats?.nextCaseNumber || 1,
  inputContent: '',
  outputContent: '',
  overwrite: false,
});
const textForm = reactive({ filename: '', content: '' });
const assetForm = reactive({ filename: '', content: '' });
const uploadInput = ref(null);
const openFileId = ref(null);

const statCards = computed(() => [
  ['题目 UID', workspace.value.problem.uid],
  ['题号', workspace.value.problem.code],
  ['测试点', workspace.value.stats.testcaseCount],
  ['数据文件', workspace.value.stats.dataFileCount],
  ['附加文件', workspace.value.stats.assetFileCount],
  ['下一组号', workspace.value.stats.nextCaseNumber],
]);

function showNotice(message, category = 'success') {
  notice.value = { message, category };
  window.setTimeout(() => {
    if (notice.value?.message === message) notice.value = null;
  }, 3200);
}

function syncWorkspace(nextWorkspace) {
  workspace.value = nextWorkspace;
  pairForm.caseIndex = nextWorkspace.stats.nextCaseNumber || 1;
  emit('workspaceUpdated', nextWorkspace);
}

watch(
  () => props.workspace,
  (nextWorkspace) => {
    workspace.value = nextWorkspace;
    pairForm.caseIndex = nextWorkspace?.stats?.nextCaseNumber || 1;
  },
);

async function refreshWorkspace() {
  busy.value = true;
  try {
    const data = await requestJson(props.workspaceUrl);
    syncWorkspace(data.workspace);
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    busy.value = false;
  }
}

async function submitWorkspaceForm(url, formData, successReset) {
  busy.value = true;
  try {
    const data = await postForm(url, formData);
    if (data.workspace) syncWorkspace(data.workspace);
    showNotice(data.message || '操作完成。', data.category || 'success');
    if (successReset) successReset();
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    busy.value = false;
  }
}

function createPair() {
  const formData = new FormData();
  formData.set('case_index', pairForm.caseIndex);
  formData.set('input_content', pairForm.inputContent);
  formData.set('output_content', pairForm.outputContent);
  if (pairForm.overwrite) formData.set('overwrite', '1');
  submitWorkspaceForm(workspace.value.urls.createPair, formData, () => {
    pairForm.inputContent = '';
    pairForm.outputContent = '';
    pairForm.overwrite = false;
  });
}

function createTextFile(isAsset = false) {
  const formState = isAsset ? assetForm : textForm;
  const formData = new FormData();
  formData.set('filename', formState.filename);
  formData.set('content', formState.content);
  submitWorkspaceForm(workspace.value.urls.createText, formData, () => {
    formState.filename = '';
    formState.content = '';
  });
}

function uploadFiles() {
  const files = uploadInput.value?.files || [];
  if (!files.length) {
    showNotice('没有选择要上传的文件。', 'error');
    return;
  }
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append('files', file));
  submitWorkspaceForm(workspace.value.urls.upload, formData, () => {
    uploadInput.value.value = '';
  });
}

function updateFile(file) {
  const formData = new FormData();
  formData.set('filename', file.filename);
  formData.set('content', file.content || '');
  submitWorkspaceForm(file.urls.update, formData);
}

function deleteFile(file) {
  if (!window.confirm(`确认删除这个文件吗？\n${file.filename}`)) return;
  submitWorkspaceForm(file.urls.delete, new FormData());
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <div v-if="notice" class="oj-vue-alert" :class="notice.category === 'error' ? 'oj-vue-alert--error' : 'oj-vue-alert--success'">
      {{ notice.message }}
    </div>

    <section class="bench-card p-5 flex flex-col gap-5">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p class="text-xs font-black tracking-[0.2em] text-stone-400 mb-2">状态概览</p>
          <h2 class="text-xl font-black text-stone-800 dark:text-stone-100">文件工作区状态</h2>
        </div>
        <button type="button" class="btn btn-sm btn-outline rounded-xl" :disabled="busy" @click="refreshWorkspace">
          <i class="fas fa-rotate-right" :class="{ 'fa-spin': busy }" aria-hidden="true"></i>
        </button>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <div v-for="[label, value] in statCards" :key="label" class="rounded-2xl bg-stone-100 dark:bg-white/5 p-4">
          <div class="text-xs font-bold tracking-[0.16em] text-stone-400 mb-2 whitespace-nowrap">{{ label }}</div>
          <div class="text-[2.6rem] leading-none whitespace-nowrap font-black text-stone-800 dark:text-stone-100 font-mono">{{ value }}</div>
        </div>
      </div>
    </section>

    <section class="workbench-shell p-6 md:p-8 flex flex-col gap-6">
      <div>
        <p class="text-xs font-black tracking-[0.28em] uppercase text-emerald-600 mb-2">Test Data</p>
        <h2 class="text-2xl font-black text-stone-800 dark:text-stone-100">测试数据工作区</h2>
        <p class="text-stone-500 dark:text-stone-400 mt-2">创建或修改 `.in/.out` 后，会自动覆盖本题的隐藏测试点。</p>
      </div>

      <div class="grid grid-cols-1 2xl:grid-cols-[1.55fr,1fr] gap-4 items-start">
        <form class="bench-card p-5 flex flex-col gap-4" @submit.prevent="createPair">
          <div>
            <p class="text-sm font-black text-stone-800 dark:text-stone-100">快速创建一组 `N.in / N.out`</p>
            <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">默认建议下一组编号 {{ workspace.stats.nextCaseNumber }}。</p>
          </div>
          <div class="flex gap-3 flex-wrap items-center">
            <input v-model.number="pairForm.caseIndex" type="number" min="1" class="input input-bordered rounded-2xl font-mono w-32" required>
            <label class="label cursor-pointer gap-2">
              <input v-model="pairForm.overwrite" type="checkbox" class="checkbox checkbox-sm">
              <span class="label-text">若已存在则覆盖</span>
            </label>
            <button type="submit" class="btn btn-primary rounded-2xl" :disabled="busy">创建这一组文件</button>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <label class="form-control">
              <span class="label-text font-bold mb-2">输入内容</span>
              <textarea v-model="pairForm.inputContent" class="textarea textarea-bordered rounded-2xl mono-editor mono-editor--compact" :placeholder="`这里直接输入 ${workspace.stats.nextCaseNumber}.in ...`"></textarea>
            </label>
            <label class="form-control">
              <span class="label-text font-bold mb-2">输出内容</span>
              <textarea v-model="pairForm.outputContent" class="textarea textarea-bordered rounded-2xl mono-editor mono-editor--compact" :placeholder="`这里直接输入 ${workspace.stats.nextCaseNumber}.out ...`"></textarea>
            </label>
          </div>
        </form>

        <form class="bench-card p-5 flex flex-col gap-4" @submit.prevent="createTextFile(false)">
          <div>
            <p class="text-sm font-black text-stone-800 dark:text-stone-100">单独创建文本文件</p>
            <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">适合 `special.in`、`checker.txt`、`config.yaml`。</p>
          </div>
          <div class="flex gap-3 flex-wrap items-center">
            <input v-model="textForm.filename" type="text" class="input input-bordered rounded-2xl font-mono flex-1 min-w-[16rem]" placeholder="例如：special.in" required>
            <button type="submit" class="btn btn-outline rounded-2xl" :disabled="busy">创建文本文件</button>
          </div>
          <textarea v-model="textForm.content" class="textarea textarea-bordered rounded-2xl mono-editor mono-editor--compact" placeholder="直接输入文件内容..."></textarea>
        </form>
      </div>

      <div class="flex flex-col gap-4">
        <details v-for="file in workspace.dataFiles" :key="file.id" class="file-row p-5" :open="openFileId === file.id || (!openFileId && workspace.dataFiles[0]?.id === file.id)">
          <summary class="cursor-pointer list-none flex items-center justify-between gap-4 flex-wrap" @click="openFileId = file.id">
            <div>
              <div class="font-bold text-stone-800 dark:text-stone-100">{{ file.filename }}</div>
              <div class="text-xs text-stone-400 mt-1">{{ file.fileSizeKb }} KB · {{ file.uploadedAt }}</div>
            </div>
            <div class="flex gap-2 flex-wrap">
              <a :href="file.filePath" target="_blank" class="btn btn-sm rounded-xl">查看原文件</a>
              <button type="button" class="btn btn-sm btn-error btn-outline rounded-xl" :disabled="busy" @click.stop.prevent="deleteFile(file)">删除</button>
            </div>
          </summary>
          <form v-if="file.isTextEditable" class="mt-5 flex flex-col gap-4" @submit.prevent="updateFile(file)">
            <div class="flex gap-3 flex-wrap items-center">
              <input v-model="file.filename" type="text" class="input input-bordered rounded-2xl font-mono flex-1 min-w-[16rem]" required>
              <button type="submit" class="btn btn-primary rounded-2xl" :disabled="busy">保存这个数据文件</button>
            </div>
            <textarea v-model="file.content" class="textarea textarea-bordered rounded-2xl mono-editor"></textarea>
          </form>
        </details>
        <div v-if="!workspace.dataFiles.length" class="bench-card p-8 text-center text-stone-400">
          当前还没有测试数据文件。先在上面快速创建 `{{ workspace.stats.nextCaseNumber }}.in / {{ workspace.stats.nextCaseNumber }}.out` 吧。
        </div>
      </div>
    </section>

    <section class="workbench-shell p-6 md:p-8 flex flex-col gap-6">
      <div>
        <p class="text-xs font-black tracking-[0.28em] uppercase text-fuchsia-600 mb-2">Assets</p>
        <h2 class="text-2xl font-black text-stone-800 dark:text-stone-100">附加文件空间</h2>
        <p class="text-stone-500 dark:text-stone-400 mt-2">这里放图片、PDF、压缩包，或者题面引用的说明性文本文件。</p>
      </div>

      <div class="grid grid-cols-1 2xl:grid-cols-[1fr,1fr] gap-4 items-start">
        <form class="bench-card p-5" @submit.prevent="uploadFiles">
          <p class="text-sm font-black text-stone-800 dark:text-stone-100 mb-3">上传文件</p>
          <div class="flex gap-3 flex-wrap items-center">
            <input ref="uploadInput" type="file" multiple class="file-input file-input-bordered rounded-2xl flex-1 min-w-[16rem]">
            <button type="submit" class="btn btn-primary rounded-2xl" :disabled="busy">上传到附加文件区</button>
          </div>
        </form>
        <form class="bench-card p-5 flex flex-col gap-4" @submit.prevent="createTextFile(true)">
          <p class="text-sm font-black text-stone-800 dark:text-stone-100">在线新建文本附件</p>
          <div class="flex gap-3 flex-wrap items-center">
            <input v-model="assetForm.filename" type="text" class="input input-bordered rounded-2xl font-mono flex-1 min-w-[16rem]" placeholder="例如：notes.md" required>
            <button type="submit" class="btn btn-outline rounded-2xl" :disabled="busy">创建文本附件</button>
          </div>
          <textarea v-model="assetForm.content" class="textarea textarea-bordered rounded-2xl mono-editor mono-editor--compact" placeholder="直接输入文件内容..."></textarea>
        </form>
      </div>

      <div class="flex flex-col gap-4">
        <details v-for="file in workspace.assetFiles" :key="file.id" class="file-row p-5">
          <summary class="cursor-pointer list-none flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div class="font-bold text-stone-800 dark:text-stone-100">{{ file.filename }}</div>
              <div class="text-xs text-stone-400 mt-1">{{ file.fileSizeKb }} KB · {{ file.uploadedAt }}</div>
            </div>
            <div class="flex flex-col gap-1 text-xs min-w-[18rem]">
              <a :href="file.filePath" target="_blank" class="font-mono text-cyan-600 break-all">{{ file.filePath }}</a>
              <code class="whitespace-pre-wrap break-all">{{ file.markdownEmbed }}</code>
            </div>
            <div class="flex gap-2 flex-wrap">
              <a :href="file.filePath" target="_blank" class="btn btn-sm rounded-xl">打开</a>
              <button type="button" class="btn btn-sm btn-error btn-outline rounded-xl" :disabled="busy" @click.stop.prevent="deleteFile(file)">删除</button>
            </div>
          </summary>
          <form v-if="file.isTextEditable" class="mt-5 flex flex-col gap-4" @submit.prevent="updateFile(file)">
            <div class="flex gap-3 flex-wrap items-center">
              <input v-model="file.filename" type="text" class="input input-bordered rounded-2xl font-mono flex-1 min-w-[16rem]" required>
              <button type="submit" class="btn btn-primary rounded-2xl" :disabled="busy">保存这个文本文件</button>
            </div>
            <textarea v-model="file.content" class="textarea textarea-bordered rounded-2xl mono-editor"></textarea>
          </form>
        </details>
        <div v-if="!workspace.assetFiles.length" class="bench-card p-8 text-center text-stone-400">
          当前还没有附加文件。可以上传图片、压缩包，或者新建 `notes.md` 这类文本附件。
        </div>
      </div>
    </section>
  </div>
</template>
