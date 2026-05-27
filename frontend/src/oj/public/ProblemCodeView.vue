<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { requestJson } from './api.js';
import DifficultyBadge from '../DifficultyBadge.vue';
import { useCodeCollaboration } from './useCodeCollaboration.js';

const props = defineProps({
  workspace: { type: Object, required: true },
  currentUser: { type: Object, default: () => ({}) },
  syncSession: { type: Object, default: null },
  syncRequest: { type: Object, default: null },
});

const emit = defineEmits(['back', 'openProblem', 'openSubmissions', 'openSubmission', 'submitted', 'requestSync', 'syncEnded']);

const editorHost = ref(null);
const notice = ref('');
const draftStatus = ref('准备中...');
const syntaxStatus = ref({ text: '正在初始化编辑器...', isError: false });
const activeLanguage = ref('python');
const submitting = ref(false);
const editorReady = ref(false);
const selfTestInput = ref('');
const selfTestOutput = ref('');
const selfTestStatus = ref({ text: '准备自测', tone: 'neutral' });
const selfTesting = ref(false);
const editorFontSize = ref(Number(localStorage.getItem('oj-code-editor-font-size')) || 14);
const editorFontFamily = ref(localStorage.getItem('oj-code-editor-font-family') || '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace');
const collaboration = useCodeCollaboration();

let monacoEditor = null;
let autosaveTimer = 0;
let syntaxTimer = 0;
const startedSessionId = ref('');

const defaultSnippets = {
  python: '',
  cpp: '',
  c: '',
};

const fontOptions = [
  { label: 'JetBrains Mono', value: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Fira Code', value: '"Fira Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Cascadia Code', value: '"Cascadia Code", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' },
  { label: 'Menlo', value: 'Menlo, Monaco, Consolas, ui-monospace, monospace' },
  { label: 'Consolas', value: 'Consolas, "Courier New", ui-monospace, monospace' },
];

const fontSizeOptions = [12, 13, 14, 15, 16, 18, 20, 22];

const latestTask = computed(() => props.workspace.latestTask);
const assignmentId = computed(() => props.workspace.activeAssignment?.id || null);
const currentUser = computed(() => props.workspace.currentUser || props.currentUser || {});
const collaborationConfig = computed(() => props.workspace.collaboration || {});
const showSyncFeature = computed(() => Boolean(collaborationConfig.value.enabled && !props.workspace.contestId));
const syncRequestPending = computed(() => props.syncRequest?.status === 'pending');
const syncStatusTone = computed(() => {
  if (collaboration.status.value === 'active') return 'success';
  if (collaboration.status.value === 'waiting' || collaboration.status.value === 'connecting') return 'warning';
  if (collaboration.status.value === 'left') return 'neutral';
  return 'danger';
});

function storageKey(language) {
  return `oj-code-draft:${props.workspace.problem.slug}:${props.workspace.storageScope}:${language}`;
}

function setSyntaxStatus(text, isError = false) {
  syntaxStatus.value = { text, isError };
}

function setNotice(text) {
  notice.value = text;
  window.setTimeout(() => {
    if (notice.value === text) notice.value = '';
  }, 3200);
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
  const initialCode = props.workspace.initialCode?.[language] || defaultSnippets[language] || '';
  monacoEditor.setValue(saved !== null ? saved : initialCode);
  draftStatus.value = saved !== null ? '已载入草稿' : '新草稿';
  queueSyntaxCheck();
}

function applyLanguage() {
  if (!monacoEditor || !window.monaco) return;
  window.monaco.editor.setModelLanguage(monacoEditor.getModel(), 'python');
  window.monaco.editor.setModelMarkers(monacoEditor.getModel(), 'oj-python', []);
  setSyntaxStatus('Python 语法检查已开启。', false);
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
      message: item.text || 'Python 语法错误',
      startLineNumber: (item.row || 0) + 1,
      startColumn: (item.column || 0) + 1,
      endLineNumber: (item.row || 0) + 1,
      endColumn: Math.max((item.column || 0) + 2, 2),
    }));
    window.monaco.editor.setModelMarkers(monacoEditor.getModel(), 'oj-python', markers);
    setSyntaxStatus(data.message || '语法检查完成。', !data.ok);
  } catch (error) {
    setSyntaxStatus(error.message || '语法检查服务暂不可用，仍可继续编辑和提交。', true);
  }
}

function queueSyntaxCheck() {
  window.clearTimeout(syntaxTimer);
  syntaxTimer = window.setTimeout(checkSyntax, 520);
}

function toggleSync() {
  if (!showSyncFeature.value || !monacoEditor) return;
  if (collaboration.enabled.value) {
    collaboration.stopSync({ nextMessage: '同步已断开。' });
    startedSessionId.value = '';
    emit('syncEnded');
    return;
  }
  if (syncRequestPending.value) return;
  if (props.syncSession) {
    startAcceptedSync(props.syncSession);
    return;
  }
  emit('requestSync', {
    problem: {
      ...props.workspace.problem,
      codeUrl: props.workspace.urls.code,
    },
    codeUrl: props.workspace.urls.code,
    inviteUrl: collaborationConfig.value.inviteUrl,
    collaborationUrl: collaborationConfig.value.collaborationUrl,
  });
}

