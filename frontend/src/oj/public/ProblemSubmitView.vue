<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { requestJson } from './api.js';
import DifficultyBadge from '../DifficultyBadge.vue';

const props = defineProps({
  workspace: { type: Object, required: true },
});

const emit = defineEmits(['back', 'open-problem', 'open-code', 'open-submissions', 'open-submission', 'submitted']);

const editorHost = ref(null);
const activeLanguage = ref(props.workspace.defaultLanguage || props.workspace.problem.allowedLanguages[0] || 'python');
const notice = ref('');
const syntaxStatus = ref({ text: '正在初始化编辑器...', isError: false });
const draftStatus = ref('准备中...');
const submitting = ref(false);
const editorReady = ref(false);
const clearConfirming = ref(false);
const editorFontSize = ref(Number(localStorage.getItem('oj-code-editor-font-size')) || 14);
const editorFontFamily = ref(localStorage.getItem('oj-code-editor-font-family') || '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace');

let monacoEditor = null;
let autosaveTimer = 0;
let syntaxTimer = 0;
let clearConfirmTimer = 0;

const fontOptions = [
  { label: 'JetBrains Mono', value: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Fira Code', value: '"Fira Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Cascadia Code', value: '"Cascadia Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Menlo', value: 'Menlo, Monaco, Consolas, ui-monospace, monospace' },
  { label: 'Consolas', value: 'Consolas, "Courier New", ui-monospace, monospace' },
];

const fontSizeOptions = [12, 13, 14, 15, 16, 18, 20, 22];
const languageIcon = computed(() => (activeLanguage.value === 'python' ? 'fab fa-python' : 'fas fa-code'));
const languageLabel = computed(() => activeLanguage.value.toUpperCase());

function storageKey(language) {
  return `oj-submit-draft:${props.workspace.problem.slug}:${props.workspace.storageScope}:${language}`;
}

function setNotice(text) {
  notice.value = text;
  window.setTimeout(() => {
    if (notice.value === text) notice.value = '';
  }, 3200);
}

function resetClearConfirm() {
  window.clearTimeout(clearConfirmTimer);
  clearConfirming.value = false;
}

function setSyntaxStatus(text, isError = false) {
  syntaxStatus.value = { text, isError };
}

function getEditorLanguage(language) {
  if (language === 'python') return 'python';
  if (language === 'cpp') return 'cpp';
  if (language === 'c') return 'c';
  return 'plaintext';
}

function saveDraft(language = activeLanguage.value) {
  if (!monacoEditor) return;
  localStorage.setItem(storageKey(language), monacoEditor.getValue());
  draftStatus.value = `已保存 ${new Date().toLocaleTimeString('zh-CN', { hour12: false })}`;
}

function queueAutosave() {
  window.clearTimeout(autosaveTimer);
  autosaveTimer = window.setTimeout(() => saveDraft(), 550);
}

function loadDraft(language) {
  if (!monacoEditor) return;
  const saved = localStorage.getItem(storageKey(language));
  const initialCode = props.workspace.initialCode?.[language] || '';
  monacoEditor.setValue(saved !== null ? saved : initialCode);
  draftStatus.value = saved !== null ? '已载入草稿' : '新草稿';
  queueSyntaxCheck();
}

function applyLanguage() {
  if (!monacoEditor || !window.monaco) return;
  window.monaco.editor.setModelLanguage(monacoEditor.getModel(), getEditorLanguage(activeLanguage.value));
  window.monaco.editor.setModelMarkers(monacoEditor.getModel(), 'oj-submit', []);
  if (activeLanguage.value === 'python') {
    setSyntaxStatus('Python 语法检查已开启。', false);
  } else {
    setSyntaxStatus('当前仅对 Python 代码提供语法检查。', false);
  }
}

function applyEditorPreferences() {
  if (!monacoEditor) return;
  monacoEditor.updateOptions({
    fontFamily: editorFontFamily.value,
    fontSize: Number(editorFontSize.value) || 14,
    lineHeight: Math.round((Number(editorFontSize.value) || 14) * 1.7),
  });
}

function changeFontFamily(event) {
  editorFontFamily.value = event.target.value;
  localStorage.setItem('oj-code-editor-font-family', editorFontFamily.value);
  applyEditorPreferences();
}

function changeFontSize(event) {
  editorFontSize.value = Number(event.target.value) || 14;
  localStorage.setItem('oj-code-editor-font-size', String(editorFontSize.value));
  applyEditorPreferences();
}

function changeLanguage(event) {
  if (!monacoEditor) return;
  resetClearConfirm();
  saveDraft(activeLanguage.value);
  activeLanguage.value = event.target.value;
  applyLanguage();
  loadDraft(activeLanguage.value);
}

function requestClearEditor() {
  if (!monacoEditor || !editorReady.value) return;
  if (!monacoEditor.getValue().length) {
    setNotice('编辑器已经是空的。');
    return;
  }
  clearConfirming.value = true;
  window.clearTimeout(clearConfirmTimer);
  clearConfirmTimer = window.setTimeout(() => {
    clearConfirming.value = false;
  }, 5000);
}

function confirmClearEditor() {
  if (!monacoEditor || !editorReady.value) return;
  window.clearTimeout(clearConfirmTimer);
  clearConfirming.value = false;
  monacoEditor.setValue('');
  localStorage.setItem(storageKey(activeLanguage.value), '');
  draftStatus.value = '已清空草稿';
  setSyntaxStatus(activeLanguage.value === 'python' ? 'Python 语法检查已开启。' : '当前仅对 Python 代码提供语法检查。', false);
  if (window.monaco) {
    window.monaco.editor.setModelMarkers(monacoEditor.getModel(), 'oj-submit', []);
  }
  monacoEditor.focus();
}

async function checkSyntax() {
  if (!monacoEditor || !window.monaco) return;
  try {
    const data = await requestJson(props.workspace.urls.syntaxCheck, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: activeLanguage.value,
        source_code: monacoEditor.getValue(),
      }),
    });
    const markers = (data.diagnostics || []).map((item) => ({
      severity: item.type === 'error' ? window.monaco.MarkerSeverity.Error : window.monaco.MarkerSeverity.Warning,
      message: item.text || '语法错误',
      startLineNumber: (item.row || 0) + 1,
      startColumn: (item.column || 0) + 1,
      endLineNumber: (item.row || 0) + 1,
      endColumn: Math.max((item.column || 0) + 2, 2),
    }));
    window.monaco.editor.setModelMarkers(monacoEditor.getModel(), 'oj-submit', markers);
    setSyntaxStatus(data.message || '语法检查完成。', !data.ok);
  } catch (error) {
    setSyntaxStatus(error.message || '语法检查服务暂不可用，仍可继续编辑和提交。', true);
  }
}

