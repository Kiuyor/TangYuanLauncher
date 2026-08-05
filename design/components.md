# 组件规格 — Rev.Ini 编辑器

> 逐组件规格对照表:design.md 规范 → 实现状态 → 实现位置
> 本轮审计日期:2026-08-03

---

## 对照表

| 组件 | MD3 规范 | 实现状态 | 实现位置 |
|------|---------|---------|---------|
| Navigation Rail | 88px 宽,图标+标签,pill 指示器 | ✅ 已实现 | main_window._build_nav, widgets.NavDelegate |
| Top App Bar | 64px 高,三栏布局 | ✅ 已实现 | main_window._build_title_bar |
| Bottom Bar | 40px 高,状态+编码+时钟 | ✅ 已实现 | main_window._build_status_bar |
| Filled Card(字段行) | 12px 圆角,surface_low 背景 | ✅ 已实现 | widgets.FieldRow |
| Material Switch | MD3 开关,thumb 动画 | ✅ 已实现 | widgets.ToggleSwitch |
| Filled Text Field | 底边框,focus 琥珀色 | ✅ 已实现 | FieldRow._make_text (QLineEdit + QSS) |
| MD3 ComboBox | 自绘 popup,圆角 | ✅ 已实现 | widgets.MD3ComboBox |
| MD3 SpinBox | 自绘 +/- 按钮 | ✅ 已实现 | widgets.MD3SpinBox |
| Round Button | pill 形状,state layer | ✅ 已实现 | widgets.RoundButton |
| Snackbar | 底部弹出,44px,撤销按钮 + error 变体(警告图标+action) | ✅ 已实现(v3.3) | widgets.Snackbar |
| Confirm Dialog | 居中圆角,3 按钮 | ✅ 已实现 | widgets.ConfirmDialog |
| Page Transition | Shared Axis X,300ms 快照淡入 | ✅ 已实现 | widgets.PageTransitionOverlay |
| **搜索框** | 导航区常驻,30px | ✅ 新增(本轮) | main_window._build_nav |
| **搜索结果面板** | 浮层,380px,键盘导航 | ✅ 新增(本轮) | widgets.SearchPanel |
| **快捷键** | Ctrl+S/O/F | ✅ 新增(本轮) | main_window._build_shortcuts |

---

## 新增组件规格

### 搜索框(SearchBox)

| 属性 | 值 | 说明 |
|------|-----|------|
| 位置 | Navigation Rail 顶部 | 88px 宽栏内,10px 内边距 |
| 高度 | 30px | 紧凑设计,不占过多导航空间 |
| 背景 | surface_high + outline_variant 边框 | 与下拉框一致 |
| focus 态 | primary 边框 | 琥珀色高亮 |
| Leading 图标 | Material search 线条图标(自绘 QPainter) | on_surface_variant,18px,替代 emoji 🔍 |
| placeholder | "搜索" | 清除按钮内置 |
| 匹配范围 | 标签 + 描述 + section.key + 分组名 + chips | 全文小写匹配 |
| 快捷键 | Ctrl+F 聚焦 + 全选 | 全局快捷键 |

### 搜索结果面板(SearchPanel)

| 属性 | 值 | 说明 |
|------|-----|------|
| 宽度 | 380px | 覆盖内容区左上角 |
| 行高 | 36px | 每行:标签 + 面包屑(灰色) |
| 最大可见行 | 8 | 超出滚动 |
| 背景 | surface_highest + outline_variant 边框 | MD3 弹窗层级 |
| 选中态 | primary_container 背景 | 琥珀容器色 |
| 空态 | "无匹配项" 居中 | outline 色文字 |
| 键盘 | ↑↓ 选择(循环)/ Enter 跳转 / Esc 关闭 | 焦点留在搜索框 |
| 跳转 | 切页 → 切子 tab → 滚动定位 → flash 高亮 1.2s | 自动定位 |

### Flash 高亮

| 属性 | 值 | 说明 |
|------|-----|------|
| 背景 | primary_container | 搜索跳转后引导视线 |
| 持续 | 1200ms | 自动清除 |
| 触发 | 搜索跳转 / 不影响正常 hover | QSS property 动态切换 |

---

## 状态规范

### Disabled 状态

| 组件 | 规范 | 实现 |
|------|------|------|
| 按钮 | opacity 0.38 + 禁用点击 | ✅ QSS `:disabled` |
| 输入框 | opacity 0.38 + 不可编辑 | ✅ QSS `:disabled` |
| 开关 | opacity 0.38 + 不可切换 | ✅ ToggleSwitch.setEnabled(False) |

### Error 状态

| 组件 | 规范 | 实现 |
|------|------|------|
| 保存失败 | 错误 Snackbar(error 变体, 前置 Material warning 图标, action 染 error_container 深红, 10s) | ✅ 已迁移(v3.2/v3.3, v3.4 对比度修复): 编码→切换 UTF-8 / 写入→重试 / 损坏→从备份恢复 |
| 输入框(编码错误) | error 底边框 | ⚠ 内联 error 边框未做(经 Snackbar 指引切换编码) |
| 文件损坏检测 | section 头结构判断 | ✅ _target_file_intact |

### Hover 状态

| 组件 | 规范 | 实现 |
|------|------|------|
| 卡片 | surface_low → card_hover | ✅ QSS `:hover` |
| 按钮 | 8% on-surface state layer | ✅ RoundButton._colors + paintEvent |
| 搜索结果项 | 白色 6% on-surface 状态层(面板 surface_highest 之上) | ✅ QSS `::item:hover` |

---

## 无障碍(A11y)

### 已实现

| 项 | 状态 | 说明 |
|----|------|------|
| ToolTip | ✅ 12 处 | 按钮、编码框、搜索框、目录等(含快捷键后缀 Ctrl+S/O/F) |
| 键盘导航 | ✅ | Ctrl+S/O/F,搜索 ↑↓Enter Esc |
| 焦点可见 | ✅ | QSS focus 边框(琥珀色) + 导航项自绘焦点环(v3.4) |
| 高对比度 | ✅ | 暗色主题,文字/背景对比度 ≥ 4.5:1 |

### 待改进(本轮不做,记录 backlog)

| 项 | 说明 |
|----|------|
| WhatsThis 帮助 | 每个字段可加详细说明(Ctrl+Shift+F1 显示) |
| 显式 Tab 顺序 | 当前依赖布局默认顺序,可显式 setTabOrder |
| 屏幕阅读器 | PySide6 AccessibilityInterface 未深度集成 |

---

## 动效规范

| 动效 | 时长 | 曲线 | 实现 |
|------|------|------|------|
| 页面切换(Shared Axis X) | 300ms | EmphasizedDecelerate | PageTransitionOverlay |
| Pill 指示器滑动 | 300ms | InOutCubic | QPropertyAnimation (NavDelegate.animate_pill_to) |
| Switch thumb | 100ms | InOutCubic | ToggleSwitch._anim (design.md Durations: 100ms Switch toggle) |
| Snackbar 显示/隐藏 | 300ms | OutCubic | QPropertyAnimation (Snackbar._anim, design.md: 300ms) |
| Flash 高亮 | 1200ms | 无(持续态 + 瞬切) | QTimer + QSS property |
| 降级模式 | 0ms(直接切换) | — | REVINI_NO_ANIM=1 环境变量 |