function startAcceptedSync(session) {
  if (!session || !monacoEditor || !showSyncFeature.value) return;
  if (startedSessionId.value === session.id && collaboration.enabled.value) return;
  if (collaboration.enabled.value) collaboration.stopSync({ nextMessage: '正在切换同步会话。' });
  startedSessionId.value = session.id;
  const room = collaborationConfig.value.room || `problem-${props.workspace.problem.id}`;
  collaboration.startSync({
    editorView: monacoEditor,
    room: session.room || room,
    user: currentUser.value,
    collaborationUrl: collaborationConfig.value.collaborationUrl,
    serverUrl: collaborationConfig.value.serverUrl,
    seedDocument: session.ownerUserId === currentUser.value.id,
  });
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
    language: 'python',
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
    draftStatus.value = '编辑中...';
    queueAutosave();
    queueSyntaxCheck();
  });

  monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
    submitCode();
  });

  if (props.syncSession) startAcceptedSync(props.syncSession);
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

async function runSelfTest() {
  if (!monacoEditor || selfTesting.value) return;
  const sourceCode = monacoEditor.getValue();
  if (!sourceCode.trim()) {
    setNotice('请先填写代码再自测。');
    return;
  }
  selfTesting.value = true;
  selfTestOutput.value = '';
  selfTestStatus.value = { text: '正在运行...', tone: 'neutral' };
  saveDraft();
  try {
    const data = await requestJson(props.workspace.urls.selfTest, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: activeLanguage.value,
        source_code: sourceCode,
        stdin: selfTestInput.value,
      }),
    });
    selfTestOutput.value = data.stdout || '';
    selfTestStatus.value = {
      text: `${data.statusLabel || '自测完成'}${data.timeMs ? ` · ${data.timeMs} ms` : ''}`,
      tone: data.statusTone || 'neutral',
    };
  } catch (error) {
    selfTestOutput.value = '';
    selfTestStatus.value = { text: error.message || '自测失败', tone: 'danger' };
  } finally {
    selfTesting.value = false;
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
  collaboration.stopSync({ nextMessage: '同步已断开。' });
  if (monacoEditor) {
    monacoEditor.dispose();
    monacoEditor = null;
  }
});

watch(
  () => props.syncSession,
  (session) => {
    if (editorReady.value && session) startAcceptedSync(session);
  },
  { deep: true },
);
</script>

