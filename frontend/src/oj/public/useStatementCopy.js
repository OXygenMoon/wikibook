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

      pre.classList.add('statement-code-block');

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
      pre.appendChild(button);

      cleanups.push(() => {
        button.removeEventListener('click', handleClick);
        button.remove();
        pre.classList.remove('statement-code-block');
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
