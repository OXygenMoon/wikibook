import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue';

function fallbackCopyText(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', 'true');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  textarea.style.pointerEvents = 'none';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();

  try {
    return document.execCommand('copy');
  } finally {
    textarea.remove();
  }
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  if (!fallbackCopyText(text)) {
    throw new Error('复制失败，请检查浏览器剪贴板权限。');
  }
}

export function useStatementCopy(rootRef, contentRef, { onCopied = () => {}, onCopyError = () => {} } = {}) {
  const cleanups = [];

  function cleanupButtons() {
    while (cleanups.length) {
      const dispose = cleanups.pop();
      dispose?.();
    }
  }

  function enhanceCodeBlocks() {
    cleanupButtons();

    const root = rootRef.value;
    if (!root) return;

    const blocks = root.querySelectorAll('pre');
    blocks.forEach((pre, index) => {
      if (!(pre instanceof HTMLElement)) return;
      const code = pre.querySelector('code');
      if (!code) return;

      const wrapper = document.createElement('div');
      wrapper.className = 'statement-code-frame';

      const toolbar = document.createElement('div');
      toolbar.className = 'statement-code-toolbar';

      const meta = document.createElement('div');
      meta.className = 'statement-code-meta';
      meta.textContent = code.className
        .split(/\s+/)
        .find((name) => name.startsWith('language-'))
        ?.replace('language-', '')
        .toUpperCase() || 'CODE';

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'statement-copy-button';
      button.setAttribute('aria-label', '复制代码');
      button.innerHTML = '<i class="fas fa-copy" aria-hidden="true"></i><span>复制</span>';
      button.dataset.copyBlockId = `${index}`;

      const handleClick = async () => {
        try {
          await copyText(code.textContent || '');
          onCopied();
        } catch (error) {
          onCopyError(error);
        }
      };

      button.addEventListener('click', handleClick);

      const parent = pre.parentNode;
      if (!parent) return;

      parent.insertBefore(wrapper, pre);
      wrapper.appendChild(toolbar);
      toolbar.appendChild(meta);
      toolbar.appendChild(button);
      wrapper.appendChild(pre);

      cleanups.push(() => {
        button.removeEventListener('click', handleClick);
        if (wrapper.parentNode) {
          wrapper.parentNode.insertBefore(pre, wrapper);
          wrapper.remove();
        } else {
          button.remove();
        }
      });
    });
  }

  async function refreshCodeBlocks() {
    await nextTick();
    enhanceCodeBlocks();
  }

  onMounted(() => {
    refreshCodeBlocks();
  });

  watch(contentRef, () => {
    refreshCodeBlocks();
  });

  onBeforeUnmount(() => {
    cleanupButtons();
  });
}