<template>
  <div class="code-workspace">
    <section class="workspace-panel">
      <div class="workspace-header">
        <div class="workspace-tab">
          <i class="fas fa-file-lines" aria-hidden="true"></i>
          <span>题目描述</span>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" class="btn btn-ghost btn-sm rounded-lg" @click="emit('back')">
            <i class="fas fa-arrow-left" aria-hidden="true"></i> 返回题目
          </button>
          <a
            :href="workspace.urls.submissions"
            class="btn btn-ghost btn-sm rounded-lg"
            @click.prevent="emit('openSubmissions', workspace.urls.submissions.replace('/oj/submissions', '/oj/submissions.json'))"
          >
            <i class="fas fa-clock-rotate-left" aria-hidden="true"></i> 提交记录
          </a>
        </div>
      </div>

      <div class="problem-scroll">
        <div class="mb-6">
          <p class="text-xs font-black tracking-[0.32em] uppercase text-cyan-600 mb-2">Problem {{ workspace.problem.code }} · UID {{ workspace.problem.uid }}</p>
          <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ workspace.problem.title }}</h1>
          <div class="flex gap-2 flex-wrap mt-4">
            <DifficultyBadge :difficulty="workspace.problem.difficulty" />
            <span class="badge badge-outline">{{ workspace.problem.timeLimitMs }}ms</span>
            <span class="badge badge-outline">{{ workspace.problem.memoryLimitMb }}MB</span>
            <span v-if="workspace.problem.source" class="badge badge-outline">{{ workspace.problem.source }}</span>
            <span v-if="assignmentId" class="badge badge-outline">作业模式</span>
          </div>
        </div>

        <section class="workspace-prose" v-html="workspace.problem.statementHtml"></section>

        <section v-if="!workspace.problem.statementHasSamplePairs" class="mt-8">
          <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100 mb-4">样例</h2>
          <div class="sample-grid">
            <template v-for="(sample, index) in workspace.problem.sampleCases" :key="index">
              <div class="sample-card">
                <div class="flex items-center justify-between mb-2">
                  <h3 class="font-black text-stone-900 dark:text-stone-100">输入 {{ index + 1 }}</h3>
                  <span class="text-xs text-stone-400">score {{ sample.score }}</span>
                </div>
                <pre class="sample-code">{{ sample.input }}</pre>
              </div>
              <div class="sample-card">
                <h3 class="font-black text-stone-900 dark:text-stone-100 mb-2">输出 {{ index + 1 }}</h3>
                <pre class="sample-code">{{ sample.expectedOutput }}</pre>
              </div>
            </template>
            <div v-if="!workspace.problem.sampleCases.length" class="sample-card text-stone-400 md:col-span-2">这道题暂时没有公开样例。</div>
          </div>
        </section>
      </div>
    </section>

    <section class="workspace-panel editor-shell">
      <div class="workspace-header">
        <div class="workspace-tab">
          <i class="fas fa-code" aria-hidden="true"></i>
          <span>代码</span>
        </div>
        <div class="workspace-actions">
          <a
            v-if="latestTask"
            :href="latestTask.url"
            class="btn btn-ghost btn-sm rounded-lg"
            @click.prevent="emit('openSubmission', latestTask.id, latestTask.url)"
          >
            最近提交 #{{ latestTask.id }}
          </a>
          <button type="button" class="btn btn-ghost btn-sm rounded-lg" @click="saveDraft()" :disabled="!editorReady">
            <i class="fas fa-bookmark" aria-hidden="true"></i> 保存草稿
          </button>
          <button
            v-if="showSyncFeature"
            type="button"
            class="btn btn-ghost btn-sm rounded-lg sync-toggle-button"
            :class="{ 'sync-toggle-button--active': collaboration.enabled.value }"
            :disabled="!editorReady"
            :title="collaboration.enabled.value ? '断开同步' : '开启同步'"
            @click="toggleSync"
          >
            <i class="fas" :class="collaboration.enabled.value ? 'fa-link-slash' : 'fa-bolt'" aria-hidden="true"></i>
            {{ collaboration.enabled.value ? '断开同步' : (syncRequestPending ? '等待确认' : '同步') }}
          </button>
          <button type="button" class="btn btn-sm btn-judge px-5" :disabled="submitting || !editorReady" @click="submitCode">
            <i class="fas fa-cloud-arrow-up" aria-hidden="true"></i> {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </div>

      <div class="editor-toolbar">
        <div class="flex items-center gap-3 flex-wrap">
          <span class="editor-language-pill" aria-label="编程语言">
            <i class="fab fa-python" aria-hidden="true"></i>
            Python
          </span>
          <select class="editor-select" :value="editorFontFamily" aria-label="选择编辑器字体" @change="changeFontFamily">
            <option v-for="font in fontOptions" :key="font.value" :value="font.value">{{ font.label }}</option>
          </select>
          <select class="editor-select editor-select--compact" :value="editorFontSize" aria-label="选择编辑器字号" @change="changeFontSize">
            <option v-for="size in fontSizeOptions" :key="size" :value="size">{{ size }}px</option>
          </select>
          <span class="text-sm text-stone-500 dark:text-stone-400">
            <i class="fas fa-lock" aria-hidden="true"></i>
            使用全部测试点评测
          </span>
        </div>
        <div class="editor-status-strip">
          <span v-if="syncRequestPending && !collaboration.enabled.value" class="sync-status-chip sync-status-chip--warning">
            <i class="fas fa-paper-plane" aria-hidden="true"></i>
            已发送同步邀请
          </span>
          <span v-else-if="collaboration.enabled.value || ['left', 'error'].includes(collaboration.status.value)" class="sync-status-chip" :class="`sync-status-chip--${syncStatusTone}`">
            <i class="fas" :class="collaboration.active.value ? 'fa-link' : 'fa-circle-info'" aria-hidden="true"></i>
            {{ collaboration.message.value }}
          </span>
          <span class="text-xs text-stone-400">{{ draftStatus }}</span>
        </div>
      </div>

      <div v-if="notice" class="px-4 pt-3">
        <div class="oj-vue-alert oj-vue-alert--error">{{ notice }}</div>
      </div>

      <div class="editor-body">
        <div class="monaco-editor-frame">
          <div ref="editorHost" class="monaco-editor-host"></div>
        </div>
        <div class="editor-diagnostics">
          <div class="diagnostic-line" :class="{ error: syntaxStatus.isError }">
            <i class="fas" :class="syntaxStatus.isError ? 'fa-circle-exclamation' : 'fa-circle-info'" aria-hidden="true"></i>
            <span>{{ syntaxStatus.text }}</span>
          </div>
        </div>
        <section class="self-test-panel">
          <div class="self-test-header">
            <div class="workspace-tab self-test-tab">
              <i class="fas fa-vial" aria-hidden="true"></i>
              <span>自测</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="status-chip" :class="`status-chip--${selfTestStatus.tone}`">{{ selfTestStatus.text }}</span>
              <button type="button" class="btn btn-sm btn-outline rounded-lg" :disabled="selfTesting || !editorReady" @click="runSelfTest">
                <i class="fas fa-play" aria-hidden="true"></i> {{ selfTesting ? '运行中' : '运行' }}
              </button>
            </div>
          </div>
          <div class="self-test-grid">
            <label class="self-test-field">
              <span>输入</span>
              <textarea v-model="selfTestInput" spellcheck="false" placeholder="在这里输入自测数据"></textarea>
            </label>
            <label class="self-test-field">
              <span>输出</span>
              <textarea :value="selfTestOutput" spellcheck="false" readonly placeholder="运行后显示标准输出"></textarea>
            </label>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>
