# 实施标签系统与笔记历史版本

## Phase 1: 标签系统 (Tagging System)
### 1. 数据库变更
- 创建 `Tag` 模型 (id, name)。
- 创建关联表 `note_tags` (note_id, tag_id) 和 `wiki_page_tags` (page_id, tag_id)。
- 迁移数据库。

### 2. 后端逻辑
- 更新 `Note` 和 `WikiPage` 模型，建立与 `Tag` 的多对多关系。
- 在创建/编辑 笔记和 Wiki 页面时，处理标签的解析（支持输入逗号分隔的标签或从列表选择）。
- 更新搜索逻辑，支持按标签名称过滤。

### 3. 前端实现
- **编辑器**: 使用 `Tagify` 或类似的轻量级库，或手写简单的标签输入框（输入文本自动生成标签）。
- **展示页**: 在标题下方或底部精美展示标签。
- **列表页/首页**: 点击标签可筛选相关内容。

## Phase 2: 笔记历史版本 (Note History)
### 1. 数据库变更
- 创建 `NoteHistory` 模型 (id, note_id, title, content_md, updated_at, user_id)。

### 2. 业务逻辑
- 修改 `edit_note` 路由：在保存更新前，将当前版本存入 `NoteHistory`。
- 新增 `note_history` 路由：查看历史列表。
- 新增 `restore_note` 路由：将旧版本内容覆盖回当前笔记。

### 3. 前端实现
- 在笔记详情页添加“历史版本”入口（类似 Wiki 页面）。
- 创建历史版本列表页和对比/恢复界面。
