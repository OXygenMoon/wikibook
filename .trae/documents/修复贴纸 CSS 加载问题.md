**原因分析**

`sticker.css` 未被加载的根本原因是模板块（block）名称不匹配：
*   在 `base.html` 中，预留的 CSS 扩展块名为 `{% block extra_css %}`。
*   在 `index.html` 和 `book/index.html` 中，错误地使用了 `{% block styles %}` 来引入 `sticker.css`。

由于 `base.html` 中没有定义 `styles` 这个块，因此子模板中的这部分内容被忽略，导致 CSS 文件未被加载，进而导致贴纸 UI 样式错乱。

**修复计划**

1.  **修正 Wiki 首页模板 (`templates/index.html`)**：
    *   将 `{% block styles %}` 替换为 `{% block extra_css %}`。
2.  **修正 Book 首页模板 (`templates/book/index.html`)**：
    *   同样将 `{% block styles %}` 替换为 `{% block extra_css %}`。

**验证**

*   完成修改后，刷新首页。
*   检查 HTML 源码，确认 `<head>` 中是否已包含 `sticker.css` 的 `<link>` 标签。
*   检查 UI，确认贴纸库按钮、抽屉面板和贴纸本身的样式是否恢复正常。
