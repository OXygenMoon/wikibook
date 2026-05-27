import { computed, ref } from 'vue';
import { resolveCollaborationUrl } from './syncUrls.js';

const MAX_ROOM_USERS = 2;
const BINDING_ORIGIN = 'oj-code-collaboration';

function userColor(userId) {
  const palette = ['#0891b2', '#16a34a', '#dc2626', '#7c3aed', '#ea580c', '#2563eb'];
  const numericId = Number(userId) || 0;
  return palette[Math.abs(numericId) % palette.length];
}

function getAwarenessUsers(awareness) {
  return Array.from(awareness.getStates().entries())
    .map(([clientId, state]) => ({ clientId, ...(state.user || {}) }))
    .filter((user) => user.id || user.name);
}

function applyTextToEditor(editor, text) {
  const model = editor.getModel();
  const position = editor.getPosition();
  const scrollTop = editor.getScrollTop();
  editor.setValue(text);
  if (model && position) {
    const lineNumber = Math.min(position.lineNumber, model.getLineCount());
    const column = Math.min(position.column, model.getLineMaxColumn(lineNumber));
    editor.setPosition({ lineNumber, column });
  }
  editor.setScrollTop(scrollTop);
}

function sanitizeCursorKey(value) {
  return String(value || 'remote')
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, '-');
}

