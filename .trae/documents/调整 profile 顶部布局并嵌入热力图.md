## 目标
- 将 profile.html 顶部板块改为靠左且更窄的布局。
- 把 book/my_notes.html 中的热力图移动到该顶部板块的右侧，形成左右并排的响应式布局。

## 涉及文件
- [profile.html](file:///root/projects/wikibook/templates/profile.html)
- [my_notes.html](file:///root/projects/wikibook/templates/book/my_notes.html#L226)
- 可能需要： [base.html](file:///root/projects/wikibook/templates/base.html)
- 新增局部模板： templates/partials/notes_heatmap.html（用于复用热力图块）

## 实现步骤
1. 调整 profile 顶部容器样式
- 将现有居中/全宽类改为靠左且较窄：使用 text-left、items-start、justify-start，结合 max-w-lg 或 md:w-2/5。
- 外层采用响应式两列布局：md:flex md:justify-between 或 md:grid md:grid-cols-2，并设置 gap-6。

2. 抽取热力图为局部模板
- 在 [my_notes.html](file:///root/projects/wikibook/templates/book/my_notes.html#L226) 附近定位热力图容器及其初始化脚本。
- 创建 templates/partials/notes_heatmap.html，包含：
  - 热力图根容器（例如 <div id="notes-heatmap">）。
  - 初始化脚本（保留现有数据获取逻辑与依赖）。

3. 在 profile 顶部右侧插入热力图
- 在 profile.html 顶部布局的右列引入该局部模板（例如 Jinja include）。
- 为右侧容器设置尺寸：w-full md:w-3/5，固定高度或自适应（如 h-[280px]），并与左侧内容保持合理间距。

4. 管理依赖资源
- 将热力图依赖的 JS/CSS（如 Tailwind、ECharts/Cal-Heatmap/D3 等）在 base.html 统一引入，或在 profile.html 的 scripts 区块按需引入，避免重复加载。

5. 数据与渲染
- 若热力图依赖模板变量或异步接口，确保 profile 的视图函数也提供相同变量，或保持接口可访问。
- 不改变数据来源，只复用现有逻辑，避免回归风险。

6. 响应式与可用性
- md 及以上屏幕：左右并排，左窄右宽。
- 小屏：自动纵向堆叠，顺序为左内容在上、热力图在下。

7. 验证
- 打开 profile 页面，检查布局与对齐。
- 观察控制台是否有脚本错误；验证热力图正确渲染与数据加载。

## 变更范围与风险
- 主要是模板结构与样式调整；抽取局部模板有助于后续复用。
- 风险在于依赖脚本未在 profile 页面加载或数据未注入；通过依赖统一与视图注入解决。

## 交付结果
- 更新后的 profile 顶部为靠左窄列 + 右侧热力图的响应式布局。
- 热力图作为局部模板复用，并在 my_notes 与 profile 中均可渲染。