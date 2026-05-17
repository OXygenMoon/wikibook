**功能实现与修复计划**

1. **修复 UI 高度不一致**

   * 在 `templates/admin/edit_badge.html` 中，为文件上传输入框 (`.file-input`) 添加 `file-input-md` 或调整父容器的 Flex 布局，确保与左侧的文本输入框 (`.input`) 高度对齐。

2. **修复图片上传无法替换问题**

   * 检查 `edit_badge.html` 中的 JS 上传逻辑。我之前修改了上传接口返回格式为 `{"success": 1, "url": "..."}`，但 `edit_badge.html` 中的 JS 仍然可能在使用旧的解析逻辑（`data.data.filePath`）。

   * 更新 `templates/admin/manage_badges.html` 和 `templates/admin/edit_badge.html` 中的 `uploadBadgeIcon` 函数，使其兼容新的接口返回格式。

3. **新建徽章支持图片上传**

   * `templates/admin/manage_badges.html` 中已经有了上传控件和 JS，但需要确保 JS 逻辑与后端接口兼容（同第 2 点）。

   * 确认表单提交时 `icon` 字段能正确接收上传后的 URL。

4. **增加“手动发放”条件**

   * **后端 (`app.py`)**:

     * 在 `edit_badge` 和 `create_badge` (即 `manage_badges`) 路由中，无需特殊修改，只需前端传值 `manual` 即可存入数据库。

     * 修改 `check_and_award_badges` 函数，确保它**忽略** `condition_type == 'manual'` 的徽章（不进行自动检查）。

     * 新增一个路由 `/admin/badges/<int:badge_id>/award` (POST)，用于接收管理员选定的用户列表，并手动创建 `UserBadge` 记录。

   * **前端 (`templates/admin/manage_badges.html`** **&** **`edit_badge.html`)**:

     * 在 `select` 下拉菜单中添加 `<option value="manual">手动发放</option>`。

     * 在 `manage_badges.html` 的列表项中，如果 `badge.condition_type == 'manual'`，则显示一个“发放给...”按钮。

     * 点击按钮弹出模态框（Modal），列出所有用户（支持多选），提交后调用上述后端接口。

5. **显示已获得人数**

   * **后端 (`app.py`)**:

     * 在 `manage_badges` 路由中，查询徽章列表时，同时统计每个徽章的获得人数。

     * 可以通过 SQLAlchemy 的 `db.session.query(Badge, func.count(UserBadge.id)).outerjoin(UserBadge).group_by(Badge.id)` 来高效查询，或者简单地在 Jinja2 模板中使用 `badge.user_badges|length`（需要在 `Badge` 模型中添加 `user_badges` 的 `backref` 或 `relationship`）。

     * 检查 `Badge` 模型，发现已有 `UserBadge` 定义了 `badge = db.relationship("Badge")`，建议在 `Badge` 侧添加 `users = db.relationship("UserBadge", backref="badge_info", lazy="dynamic")` 以便计数。

   * **前端 (`manage_badges.html`)**:

     * 在徽章卡片中显示获得人数统计（例如：`{{ badge.users.count() }} 人已获得`）。

**实施步骤**

1. **修改** **`app.py`**:

   * 更新 `Badge` 模型关系（添加 `users` 关联以方便计数）。

   * 更新 `check_and_award_badges` 忽略 `manual` 类型。

   * 添加 `/admin/badges/<int:badge_id>/award` 路由。
2. **修改** **`templates/admin/manage_badges.html`**:

   * 更新上传 JS 逻辑。

   * 添加“手动发放”选项。

   * 添加手动发放的 Modal 和按钮。

   * 显示获得人数。
3. **修改** **`templates/admin/edit_badge.html`**:

   * 修复 UI 高度问题。

   * 更新上传 JS 逻辑。

   * 添加“手动发放”选项。

**Code Reference**

* `app.py`: [check\_and\_award\_badges](file:///root/projects/wikibook/app.py#L1920)

* `templates/admin/manage_badges.html`: [Badge List](file:///root/projects/wikibook/templates/admin/manage_badges.html#L14)

* `templates/admin/edit_badge.html`: [Icon Input](file:///root/projects/wikibook/templates/admin/edit_badge.html#L20)