function hexToRgba(hex, alpha) {
  const normalized = String(hex || '#2563eb').replace('#', '');
  const source = normalized.length === 3
    ? normalized.split('').map((part) => `${part}${part}`).join('')
    : normalized.padEnd(6, '0').slice(0, 6);
  const numeric = Number.parseInt(source, 16);
  const red = (numeric >> 16) & 255;
  const green = (numeric >> 8) & 255;
  const blue = numeric & 255;
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

export function useCodeCollaboration() {
  const enabled = ref(false);
  const active = ref(false);
  const status = ref('idle');
  const message = ref('未开启同步');
  const otherUser = ref(null);
  const lastLeftUser = ref(null);
  const hadConnection = ref(false);
  const error = ref('');

  let Y = null;
  let WebsocketProvider = null;
  let ydoc = null;
  let ytext = null;
  let provider = null;
  let editor = null;
  let localUser = null;
  let savedContent = '';
  let shouldSeedDocument = false;
  let didInitialSync = false;
  let initialDocumentResolved = false;
  let ownerSnapshotApplied = false;
  let applyingRemote = false;
  let editorDisposable = null;
  let cursorSelectionDisposable = null;
  let cursorFocusDisposable = null;
  let cursorBlurDisposable = null;
  let textObserver = null;
  let awarenessChangeHandler = null;
  let syncHandler = null;
  let statusHandler = null;
  let remoteSelectionDecorationIds = [];
  let remoteCursorWidgets = new Map();
  const knownUsers = new Map();

  const isConnected = computed(() => active.value && Boolean(otherUser.value));

  function resetState(nextMessage = '未开启同步', { keepLastLeftUser = false } = {}) {
    enabled.value = false;
    active.value = false;
    status.value = 'idle';
    message.value = nextMessage;
    otherUser.value = null;
    error.value = '';
    if (!keepLastLeftUser) lastLeftUser.value = null;
    knownUsers.clear();
  }

  function setWaiting(nextMessage = null) {
    active.value = false;
    otherUser.value = null;
    status.value = 'waiting';
    message.value = nextMessage || (localUser?.isSuperAdmin ? '等待学生加入同步' : '等待超管加入同步');
  }

  function failSync(nextError) {
    stopSync({ nextMessage: nextError, rememberLeftUser: false });
    error.value = nextError;
    status.value = 'error';
    message.value = nextError;
  }

  function ensureRemoteSelectionStyle(key, color) {
    if (typeof document === 'undefined') return `oj-remote-selection-${key}`;
    const className = `oj-remote-selection-${key}`;
    const styleId = `oj-remote-selection-style-${key}`;
    if (document.getElementById(styleId)) return className;
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `.${className}{background:${hexToRgba(color, 0.18)};border-bottom:1px solid ${hexToRgba(color, 0.45)};}`;
    document.head.appendChild(style);
    return className;
  }

  function disposeRemoteCursorWidgets() {
    remoteCursorWidgets.forEach((widget) => {
      try {
        editor?.removeContentWidget(widget);
      } catch (error) {
        // Ignore widget disposal errors during teardown.
      }
    });
    remoteCursorWidgets = new Map();
    remoteSelectionDecorationIds = [];
  }

  function replaceSharedText(nextText, origin = 'oj-code-collaboration-reset') {
    if (!ydoc || !ytext) return;
    const normalizedText = typeof nextText === 'string' ? nextText : '';
    ydoc.transact(() => {
      if (ytext.length > 0) ytext.delete(0, ytext.length);
      if (normalizedText) ytext.insert(0, normalizedText);
    }, origin);
  }

  function removeRemoteCursorWidget(key) {
    const widget = remoteCursorWidgets.get(key);
    if (!widget) return;
    try {
      editor?.removeContentWidget(widget);
    } catch (error) {
      // Ignore widget disposal errors during updates.
    }
    remoteCursorWidgets.delete(key);
  }

  function upsertRemoteCursorWidget(key, remoteUser, position, { isLocal = false } = {}) {
    if (!editor || !window.monaco?.editor) return;
    let widget = remoteCursorWidgets.get(key);
    if (!widget) {
      const domNode = document.createElement('div');
      domNode.className = 'oj-remote-cursor-widget';
      domNode.innerHTML = '<div class="oj-remote-cursor-label"></div><div class="oj-remote-cursor-caret"></div>';
      widget = {
        allowEditorOverflow: true,
        suppressMouseDown: true,
        domNode,
        id: `oj-remote-cursor-${key}`,
        position: null,
        getDomNode() {
          return this.domNode;
        },
        getId() {
          return this.id;
        },
        getPosition() {
          return this.position
            ? {
                position: this.position,
                preference: [window.monaco.editor.ContentWidgetPositionPreference.EXACT],
              }
            : null;
        },
      };
      remoteCursorWidgets.set(key, widget);
      editor.addContentWidget(widget);
    }

    const lineHeight = editor.getOption(window.monaco.editor.EditorOption.lineHeight) || 24;
    const color = remoteUser.color || userColor(remoteUser.id);
    const labelNode = widget.domNode.querySelector('.oj-remote-cursor-label');
    const caretNode = widget.domNode.querySelector('.oj-remote-cursor-caret');
    widget.domNode.classList.toggle('oj-remote-cursor-widget--self', isLocal);
    if (labelNode) {
      labelNode.textContent = remoteUser.name || remoteUser.username || '协作者';
      labelNode.style.background = color;
    }
    if (caretNode) {
      caretNode.style.background = color;
      caretNode.style.height = `${lineHeight}px`;
    }
    widget.domNode.style.setProperty('--oj-remote-cursor-height', `${lineHeight}px`);
    widget.position = position;
    editor.layoutContentWidget(widget);
  }

  function resolveAbsoluteSelection(selection) {
    if (!selection?.anchor || !selection?.head || !Y || !ydoc || !ytext) return null;
    const anchor = Y.createAbsolutePositionFromRelativePosition(selection.anchor, ydoc);
    const head = Y.createAbsolutePositionFromRelativePosition(selection.head, ydoc);
    if (!anchor || !head || anchor.type !== ytext || head.type !== ytext) return null;
    return {
      anchor: anchor.index,
      head: head.index,
    };
  }

  function updateRemoteSelections() {
    if (!editor || !provider || !ydoc || !ytext || !window.monaco?.Range) return;
    const model = editor.getModel();
    if (!model) return;

    const nextDecorations = [];
    const activeKeys = new Set();
    const localSelection = editor.getSelection();
    provider.awareness.getStates().forEach((state, clientId) => {
      const remoteUser = state.user;
      if (!remoteUser || clientId === provider.awareness.clientID || remoteUser.id === localUser?.id) return;
      const resolved = resolveAbsoluteSelection(state.selection);
      if (!resolved) {
        removeRemoteCursorWidget(`client-${sanitizeCursorKey(clientId)}`);
        return;
      }

      const key = `client-${sanitizeCursorKey(clientId)}`;
      const color = remoteUser.color || userColor(remoteUser.id);
      const cursorPosition = model.getPositionAt(resolved.head);
      const start = Math.min(resolved.anchor, resolved.head);
      const end = Math.max(resolved.anchor, resolved.head);

      activeKeys.add(key);
      upsertRemoteCursorWidget(key, remoteUser, cursorPosition);
      if (start !== end) {
        nextDecorations.push({
          range: new window.monaco.Range(
            model.getPositionAt(start).lineNumber,
            model.getPositionAt(start).column,
            model.getPositionAt(end).lineNumber,
            model.getPositionAt(end).column,
          ),
          options: {
            className: ensureRemoteSelectionStyle(key, color),
          },
        });
      }
    });

    if (localUser && localSelection) {
      const localKey = 'client-self';
      activeKeys.add(localKey);
      upsertRemoteCursorWidget(
        localKey,
        localUser,
        {
          lineNumber: localSelection.positionLineNumber,
          column: localSelection.positionColumn,
        },
        { isLocal: true },
      );
    }

    Array.from(remoteCursorWidgets.keys()).forEach((key) => {
      if (!activeKeys.has(key)) removeRemoteCursorWidget(key);
    });
    remoteSelectionDecorationIds = editor.deltaDecorations(remoteSelectionDecorationIds, nextDecorations);
  }

  function updateLocalSelectionAwareness() {
    if (!editor || !provider || !ytext || !Y) return;
    const model = editor.getModel();
    const selection = editor.getSelection();
    if (!model || !selection) return;

    const anchorOffset = model.getOffsetAt({
      lineNumber: selection.selectionStartLineNumber,
      column: selection.selectionStartColumn,
    });
    const headOffset = model.getOffsetAt({
      lineNumber: selection.positionLineNumber,
      column: selection.positionColumn,
    });

    provider.awareness.setLocalStateField('selection', {
      anchor: Y.createRelativePositionFromTypeIndex(ytext, anchorOffset),
      head: Y.createRelativePositionFromTypeIndex(ytext, headOffset),
    });
  }

  function setLocalDocumentReady(ready) {
    if (!provider) return;
    provider.awareness.setLocalStateField('sync', {
      documentReady: Boolean(ready),
    });
  }

  function hasRemoteDocumentReady() {
    if (!provider) return false;
    return Array.from(provider.awareness.getStates().entries()).some(([clientId, state]) => {
      if (clientId === provider.awareness.clientID) return false;
      if (state.user?.id === localUser?.id) return false;
      return Boolean(state.sync?.documentReady);
    });
  }

  function bindEditorToText() {
    if (!editor || !ytext || editorDisposable || textObserver) return;

    textObserver = (event) => {
      if (event.transaction.origin === BINDING_ORIGIN || !editor) return;
      applyingRemote = true;
      try {
        applyTextToEditor(editor, ytext.toString());
      } finally {
        applyingRemote = false;
      }
      updateRemoteSelections();
    };
    ytext.observe(textObserver);

    editorDisposable = editor.onDidChangeModelContent((event) => {
      if (applyingRemote || !ytext || !ydoc) return;
      if (!shouldSeedDocument && !initialDocumentResolved) return;
      const changes = [...event.changes].sort((a, b) => b.rangeOffset - a.rangeOffset);
      ydoc.transact(() => {
        changes.forEach((change) => {
          if (change.rangeLength > 0) ytext.delete(change.rangeOffset, change.rangeLength);
          if (change.text) ytext.insert(change.rangeOffset, change.text);
        });
      }, BINDING_ORIGIN);
      updateLocalSelectionAwareness();
      updateRemoteSelections();
    });

    cursorSelectionDisposable = editor.onDidChangeCursorSelection(() => {
      updateLocalSelectionAwareness();
      updateRemoteSelections();
    });
    cursorFocusDisposable = editor.onDidFocusEditorText(() => {
      updateLocalSelectionAwareness();
      updateRemoteSelections();
    });
    cursorBlurDisposable = editor.onDidBlurEditorText(() => {
      updateLocalSelectionAwareness();
      updateRemoteSelections();
    });
  }

  function seedOrHydrateDocument() {
    if (!editor || !ytext || !ydoc || !didInitialSync || initialDocumentResolved) return;
    if (shouldSeedDocument) {
      const authoritativeContent = editor.getValue();
      savedContent = authoritativeContent;
      if (!ownerSnapshotApplied) {
        replaceSharedText(authoritativeContent, 'oj-code-collaboration-student-seed');
        ownerSnapshotApplied = true;
      }
      initialDocumentResolved = true;
      setLocalDocumentReady(true);
      applyingRemote = true;
      try {
        applyTextToEditor(editor, authoritativeContent);
      } finally {
        applyingRemote = false;
      }
      updateLocalSelectionAwareness();
      updateRemoteSelections();
      return;
    }
    if (!hasRemoteDocumentReady()) return;
    initialDocumentResolved = true;
    applyingRemote = true;
    try {
      applyTextToEditor(editor, ytext.toString());
    } finally {
      applyingRemote = false;
    }
    updateLocalSelectionAwareness();
    updateRemoteSelections();
  }

  function activateIfReady(users) {
    const adminCount = users.filter((user) => user.isSuperAdmin).length;
    const studentCount = users.length - adminCount;

    if (users.length > MAX_ROOM_USERS) {
      failSync('房间人数超过 2 人上限，已断开同步。');
      return;
    }
    if (users.length === MAX_ROOM_USERS && (adminCount !== 1 || studentCount !== 1)) {
      failSync('协同编辑需要且仅需要 1 名超管和 1 名学生。');
      return;
    }
    if (users.length < MAX_ROOM_USERS) {
      setWaiting();
      return;
    }

    const remoteUser = users.find((user) => user.id !== localUser.id) || null;
    otherUser.value = remoteUser;
    lastLeftUser.value = null;
    hadConnection.value = true;
    active.value = true;
    status.value = 'active';
    message.value = remoteUser ? `与 ${remoteUser.name} 同步中` : '同步中';
  }

  function handleAwarenessChange(changes) {
    if (!provider) return;
    const users = getAwarenessUsers(provider.awareness);
    users.forEach((user) => knownUsers.set(user.clientId, user));

    const removedSuperAdmin = (changes?.removed || [])
      .map((clientId) => knownUsers.get(clientId))
      .find((user) => user?.isSuperAdmin);
    if (removedSuperAdmin && !localUser?.isSuperAdmin && hadConnection.value) {
      lastLeftUser.value = removedSuperAdmin;
      stopSync({ nextMessage: `${removedSuperAdmin.name} 已离开，同步已断开。`, rememberLeftUser: true });
      return;
    }

    activateIfReady(users);
    if (!initialDocumentResolved && didInitialSync) seedOrHydrateDocument();
    updateRemoteSelections();
  }

  async function startSync({ editorView, room, user, collaborationUrl, serverUrl, seedDocument = false }) {
    if (enabled.value || !editorView) return;
    editor = editorView;
    localUser = {
      id: user.id,
      name: user.name || user.username || '匿名用户',
      username: user.username || '',
      isSuperAdmin: Boolean(user.isSuperAdmin || user.isAdmin),
      color: userColor(user.id),
    };
    shouldSeedDocument = Boolean(seedDocument);
    savedContent = editor.getValue();
    initialDocumentResolved = false;
    ownerSnapshotApplied = false;
    enabled.value = true;
    status.value = 'connecting';
    message.value = '正在连接同步房间...';

    try {
      const [yjsModule, websocketModule] = await Promise.all([
        import('yjs'),
        import('y-websocket'),
      ]);
      Y = yjsModule;
      WebsocketProvider = websocketModule.WebsocketProvider;

      ydoc = new Y.Doc();
      ytext = ydoc.getText('monaco');
      if (shouldSeedDocument && savedContent && ytext.length === 0) {
        ydoc.transact(() => {
          ytext.insert(0, savedContent);
        }, 'oj-code-collaboration-seed-initial');
      }
      bindEditorToText();

      provider = new WebsocketProvider(
        resolveCollaborationUrl(collaborationUrl, serverUrl),
        room,
        ydoc,
        { connect: true },
      );
      provider.awareness.setLocalStateField('user', localUser);
      setLocalDocumentReady(false);

      syncHandler = (isSynced) => {
        didInitialSync = Boolean(isSynced);
        if (didInitialSync) seedOrHydrateDocument();
      };
      statusHandler = (event) => {
        if (!enabled.value) return;
        if (event.status === 'connected') {
          message.value = '同步服务已连接，正在等待房间就绪...';
          activateIfReady(getAwarenessUsers(provider.awareness));
          return;
        }
        if (event.status === 'connecting') {
          status.value = 'connecting';
          message.value = '正在连接同步服务...';
          return;
        }
        if (event.status === 'disconnected') {
          status.value = 'connecting';
          active.value = false;
          otherUser.value = null;
          message.value = '同步服务已断开，正在重连...';
        }
      };
      awarenessChangeHandler = handleAwarenessChange;

      provider.on('sync', syncHandler);
      provider.on('status', statusHandler);
      provider.awareness.on('change', awarenessChangeHandler);

      setWaiting('正在加入同步房间...');
      activateIfReady(getAwarenessUsers(provider.awareness));
      updateLocalSelectionAwareness();
      updateRemoteSelections();
    } catch (syncError) {
      failSync(syncError?.message || '同步模块加载失败，请稍后重试。');
    }
  }

  function stopSync({ nextMessage = '同步已断开。', rememberLeftUser = false } = {}) {
    if (editorDisposable) {
      editorDisposable.dispose();
      editorDisposable = null;
    }
    if (cursorSelectionDisposable) {
      cursorSelectionDisposable.dispose();
      cursorSelectionDisposable = null;
    }
    if (cursorFocusDisposable) {
      cursorFocusDisposable.dispose();
      cursorFocusDisposable = null;
    }
    if (cursorBlurDisposable) {
      cursorBlurDisposable.dispose();
      cursorBlurDisposable = null;
    }
    if (ytext && textObserver) {
      ytext.unobserve(textObserver);
      textObserver = null;
    }
    if (provider) {
      if (awarenessChangeHandler) provider.awareness.off('change', awarenessChangeHandler);
      if (syncHandler) provider.off('sync', syncHandler);
      if (statusHandler) provider.off('status', statusHandler);
      provider.disconnect();
      provider.destroy();
      provider = null;
    }
    disposeRemoteCursorWidgets();
    if (ydoc) {
      ydoc.destroy();
      ydoc = null;
    }
    ytext = null;
    editor = null;
    localUser = null;
    savedContent = '';
    shouldSeedDocument = false;
    didInitialSync = false;
    initialDocumentResolved = false;
    ownerSnapshotApplied = false;
    syncHandler = null;
    statusHandler = null;
    awarenessChangeHandler = null;
    if (!rememberLeftUser) lastLeftUser.value = null;
    resetState(nextMessage, { keepLastLeftUser: rememberLeftUser });
    if (rememberLeftUser) {
      status.value = 'left';
      message.value = nextMessage;
    }
  }

  return {
    enabled,
    active,
    status,
    message,
    otherUser,
    lastLeftUser,
    hadConnection,
    isConnected,
    error,
    startSync,
    stopSync,
  };
}
