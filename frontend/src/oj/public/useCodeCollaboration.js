import { computed, ref } from 'vue';
import { resolveCollaborationUrl } from './syncUrls.js';

const MAX_ROOM_USERS = 2;
const BINDING_ORIGIN = 'oj-code-collaboration';
const DRAWINGS_ORIGIN = 'oj-screen-drawing';

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

function escapeCssIdent(value) {
  if (typeof CSS !== 'undefined' && CSS.escape) return CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
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
  const drawingMode = ref(false);
  const drawCount = ref(0);

  let Y = null;
  let WebsocketProvider = null;
  let ydoc = null;
  let ytext = null;
  let ydrawings = null;
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
  let drawingObserver = null;
  let awarenessChangeHandler = null;
  let syncHandler = null;
  let statusHandler = null;
  let editorScrollDisposable = null;
  let remoteSelectionDecorationIds = [];
  let remoteCursorWidgets = new Map();
  let statementViewport = null;
  let statementScrollRoot = null;
  let statementOverlay = null;
  let statementContent = null;
  let statementPointerMoveHandler = null;
  let statementPointerLeaveHandler = null;
  let statementSelectionChangeHandler = null;
  let statementScrollHandler = null;
  let viewportPointerMoveHandler = null;
  let viewportPointerLeaveHandler = null;
  let globalPointerLayer = null;
  let drawingLayer = null;
  let drawingSvg = null;
  let drawingPointerDownHandler = null;
  let drawingPointerMoveHandler = null;
  let drawingPointerUpHandler = null;
  let clickHandler = null;
  let resizeHandler = null;
  let windowScrollHandler = null;
  let remoteStatementPointerNodes = new Map();
  let remoteStatementSelectionNodes = new Map();
  let localDrawings = [];
  let activeStroke = null;
  let applyingRemoteScroll = false;
  let scrollFrame = 0;
  let selectionFrame = 0;
  const seenRippleIds = new Set();
  const appliedScrollIds = new Set();
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

  function clearNodeMap(map) {
    map.forEach((node) => {
      try {
        node.remove();
      } catch (error) {
        // Ignore DOM cleanup errors during teardown.
      }
    });
    map.clear();
  }

  function disposeStatementOverlay() {
    if (selectionFrame) {
      window.cancelAnimationFrame(selectionFrame);
      selectionFrame = 0;
    }
    clearNodeMap(remoteStatementPointerNodes);
    clearNodeMap(remoteStatementSelectionNodes);
    if (viewportPointerMoveHandler) {
      window.removeEventListener('pointermove', viewportPointerMoveHandler);
      window.removeEventListener('pointerleave', viewportPointerLeaveHandler);
      document.removeEventListener('mouseleave', viewportPointerLeaveHandler);
    }
    if (statementPointerMoveHandler && statementViewport) {
      statementViewport.removeEventListener('pointermove', statementPointerMoveHandler);
      statementViewport.removeEventListener('pointerleave', statementPointerLeaveHandler);
    }
    if (statementSelectionChangeHandler) {
      document.removeEventListener('selectionchange', statementSelectionChangeHandler);
    }
    if (statementScrollHandler) {
      statementScrollRoot?.removeEventListener('scroll', statementScrollHandler);
      window.removeEventListener('scroll', statementScrollHandler, true);
      window.removeEventListener('resize', statementScrollHandler);
    }
    unbindDrawingLayer();
    statementViewport = null;
    statementScrollRoot = null;
    statementOverlay = null;
    statementContent = null;
    statementPointerMoveHandler = null;
    statementPointerLeaveHandler = null;
    statementSelectionChangeHandler = null;
    statementScrollHandler = null;
    viewportPointerMoveHandler = null;
    viewportPointerLeaveHandler = null;
  }

  function setLocalStatementAwareness(nextState = null) {
    if (!provider) return;
    provider.awareness.setLocalStateField('statement', nextState);
  }

  function mergeLocalStatementAwareness(patch = {}) {
    if (!provider) return;
    const current = provider.awareness.getLocalState()?.statement || {};
    setLocalStatementAwareness({
      ...current,
      ...patch,
    });
  }

  function syncSurfaceRect() {
    const root = document.querySelector('.code-workspace') || document.getElementById('oj-public-shell-app') || document.body;
    return root.getBoundingClientRect();
  }

  function viewportToSurfacePoint(clientX, clientY) {
    const rect = syncSurfaceRect();
    const width = Math.max(rect.width, 1);
    const height = Math.max(rect.height, 1);
    return {
      x: Math.min(Math.max((clientX - rect.left) / width, 0), 1),
      y: Math.min(Math.max((clientY - rect.top) / height, 0), 1),
    };
  }

  function surfaceToViewportPoint(point) {
    if (!point || !Number.isFinite(point.x) || !Number.isFinite(point.y)) return null;
    const rect = syncSurfaceRect();
    return {
      left: Math.round(rect.left + point.x * rect.width),
      top: Math.round(rect.top + point.y * rect.height),
    };
  }

  function createEventId(prefix = 'event') {
    const idPart = localUser?.id || provider?.awareness?.clientID || 'local';
    return `${prefix}-${idPart}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function scrollRatio(element, axis) {
    if (!element) return 0;
    const max = axis === 'x'
      ? Math.max(element.scrollWidth - element.clientWidth, 0)
      : Math.max(element.scrollHeight - element.clientHeight, 0);
    if (max <= 0) return 0;
    return (axis === 'x' ? element.scrollLeft : element.scrollTop) / max;
  }

  function applyScrollRatio(element, ratioX, ratioY) {
    if (!element) return;
    const maxX = Math.max(element.scrollWidth - element.clientWidth, 0);
    const maxY = Math.max(element.scrollHeight - element.clientHeight, 0);
    element.scrollLeft = Math.round(maxX * Math.min(Math.max(ratioX || 0, 0), 1));
    element.scrollTop = Math.round(maxY * Math.min(Math.max(ratioY || 0, 0), 1));
  }

  function publishScrollState(source) {
    if (!provider || applyingRemoteScroll) return;
    const scroll = {
      id: createEventId('scroll'),
      source,
      statement: statementScrollRoot
        ? {
            x: scrollRatio(statementScrollRoot, 'x'),
            y: scrollRatio(statementScrollRoot, 'y'),
          }
        : null,
      editor: editor
        ? {
            y: editor.getScrollTop() / Math.max(editor.getScrollHeight() - editor.getLayoutInfo().height, 1),
            x: editor.getScrollLeft() / Math.max(editor.getScrollWidth() - editor.getLayoutInfo().width, 1),
          }
        : null,
      window: {
        x: scrollRatio(document.scrollingElement || document.documentElement, 'x'),
        y: scrollRatio(document.scrollingElement || document.documentElement, 'y'),
      },
    };
    mergeLocalStatementAwareness({ scroll });
  }

  function queuePublishScrollState(source) {
    if (scrollFrame) return;
    scrollFrame = window.requestAnimationFrame(() => {
      scrollFrame = 0;
      publishScrollState(source);
    });
  }

  function applyRemoteScroll(scroll) {
    if (!scroll?.id || appliedScrollIds.has(scroll.id) || !active.value) return;
    appliedScrollIds.add(scroll.id);
    applyingRemoteScroll = true;
    try {
      if (scroll.statement && statementScrollRoot) {
        applyScrollRatio(statementScrollRoot, scroll.statement.x, scroll.statement.y);
      }
      if (scroll.editor && editor) {
        const layout = editor.getLayoutInfo();
        const maxTop = Math.max(editor.getScrollHeight() - layout.height, 0);
        const maxLeft = Math.max(editor.getScrollWidth() - layout.width, 0);
        editor.setScrollTop(Math.round(maxTop * Math.min(Math.max(scroll.editor.y || 0, 0), 1)));
        editor.setScrollLeft(Math.round(maxLeft * Math.min(Math.max(scroll.editor.x || 0, 0), 1)));
      }
      if (scroll.window) {
        const scrollingElement = document.scrollingElement || document.documentElement;
        applyScrollRatio(scrollingElement, scroll.window.x, scroll.window.y);
      }
    } finally {
      window.setTimeout(() => {
        applyingRemoteScroll = false;
      }, 80);
    }
  }

  function publishClickRipple(event) {
    if (!provider || drawingMode.value) return;
    const point = viewportToSurfacePoint(event.clientX, event.clientY);
    const ripple = {
      id: createEventId('click'),
      point,
    };
    mergeLocalStatementAwareness({ ripple });
    renderClickRipple(point, localUser);
  }

  function renderClickRipple(point, user = null) {
    const position = surfaceToViewportPoint(point);
    if (!position) return;
    const layer = ensureGlobalPointerLayer();
    if (!layer) return;
    const node = document.createElement('div');
    node.className = 'oj-sync-click-ripple';
    node.style.left = `${position.left}px`;
    node.style.top = `${position.top}px`;
    node.style.setProperty('--oj-sync-ripple-color', user?.color || userColor(user?.id));
    layer.appendChild(node);
    window.setTimeout(() => node.remove(), 820);
  }

  function ensureDrawingLayer() {
    if (drawingLayer || typeof document === 'undefined') return drawingLayer;
    const layer = document.createElement('div');
    layer.className = 'oj-sync-drawing-layer';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('oj-sync-drawing-svg');
    svg.setAttribute('preserveAspectRatio', 'none');
    layer.appendChild(svg);
    document.body.appendChild(layer);
    drawingLayer = layer;
    drawingSvg = svg;
    layoutDrawingLayer();
    return drawingLayer;
  }

  function layoutDrawingLayer() {
    if (!drawingLayer || !drawingSvg) return;
    const rect = syncSurfaceRect();
    drawingLayer.style.left = `${rect.left}px`;
    drawingLayer.style.top = `${rect.top}px`;
    drawingLayer.style.width = `${rect.width}px`;
    drawingLayer.style.height = `${rect.height}px`;
    drawingSvg.setAttribute('viewBox', '0 0 1 1');
  }

  function renderDrawings() {
    ensureDrawingLayer();
    if (!drawingSvg) return;
    drawingSvg.replaceChildren();
    localDrawings.forEach((stroke) => {
      if (!stroke?.points?.length) return;
      const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline.setAttribute('points', stroke.points.map((point) => `${point.x},${point.y}`).join(' '));
      polyline.setAttribute('fill', 'none');
      polyline.setAttribute('stroke', stroke.color || userColor(stroke.userId));
      polyline.setAttribute('stroke-width', '0.006');
      polyline.setAttribute('stroke-linecap', 'round');
      polyline.setAttribute('stroke-linejoin', 'round');
      drawingSvg.appendChild(polyline);
    });
  }

  function syncDrawingsFromYjs() {
    if (!ydrawings) return;
    localDrawings = ydrawings.toArray();
    drawCount.value = localDrawings.length;
    renderDrawings();
  }

  function appendDrawing(stroke) {
    if (!ydrawings || !stroke?.points?.length) return;
    ydoc.transact(() => {
      ydrawings.push([stroke]);
    }, DRAWINGS_ORIGIN);
    syncDrawingsFromYjs();
  }

  function clearDrawings() {
    if (!ydrawings) {
      localDrawings = [];
      drawCount.value = 0;
      renderDrawings();
      return;
    }
    ydoc.transact(() => {
      if (ydrawings.length > 0) ydrawings.delete(0, ydrawings.length);
    }, DRAWINGS_ORIGIN);
    syncDrawingsFromYjs();
  }

  function setDrawingMode(nextValue) {
    drawingMode.value = Boolean(nextValue);
    if (drawingLayer) drawingLayer.classList.toggle('oj-sync-drawing-layer--active', drawingMode.value);
  }

  function toggleDrawingMode() {
    setDrawingMode(!drawingMode.value);
  }

  function finishActiveStroke() {
    if (!activeStroke) return;
    const stroke = activeStroke;
    activeStroke = null;
    if (stroke.points.length > 1) appendDrawing(stroke);
  }

  function drawingPointFromEvent(event) {
    return viewportToSurfacePoint(event.clientX, event.clientY);
  }

  function handleDrawingPointerDown(event) {
    if (!drawingMode.value || !active.value) return;
    event.preventDefault();
    drawingLayer?.setPointerCapture?.(event.pointerId);
    const point = drawingPointFromEvent(event);
    activeStroke = {
      id: createEventId('draw'),
      userId: localUser?.id,
      color: localUser?.color || userColor(localUser?.id),
      points: [point, { x: Math.min(point.x + 0.001, 1), y: Math.min(point.y + 0.001, 1) }],
    };
    localDrawings = [...(ydrawings ? ydrawings.toArray() : localDrawings), activeStroke];
    drawCount.value = localDrawings.length;
    renderDrawings();
  }

  function handleDrawingPointerMove(event) {
    if (!drawingMode.value || !activeStroke) return;
    event.preventDefault();
    const point = drawingPointFromEvent(event);
    const previous = activeStroke.points[activeStroke.points.length - 1];
    if (previous && Math.abs(previous.x - point.x) < 0.002 && Math.abs(previous.y - point.y) < 0.002) return;
    activeStroke.points.push(point);
    localDrawings = [...(ydrawings ? ydrawings.toArray() : localDrawings), activeStroke];
    drawCount.value = localDrawings.length;
    renderDrawings();
  }

  function handleDrawingPointerUp(event) {
    if (!drawingMode.value || !activeStroke) return;
    event.preventDefault();
    drawingLayer?.releasePointerCapture?.(event.pointerId);
    finishActiveStroke();
  }

  function bindDrawingLayer() {
    const layer = ensureDrawingLayer();
    if (!layer) return;
    drawingPointerDownHandler = handleDrawingPointerDown;
    drawingPointerMoveHandler = handleDrawingPointerMove;
    drawingPointerUpHandler = handleDrawingPointerUp;
    clickHandler = publishClickRipple;
    resizeHandler = () => {
      layoutDrawingLayer();
      updateRemoteStatementPresence();
    };
    windowScrollHandler = () => {
      layoutDrawingLayer();
      queuePublishScrollState('window');
      updateRemoteStatementPresence();
    };

    layer.addEventListener('pointerdown', drawingPointerDownHandler);
    window.addEventListener('pointermove', drawingPointerMoveHandler, { passive: false });
    window.addEventListener('pointerup', drawingPointerUpHandler, { passive: false });
    document.addEventListener('click', clickHandler, true);
    window.addEventListener('resize', resizeHandler, { passive: true });
    window.addEventListener('scroll', windowScrollHandler, true);
  }

  function unbindDrawingLayer() {
    finishActiveStroke();
    if (drawingLayer && drawingPointerDownHandler) {
      drawingLayer.removeEventListener('pointerdown', drawingPointerDownHandler);
    }
    if (drawingPointerMoveHandler) window.removeEventListener('pointermove', drawingPointerMoveHandler);
    if (drawingPointerUpHandler) window.removeEventListener('pointerup', drawingPointerUpHandler);
    if (clickHandler) document.removeEventListener('click', clickHandler, true);
    if (resizeHandler) window.removeEventListener('resize', resizeHandler);
    if (windowScrollHandler) window.removeEventListener('scroll', windowScrollHandler, true);
    drawingPointerDownHandler = null;
    drawingPointerMoveHandler = null;
    drawingPointerUpHandler = null;
    clickHandler = null;
    resizeHandler = null;
    windowScrollHandler = null;
    setDrawingMode(false);
    if (drawingLayer) drawingLayer.classList.remove('oj-sync-drawing-layer--active');
  }

  function scheduleStatementSelectionUpdate() {
    if (selectionFrame) return;
    selectionFrame = window.requestAnimationFrame(() => {
      selectionFrame = 0;
      updateLocalStatementSelectionAwareness();
    });
  }

  function readStatementSelectionRect() {
    if (!statementViewport || !statementContent) return null;
    const selection = window.getSelection?.();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return null;
    const anchorNode = selection.anchorNode;
    const focusNode = selection.focusNode;
    if (!anchorNode || !focusNode) return null;
    if (!statementContent.contains(anchorNode) || !statementContent.contains(focusNode)) return null;

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const viewportRect = statementViewport.getBoundingClientRect();
    const scrollLeft = statementScrollRoot?.scrollLeft || 0;
    const scrollTop = statementScrollRoot?.scrollTop || 0;
    if (!rect || rect.width === 0 && rect.height === 0) return null;

    const left = rect.left - viewportRect.left + scrollLeft;
    const top = rect.top - viewportRect.top + scrollTop;
    const width = rect.width;
    const height = rect.height;
    if ([left, top, width, height].some((value) => !Number.isFinite(value))) return null;
    return { left, top, width, height };
  }

  function updateLocalStatementSelectionAwareness() {
    if (!provider) return;
    const current = provider.awareness.getLocalState()?.statement || {};
    const rect = readStatementSelectionRect();
    if (!rect && !current.viewportPointer) {
      setLocalStatementAwareness(null);
      return;
    }
    setLocalStatementAwareness({
      ...current,
      selection: rect,
    });
  }

  function updateLocalStatementPointerAwareness(event = null) {
    if (!provider) return;
    const current = provider.awareness.getLocalState()?.statement || {};
    if (!event) {
      if (!current.selection) {
        if (!current.viewportPointer) setLocalStatementAwareness(null);
        else setLocalStatementAwareness({ ...current, viewportPointer: null });
        return;
      }
      setLocalStatementAwareness({
        ...current,
        viewportPointer: null,
      });
      return;
    }
    const left = event.clientX;
    const top = event.clientY;
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 1;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 1;
    if (!Number.isFinite(left) || !Number.isFinite(top) || viewportWidth <= 0 || viewportHeight <= 0) return;
    setLocalStatementAwareness({
      ...current,
      viewportPointer: {
        left,
        top,
        xRatio: Math.min(Math.max(left / viewportWidth, 0), 1),
        yRatio: Math.min(Math.max(top / viewportHeight, 0), 1),
        viewportWidth,
        viewportHeight,
        elementAnchor: createPointerElementAnchor(left, top),
      },
    });
  }

  function stableClassNames(element) {
    return Array.from(element.classList || [])
      .filter((className) => (
        className.startsWith('oj-')
        || className.startsWith('workspace-')
        || className.startsWith('problem-')
        || className.startsWith('editor-')
        || className.startsWith('monaco-')
        || className.startsWith('sample-')
        || className.startsWith('self-test')
        || className.startsWith('sync-')
        || className.startsWith('status-chip')
        || ['badge', 'btn', 'code-workspace', 'table'].includes(className)
      ))
      .slice(0, 3);
  }

  function nthOfType(element) {
    let index = 1;
    let sibling = element.previousElementSibling;
    while (sibling) {
      if (sibling.tagName === element.tagName) index += 1;
      sibling = sibling.previousElementSibling;
    }
    return index;
  }

  function selectorPart(element) {
    const tag = element.tagName.toLowerCase();
    const classes = stableClassNames(element)
      .map((className) => `.${escapeCssIdent(className)}`)
      .join('');
    return `${tag}${classes}:nth-of-type(${nthOfType(element)})`;
  }

  function buildElementSelector(element) {
    const root = document.getElementById('oj-public-shell-app') || document.body;
    const parts = [];
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
      if (current === root) {
        if (current.id) parts.unshift(`#${escapeCssIdent(current.id)}`);
        else parts.unshift(selectorPart(current));
        break;
      }
      parts.unshift(selectorPart(current));
      current = current.parentElement;
    }
    return parts.join(' > ');
  }

  function createPointerElementAnchor(left, top) {
    const target = document.elementFromPoint(left, top);
    if (!target || !(target instanceof Element)) return null;
    const anchorTarget = target.closest([
      '.workspace-tab',
      '.workspace-actions',
      '.editor-toolbar',
      '.editor-body',
      '.monaco-editor-frame',
      '.self-test-panel',
      '.statement-sync-content',
      '.sample-card',
      '.workspace-prose',
      '.workspace-panel',
      '.code-workspace',
      '.oj-public-shell',
      'button',
      'a',
      'select',
      'textarea',
      'input',
      'pre',
      'h1',
      'h2',
      'h3',
      'p',
      'section',
    ].join(',')) || target;
    const rect = anchorTarget.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;
    return {
      selector: buildElementSelector(anchorTarget),
      xRatio: Math.min(Math.max((left - rect.left) / rect.width, 0), 1),
      yRatio: Math.min(Math.max((top - rect.top) / rect.height, 0), 1),
    };
  }

  function ensureGlobalPointerLayer() {
    if (globalPointerLayer || typeof document === 'undefined') return globalPointerLayer;
    const layer = document.createElement('div');
    layer.className = 'oj-remote-pointer-layer';
    document.body.appendChild(layer);
    globalPointerLayer = layer;
    return globalPointerLayer;
  }

  function upsertStatementPointer(key, remoteUser, pointer) {
    const layer = ensureGlobalPointerLayer();
    if (!layer || !pointer) return;
    let node = remoteStatementPointerNodes.get(key);
    if (!node) {
      node = document.createElement('div');
      node.className = 'oj-remote-statement-pointer';
      node.innerHTML = '<div class="oj-remote-statement-pointer__label"></div><div class="oj-remote-statement-pointer__dot"></div>';
      remoteStatementPointerNodes.set(key, node);
      layer.appendChild(node);
    }
    const color = remoteUser.color || userColor(remoteUser.id);
    const anchoredPosition = resolvePointerElementAnchor(pointer.elementAnchor);
    const hasRatios = Number.isFinite(pointer.xRatio) && Number.isFinite(pointer.yRatio);
    const left = anchoredPosition
      ? anchoredPosition.left
      : hasRatios
        ? Math.round(pointer.xRatio * (window.innerWidth || document.documentElement.clientWidth || 0))
        : pointer.left;
    const top = anchoredPosition
      ? anchoredPosition.top
      : hasRatios
        ? Math.round(pointer.yRatio * (window.innerHeight || document.documentElement.clientHeight || 0))
        : pointer.top;
    if (!Number.isFinite(left) || !Number.isFinite(top)) return;
    node.style.left = `${left}px`;
    node.style.top = `${top}px`;
    node.style.setProperty('--oj-remote-pointer-color', color);
    const labelNode = node.querySelector('.oj-remote-statement-pointer__label');
    if (labelNode) labelNode.textContent = remoteUser.name || remoteUser.username || '协作者';
  }

  function resolvePointerElementAnchor(anchor) {
    if (!anchor?.selector || !Number.isFinite(anchor.xRatio) || !Number.isFinite(anchor.yRatio)) return null;
    let target = null;
    try {
      target = document.querySelector(anchor.selector);
    } catch (error) {
      return null;
    }
    if (!target) return null;
    const rect = target.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;
    return {
      left: Math.round(rect.left + (anchor.xRatio * rect.width)),
      top: Math.round(rect.top + (anchor.yRatio * rect.height)),
    };
  }

  function removeStatementPointer(key) {
    const node = remoteStatementPointerNodes.get(key);
    if (!node) return;
    node.remove();
    remoteStatementPointerNodes.delete(key);
  }

  function upsertStatementSelection(key, remoteUser, selection) {
    if (!statementOverlay || !selection) return;
    let node = remoteStatementSelectionNodes.get(key);
    if (!node) {
      node = document.createElement('div');
      node.className = 'oj-remote-statement-selection';
      remoteStatementSelectionNodes.set(key, node);
      statementOverlay.appendChild(node);
    }
    const color = remoteUser.color || userColor(remoteUser.id);
    node.style.left = `${selection.left}px`;
    node.style.top = `${selection.top}px`;
    node.style.width = `${Math.max(selection.width, 4)}px`;
    node.style.height = `${Math.max(selection.height, 18)}px`;
    node.style.setProperty('--oj-remote-selection-color', color);
  }

  function removeStatementSelection(key) {
    const node = remoteStatementSelectionNodes.get(key);
    if (!node) return;
    node.remove();
    remoteStatementSelectionNodes.delete(key);
  }

  function updateRemoteStatementPresence() {
    if (!provider) return;
    const activeKeys = new Set();
    provider.awareness.getStates().forEach((state, clientId) => {
      const remoteUser = state.user;
      const statement = state.statement;
      if (!remoteUser || clientId === provider.awareness.clientID || remoteUser.id === localUser?.id || !statement) return;
      const key = `client-${sanitizeCursorKey(clientId)}`;
      activeKeys.add(key);
      if (statement.viewportPointer) upsertStatementPointer(key, remoteUser, statement.viewportPointer);
      else removeStatementPointer(key);
      if (statementOverlay && statement.selection) upsertStatementSelection(key, remoteUser, statement.selection);
      else removeStatementSelection(key);
      if (statement.ripple?.id && !seenRippleIds.has(statement.ripple.id)) {
        seenRippleIds.add(statement.ripple.id);
        renderClickRipple(statement.ripple.point, remoteUser);
      }
      if (statement.scroll) applyRemoteScroll(statement.scroll);
    });

    Array.from(remoteStatementPointerNodes.keys()).forEach((key) => {
      if (!activeKeys.has(key)) removeStatementPointer(key);
    });
    Array.from(remoteStatementSelectionNodes.keys()).forEach((key) => {
      if (!activeKeys.has(key)) removeStatementSelection(key);
    });
  }

  function bindStatementSurface({ viewportEl, contentEl = null, overlayEl = null, scrollEl = null } = {}) {
    disposeStatementOverlay();
    if (!viewportEl) return;
    statementViewport = viewportEl;
    statementContent = contentEl || viewportEl;
    statementOverlay = overlayEl || viewportEl;
    statementScrollRoot = scrollEl || viewportEl;

    statementPointerMoveHandler = (event) => {
      if (!active.value) return;
      updateLocalStatementPointerAwareness(event);
    };
    statementPointerLeaveHandler = () => {
      if (!active.value) return;
      scheduleStatementSelectionUpdate();
    };
    viewportPointerMoveHandler = (event) => {
      if (!active.value) return;
      updateLocalStatementPointerAwareness(event);
    };
    viewportPointerLeaveHandler = () => {
      if (!active.value) return;
      updateLocalStatementPointerAwareness(null);
    };
    statementSelectionChangeHandler = () => {
      if (!active.value) return;
      scheduleStatementSelectionUpdate();
    };
    statementScrollHandler = () => {
      if (!active.value) return;
      scheduleStatementSelectionUpdate();
      queuePublishScrollState('statement');
      updateRemoteStatementPresence();
    };

    ensureGlobalPointerLayer();
    bindDrawingLayer();
    window.addEventListener('pointermove', viewportPointerMoveHandler, { passive: true });
    window.addEventListener('pointerleave', viewportPointerLeaveHandler, { passive: true });
    document.addEventListener('mouseleave', viewportPointerLeaveHandler);
    statementViewport.addEventListener('pointermove', statementPointerMoveHandler, { passive: true });
    statementViewport.addEventListener('pointerleave', statementPointerLeaveHandler, { passive: true });
    document.addEventListener('selectionchange', statementSelectionChangeHandler);
    statementScrollRoot.addEventListener('scroll', statementScrollHandler, { passive: true });
    window.addEventListener('scroll', statementScrollHandler, true);
    window.addEventListener('resize', statementScrollHandler, { passive: true });
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
    editorScrollDisposable = editor.onDidScrollChange(() => {
      if (!active.value) return;
      queuePublishScrollState('editor');
    });
  }

  function setCollaborationFrame(activeFrame) {
    document.documentElement.classList.toggle('oj-sync-frame-active', Boolean(activeFrame));
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
    setCollaborationFrame(true);
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
    updateRemoteStatementPresence();
  }

  async function startSync({
    editorView,
    room,
    user,
    collaborationUrl,
    serverUrl,
    seedDocument = false,
    statementViewportEl = null,
    statementContentEl = null,
    statementOverlayEl = null,
    statementScrollEl = null,
  }) {
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
    bindStatementSurface({
      viewportEl: statementViewportEl,
      contentEl: statementContentEl,
      overlayEl: statementOverlayEl,
      scrollEl: statementScrollEl,
    });

    try {
      const [yjsModule, websocketModule] = await Promise.all([
        import('yjs'),
        import('y-websocket'),
      ]);
      Y = yjsModule;
      WebsocketProvider = websocketModule.WebsocketProvider;

      ydoc = new Y.Doc();
      ytext = ydoc.getText('monaco');
      ydrawings = ydoc.getArray('screen-drawings');
      drawingObserver = syncDrawingsFromYjs;
      ydrawings.observe(drawingObserver);
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
      syncDrawingsFromYjs();
      updateLocalSelectionAwareness();
      updateRemoteSelections();
      updateLocalStatementSelectionAwareness();
      updateRemoteStatementPresence();
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
    if (editorScrollDisposable) {
      editorScrollDisposable.dispose();
      editorScrollDisposable = null;
    }
    if (ytext && textObserver) {
      ytext.unobserve(textObserver);
      textObserver = null;
    }
    if (ydrawings && drawingObserver) {
      ydrawings.unobserve(drawingObserver);
      drawingObserver = null;
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
    setLocalStatementAwareness(null);
    disposeStatementOverlay();
    if (ydoc) {
      ydoc.destroy();
      ydoc = null;
    }
    ytext = null;
    ydrawings = null;
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
    setCollaborationFrame(false);
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
    drawingMode,
    drawCount,
    toggleDrawingMode,
    setDrawingMode,
    clearDrawings,
    startSync,
    stopSync,
  };
}