function queueSyntaxCheck() {
  window.clearTimeout(syntaxTimer);
  syntaxTimer = window.setTimeout(checkSyntax, 520);
}

async function ensureMonaco() {
  if (window.monaco?.editor) return window.monaco;
  if (window.__ojMonacoLoaderPromise) return window.__ojMonacoLoaderPromise;

  window.__ojMonacoLoaderPromise = new Promise((resolve, reject) => {
    const done = () => {
      window.require.config({ paths: { vs: '/static/js/vendor/monaco/vs' } });
      window.require(['vs/editor/editor.main'], () => resolve(window.monaco), reject);
    };

    const existing = document.querySelector('script[data-oj-monaco-loader="true"]');
    if (existing) {
      if (window.require) done();
      else existing.addEventListener('load', done, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = '/static/js/vendor/monaco/vs/loader.js';
    script.async = true;
    script.dataset.ojMonacoLoader = 'true';
    script.addEventListener('load', done, { once: true });
    script.addEventListener('error', () => reject(new Error('Monaco 编辑器资源加载失败。')), { once: true });
    document.head.appendChild(script);
  });

  return window.__ojMonacoLoaderPromise;
}

async function initializeEditor() {
  const monaco = await ensureMonaco();
  const theme = document.documentElement.classList.contains('dark') ? 'vs-dark' : 'vs';
  monacoEditor = monaco.editor.create(editorHost.value, {
    value: '',
    language: getEditorLanguage(activeLanguage.value),
    theme,
    automaticLayout: true,
    minimap: { enabled: false },
    fontFamily: editorFontFamily.value,
    fontSize: editorFontSize.value,
    lineHeight: Math.round(editorFontSize.value * 1.7),
    padding: { top: 12, bottom: 12 },
    scrollBeyondLastLine: false,
    smoothScrolling: true,
  });

  editorReady.value = true;
  applyLanguage();
  loadDraft(activeLanguage.value);

  monacoEditor.onDidChangeModelContent(() => {
    resetClearConfirm();
    draftStatus.value = '编辑中...';
    queueAutosave();
    queueSyntaxCheck();
  });

  monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
    submitCode();
  });
}

async function submitCode() {
  if (!monacoEditor || submitting.value) return;
  const sourceCode = monacoEditor.getValue();
  if (!sourceCode.trim()) {
    setNotice('请先填写代码再提交。');
    return;
  }
  submitting.value = true;
  saveDraft();
  try {
    const data = await requestJson(props.workspace.urls.submit, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: activeLanguage.value,
        source_code: sourceCode,
      }),
    });
    emit('submitted', data.submissionDetail, data.redirectUrl, data.message);
  } catch (error) {
    setNotice(error.message || '提交失败，请稍后重试。');
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  try {
    await initializeEditor();
  } catch (error) {
    setNotice(error.message || '编辑器初始化失败。');
    setSyntaxStatus('编辑器初始化失败，请刷新重试。', true);
  }
});

onUnmounted(() => {
  window.clearTimeout(autosaveTimer);
  window.clearTimeout(syntaxTimer);
  window.clearTimeout(clearConfirmTimer);
  if (monacoEditor) {
    monacoEditor.dispose();
    monacoEditor = null;
  }
});
</script>

<template>
  <div class="submit-workspace">
    <main class="oj-panel submit-workspace__main">
      <div class="submit-workspace__hero">
        <div>
          <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Submit {{ workspace.problem.code }} · UID {{ workspace.problem.uid }}</p>
          <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ workspace.problem.title }}</h1>
          <p class="text-stone-500 dark:text-stone-400 mt-3">这里是单独的提交通道。编辑器会尽量铺满可用空间，并在你编写 Python 时实时提示语法问题。</p>
        </div>
        <div class="submit-workspace__hero-actions">
          <button type="button" class="btn btn-ghost rounded-lg" @click="emit('back')">
            <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回题目
          </button>
          <a :href="workspace.urls.code" class="btn btn-outline rounded-lg" @click.prevent="emit('open-code', workspace.problem.slug, workspace.urls.code)">
            <i class="fas fa-code" aria-hidden="true"></i> 去在线编程
          </a>
          <button type="button" class="btn btn-primary rounded-lg px-8" :disabled="submitting || !editorReady" @click="submitCode">
            <i class="fas fa-paper-plane" aria-hidden="true"></i> {{ submitting ? '提交中...' : '提交并评测' }}
          </button>
        </div>
      </div>

      <div v-if="notice" class="px-6 md:px-8 pt-2">
        <div class="oj-vue-alert oj-vue-alert--error">{{ notice }}</div>
      </div>

      <div class="submit-workspace__content">
        <section class="submit-editor-shell">
          <div class="editor-toolbar submit-editor-shell__toolbar">
            <div class="flex items-center gap-3 flex-wrap">
              <span class="editor-language-pill" aria-label="当前语言">
                <i :class="languageIcon" aria-hidden="true"></i>
                {{ languageLabel }}
              </span>
              <select class="editor-select" :value="activeLanguage" aria-label="选择语言" @change="changeLanguage">
                <option v-for="language in workspace.problem.allowedLanguages" :key="language" :value="language">{{ language }}</option>
              </select>
              <select class="editor-select" :value="editorFontFamily" aria-label="选择编辑器字体" @change="changeFontFamily">
                <option v-for="font in fontOptions" :key="font.value" :value="font.value">{{ font.label }}</option>
              </select>
              <select class="editor-select editor-select--compact" :value="editorFontSize" aria-label="选择编辑器字号" @change="changeFontSize">
                <option v-for="size in fontSizeOptions" :key="size" :value="size">{{ size }}px</option>
              </select>
              <button
                type="button"
                class="btn btn-sm btn-outline rounded-lg submit-clear-button"
                :disabled="!editorReady"
                @click="requestClearEditor"
              >
                <i class="fas fa-eraser" aria-hidden="true"></i>
                清空代码
              </button>
            </div>
            <div class="editor-status-strip">
              <span class="text-xs text-stone-400">{{ draftStatus }}</span>
            </div>
          </div>

          <div v-if="clearConfirming" class="submit-clear-confirm">
            <span>
              <i class="fas fa-triangle-exclamation" aria-hidden="true"></i>
              确认清空当前编辑器内容？
            </span>
            <div class="submit-clear-confirm__actions">
              <button type="button" class="btn btn-xs rounded-lg submit-clear-confirm__confirm" @click="confirmClearEditor">确认清空</button>
              <button type="button" class="btn btn-xs rounded-lg submit-clear-confirm__cancel" @click="resetClearConfirm">取消</button>
            </div>
          </div>

          <div class="submit-editor-shell__body">
            <div class="monaco-editor-frame submit-editor-shell__frame">
              <div ref="editorHost" class="monaco-editor-host"></div>
            </div>
            <div class="editor-diagnostics submit-editor-shell__diagnostics">
              <div class="diagnostic-line" :class="{ error: syntaxStatus.isError }">
                <i class="fas" :class="syntaxStatus.isError ? 'fa-circle-exclamation' : 'fa-circle-info'" aria-hidden="true"></i>
                <span>{{ syntaxStatus.text }}</span>
              </div>
            </div>
          </div>
        </section>

        <aside class="oj-panel submit-sidebar">
          <div class="submit-sidebar__section">
            <h2 class="text-xl font-black text-stone-900 dark:text-stone-100 mb-4">题目信息</h2>
            <div class="flex flex-col gap-3 text-sm">
              <div class="meta-line"><span class="text-stone-500">UID</span><span class="font-mono font-bold">{{ workspace.problem.uid }}</span></div>
              <div class="meta-line"><span class="text-stone-500">编号</span><span class="font-mono font-bold">{{ workspace.problem.code }}</span></div>
              <div class="meta-line"><span class="text-stone-500">难度</span><DifficultyBadge :difficulty="workspace.problem.difficulty" /></div>
              <div class="meta-line"><span class="text-stone-500">时间限制</span><span class="font-bold">{{ workspace.problem.timeLimitMs }} ms</span></div>
              <div class="meta-line"><span class="text-stone-500">内存限制</span><span class="font-bold">{{ workspace.problem.memoryLimitMb }} MB</span></div>
              <div class="meta-line"><span class="text-stone-500">测试点</span><span class="font-bold">{{ workspace.problem.testcaseCount }}</span></div>
            </div>
          </div>

          <div class="submit-sidebar__section">
            <div class="rounded-lg bg-cyan-50 dark:bg-cyan-900/20 px-4 py-3 text-sm text-cyan-800 dark:text-cyan-100 leading-6">
              系统会使用当前题目的全部测试点进行评测。公开样例可以帮助你自测，隐藏数据会在后台一起运行。
            </div>
          </div>

          <div class="submit-sidebar__section">
            <div class="flex gap-2 flex-wrap">
              <a
                v-if="workspace.latestTask"
                :href="workspace.latestTask.url"
                class="btn btn-ghost rounded-lg"
                @click.prevent="emit('open-submission', workspace.latestTask.id, workspace.latestTask.url)"
              >
                最近提交 #{{ workspace.latestTask.id }}
              </a>
              <a
                :href="workspace.urls.submissions"
                class="btn btn-ghost rounded-lg"
                @click.prevent="emit('open-submissions', workspace.urls.submissions.replace('/oj/submissions', '/oj/submissions.json'))"
              >
                <i class="fas fa-clock-rotate-left" aria-hidden="true"></i> 提交记录
              </a>
            </div>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>
