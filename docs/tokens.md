# 设计令牌 Tokens — 汤圆启动器 Rev.Ini 编辑器

> 唯一事实源: `docs/preview v1.html`(HTML 是唯一事实源,本文件随它维护)
> 主题: **矢车菊蓝 #6495ED 纯色体系**(无渐变、无发光)
> 维护义务: 任何组件/token 变更必须同步本文件与 `design-system.md`、`rules.md`(见 rules.md §同步义务)
> 命名: 统一语义 kebab-case;HTML 用 `var(--token)`,Flet 用常量 `COL_*`/`SZ_*`/`RADIUS_*`/`SPACE_*`(映射见每节)

---

## 1. 颜色 Colors

### 1.1 背景色 (Background)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `bg-deep` | 最深底 | `#0c0e14` | 窗口外壳、标题栏、状态栏 | `var(--bg-deep)` | `COL_BG_DEEP` |
| `bg-main` | 主内容底 | `#0f1117` | 主页内容区、编辑页内容区 | `var(--bg-main)` | `COL_BG_MAIN` |
| `bg-card` | 卡片底 | `#161922` | 配置卡片、工具卡片 | `var(--card)` | `COL_BG_CARD` |
| `bg-card-2` | 卡片次级底 | `#1e293b` | 头像底、工具栏按钮底 | `var(--card-2)` | `COL_BG_CARD_2` |
| `bg-sidebar` | 侧栏底 | `#11141d` | 编辑页左侧导航栏 | `var(--sidebar)` | `COL_BG_SIDEBAR` |
| `bg-input` | 输入控件底 | `rgba(0,0,0,0.2)` | 输入框/下拉框背景 | (CSS 内联) | `COL_BG_INPUT` |
| `bg-ghost` | 幽灵底(白4%) | `rgba(255,255,255,0.04)` | 服务器状态胶囊、chip 默认底 | (CSS 内联) | `COL_BG_GHOST` |
| `bg-ghost-2` | 幽灵底(白3%) | `rgba(255,255,255,0.03)` | 工具栏按钮底、卡片 hover 底 | (CSS 内联) | `COL_BG_GHOST_2` |
| `bg-ghost-3` | 幽灵底(白2%) | `rgba(255,255,255,0.02)` | 推荐项面板底、滚动条轨道 | (CSS 内联) | `COL_BG_GHOST_3` |

### 1.2 品牌色 (Brand, 矢车菊蓝系)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `brand` | 品牌主色 | `#6495ED` | 启动按钮、保存按钮、运行按钮、激活导航、输入 focus、编码激活 | `var(--brand)` | `COL_BRAND` |
| `brand-hover` | 主色 hover | `#4F7FE0` | 主按钮悬停、启动中态 | `var(--brand-hover)` | `COL_BRAND_HOVER` |
| `brand-light` | 主色浅 | `#9DB9F3` | 版本徽章字、头像占位字、chip 已添加字、kicker、类别标签字 | `var(--brand-light)` | `COL_BRAND_LIGHT` |
| `brand-soft` | 主色柔 | `#8FB1F0` | 激活导航图标/文字 | `var(--brand-soft)` `var(--blue-light)` | `COL_BRAND_SOFT` |
| `brand-bg-10` | 主色底 10% | `rgba(100,149,237,0.1)` | 代码键名标签底、导航激活底 | (CSS 内联) | `COL_BRAND_BG_10` |
| `brand-bg-15` | 主色底 15% | `rgba(100,149,237,0.15)` | 类别标签底 | (CSS 内联) | `COL_BRAND_BG_15` |
| `brand-bg-18` | 主色底 18% | `rgba(100,149,237,0.18)` | chip 已添加态底 | (CSS 内联) | `COL_BRAND_BG_18` |
| `brand-bg-20` | 主色底 20% | `rgba(100,149,237,0.2)` | 版本徽章底 | (CSS 内联) | `COL_BRAND_BG_20` |

> 兼容别名: HTML 中的 `--blue`(= `--brand`)、`--blue-light`(= `--brand-soft`)为早期命名残留,Flet 统一用 `COL_BRAND`/`COL_BRAND_SOFT`。

### 1.3 文字色 (Text)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `text-primary` | 主文本 | `#ffffff` | 标题、输入值、白字按钮 | `var(--text-main)` | `COL_TEXT_PRIMARY` |
| `text-secondary` | 次文本 | `#e2e8f0` | 次级文字、在线人数 | `var(--text-2)` | `COL_TEXT_SECONDARY` |
| `text-muted` | 辅助文本 | `#a0aec0` | 辅助说明、普通图标 | `var(--text-3)` | `COL_TEXT_MUTED` |
| `text-dim` | 弱化文本 | `#64748b` | 描述、标签、离线状态 | `var(--text-4)` | `COL_TEXT_DIM` |
| `text-disabled` | 禁用文本 | `#6b7280` | 禁用态 | `var(--text-disabled)` | `COL_TEXT_DISABLED` |

### 1.4 功能色 (Status)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `status-green` | 成功/在线 | `#10b981` | 在线圆点、状态栏勾、低风险、完成 | `var(--green)` | `COL_OK` |
| `status-amber` | 警告/运行中 | `#f59e0b` | 中风险、运行中状态 | (CSS 内联) | `COL_WARN` |
| `status-red` | 错误/高危 | `#ef4444` | 关闭按钮 hover、高风险、失败状态 | (CSS 内联) | `COL_ERR` |
| `warn-bg` | 警告提示条底 | `rgba(245,158,11,0.12)` | CFG 页启动参数提示条 | (CSS 内联) | `COL_WARN_BG` |
| `err-bg` | 错误提示条底 | `rgba(239,68,68,0.12)` | CFG 页预设缺失提示条 | (CSS 内联) | `COL_ERR_BG` |

### 1.5 边框/描边 (Border)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `border-subtle` | 细边框 | `rgba(255,255,255,0.05)` | 卡片/栏/面板默认边框、分割线 | `var(--border-subtle)` | `COL_BORDER_SUBTLE` |
| `border-visible` | 明显边框 | `rgba(255,255,255,0.1)` | 输入框/下拉/chip 边框、窗口边框 | `var(--border-visible)` | `COL_BORDER_VISIBLE` |
| `border-brand` | 品牌边框 | `rgba(100,149,237,0.3)` | 版本徽章、chip 已添加、工具卡 hover | `var(--border-brand)` | `COL_BORDER_BRAND` |
| `focus-ring` | 聚焦光环 | `rgba(100,149,237,0.2)` | 输入框/下拉 focus 外圈 | (CSS 内联) | `COL_FOCUS_RING` |

### 1.6 已收编硬编码 (原散落色, 2026-08-08 收编)

| Token | 语义名 | 色值 | 原位置 | 说明 | Flet |
|-------|--------|------|--------|------|------|
| `launch-busy` | 启动中底 | `#4F7FE0` | preview v1.html JS `startGame()` | 与 brand-hover 同值,统一引用 | `COL_LAUNCH_BUSY` |
| `launch-done` | 已启动底 | `#10b981` | preview v1.html JS `startGame()` | 与 status-green 同值,统一引用 | `COL_LAUNCH_DONE` |
| `launch-glow` | 已启动辉光 | `rgba(16,185,129,0.4)` | preview v1.html JS `startGame()` | 已启动时按钮外辉光 | `COL_LAUNCH_GLOW` |
| `hover-track` | 悬停轨道 | `rgba(255,255,255,0.12)` | switch-track 底 | 开关未开态轨道 | `COL_SWITCH_INACTIVE_TRACK`(flet 实机 #2A2730) |
| `thumb-shadow` | 滑块投影 | `rgba(0,0,0,0.4)` | switch thumb | 开关滑块阴影 | `COL_SWITCH_INACTIVE_THUMB`(flet 实机 #8A8494) |
| `dot-glow` | 在线点辉光 | `rgba(16,185,129,0.15)` | `.server-dot.online` box-shadow | 在线状态点外辉光 | `SHADOW_DOT_ONLINE` |
| `hover-btnbar` | 顶栏按钮 hover | `rgba(255,255,255,0.07)` | `.btn-bar:hover` | 顶栏按钮悬停提亮 | `COL_BTN_BAR_HOVER` |
| `hover-winbtn` | 窗口按钮 hover | `rgba(255,255,255,0.08)` | `.win-btn:hover` `.chip:hover` | 窗口按钮/chip 悬停提亮 | (ui.win_btn style hovered) |
| `hover-scrollbar` | 滚动条 hover | `rgba(255,255,255,0.2)` | `.content::-webkit-scrollbar-thumb:hover` | 滚动条滑块悬停 | (flet 原生滚动条) |
| `shadow-window` | 窗口投影 | `0 24px 80px rgba(0,0,0,0.6)` | `.window` | 窗口浮起投影 | `SHADOW_WINDOW` |
| `shadow-btn` | 按钮投影 | `0 2px 8px rgba(0,0,0,0.35)` | `.btn-launch` | 按钮常态投影 | `SHADOW_BTN` |
| `shadow-btn-hover` | 按钮投影 hover | `0 4px 12px rgba(0,0,0,0.4)` | `.btn-launch:hover` | 按钮悬停投影 | `SHADOW_BTN_HOVER` |

> ⚠ 收编后 Flet 实现中**禁止再出现** `#4F7FE0`/`#10b981` 字面量,统一引用 `COL_BRAND_HOVER`/`COL_OK`。

### 1.7 裁剪相关 (Crop, 2026-08-23 修改头像页新增)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `crop-canvas-bg` | 裁剪画布底 | `#0a0b10` | 裁剪区画布背景(比 bg-deep 更深) | (CSS 内联) | `COL_CROP_CANVAS_BG` |
| `crop-mask` | 裁剪遮罩 | `rgba(0,0,0,0.55)` | 裁剪框外遮罩、头像 hover 遮罩(avatar-hint) | (CSS 内联) | `COL_CROP_MASK` |
| `crop-grid` | 裁剪九宫格线 | `rgba(255,255,255,0.25)` | 裁剪框内九宫格线 | (CSS 内联) | `COL_CROP_GRID` |

> 裁剪把手白边 `#ffffff` 复用 `text-primary`(`COL_TEXT_PRIMARY`),不单列。

---

## 2. 字号 Font Sizes

| Token | 值 | 用途 | 场景 | Flet |
|-------|-----|------|------|------|
| `font-44` | 44px | 启动按钮图标 | `.btn-launch .ic` | `FONT_44` |
| `font-36` | 36px | 头像占位首字 | `.avatar span` | `FONT_36` |
| `font-20` | 20px | 页面标题 (800) | `.page-head h2` | `FONT_20` |
| `font-20-ic` | 20px | 导航图标 | `.nav-item .ic` | `FONT_20_IC` |
| `font-18` | 18px | 昵称/主页标题 (700) | `.nickname`、标题栏"汤圆启动器" | `FONT_18` |
| `font-16` | 16px | 启动命令输入框 (mono) | `.launch-split textarea` | `FONT_16` |
| `font-15` | 15px | 在线人数/在线标签/状态图标 | `.sm-count` `.sm-label` | `FONT_15` |
| `font-14` | 14px | 卡片标题/工具名 (700)、输入框值、按钮图标 | `.card-title` `.tool-name` `.input-dark` `.btn-bar .ic` | `FONT_14` |
| `font-13` | 13px | 下拉框值 | `.select-dark` | `FONT_13` |
| `font-12` | 12px | 描述/按钮文字/状态消息 | `.card-desc` `.btn-bar` `.status-msg` `.tool-status` | `FONT_12` |
| `font-11` | 11px | 标签/提示/风险/chips | `.rec-title` `.risk-tag` `.chip` `.enc-btn` | `FONT_11` |
| `font-10` | 10px | 徽章/代码键名/类别/kicker/导航字 | `.version-tag` `.code-tag` `.cat-tag` `.kicker` `.nav-item span` | `FONT_10` |

> 数字命名直接对应 px 值,新增字号须走 design-system.md 评审并登记。

---

## 3. 圆角 Radius

> 2026-08-22 用户决策: 全 UI 矩形化 — 4/6/8/16px 圆角全部改为直角(窗口/卡片/按钮/输入框/标签),
> 仅保留形状元素(头像/启动按钮正圆、状态胶囊/版本徽章/开关胶囊)。chips 推荐项同步改方形。
> 以下表格保留历史值并标注现状; `RADIUS_LG/SM/XS/2XS` 常量在 Flet 侧已无 UI 使用(保留定义防回归)。

| Token | 值 | 用途 | 场景 | Flet |
|-------|-----|------|------|------|
| `radius-circle` | 50% | 头像/启动按钮/滑块(保留) | `.avatar` `.btn-launch` `.thumb` | `RADIUS_CIRCLE`(999) |
| `radius-pill` | 999px | 胶囊: 版本徽章/状态胶囊/开关(保留); ~~chips~~ 2026-08 改方形 | `.version-tag` `.server-monitor` `.switch-track` | `RADIUS_PILL` |
| `radius-lg` | 16px | ~~窗口外壳~~ → 矩形(2026-08-22) | ~~`.window`~~ | `RADIUS_LG`(已无 UI 使用) |
| `radius-md` | 12px | 预览工具栏(非产品) | `.toolbar` | `RADIUS_MD` |
| `radius-sm` | 8px | ~~卡片/按钮/导航项/面板~~ → 矩形(2026-08-22) | ~~`.config-card` `.tool-card` 等~~ | `RADIUS_SM`(已无 UI 使用) |
| `radius-xs` | 6px | ~~输入/下拉/窗口控制钮/编码钮~~ → 矩形(2026-08-22) | ~~`.input-dark` `.select-dark` 等~~ | `RADIUS_XS`(已无 UI 使用) |
| `radius-2xs` | 4px | ~~代码标签/类别标签~~ → 矩形(2026-08-22) | ~~`.code-tag` `.cat-tag`~~ | `RADIUS_2XS`(已无 UI 使用) |

---

## 4. 间距 Spacing

| Token | 值 | 用途 | 场景 |
|-------|-----|------|------|
| `space-4` | 4px | 微调(导航项内 gap) | `.nav-item` gap |
| `space-6` | 6px | 按钮组/窗口控制 gap | `.btn-bar` 组、`.win-controls` |
| `space-7` | 7px | 状态胶囊内 gap | `.server-monitor` |
| `space-8` | 8px | 小间距/padding | 侧栏 padding、chips gap |
| `space-10` | 10px | 卡片组 gap/标题行下距 | `.field-grid` `.tool-grid` gap、`.row-top` margin-bottom |
| `space-12` | 12px | 标准内边距 | `.rec-panel` padding、输入框 padding |
| `space-14` | 14px | 分栏 gap/状态胶囊上距 | `.launch-split` gap、`.server-monitor` margin-top |
| `space-16` | 16px | 卡片内边距/栏内边距 | `.config-card` `.tool-card` padding、`.titlebar` padding |
| `space-20` | 20px | 内容区内边距 | `.content` padding |
| `space-24` | 24px | 大间距 | 昵称上距、启动按钮上距、body padding |
| `space-36` | 36px | 主页卡片横向 padding | `.launcher-card` padding 横 |
| `space-48` | 48px | 主页卡片底部 padding | `.launcher-card` padding 底 |

---

## 5. 尺寸/布局常量 (Layout)

| Token | 值 | 用途 | 场景 | Flet |
|-------|-----|------|------|------|
| `win-launcher` | 360×510 | 主页窗口 | `.window-launcher` | `WIN_LAUNCHER` |
| `win-edit` | 784×600 | 编辑页窗口 | `.window-edit` | `WIN_EDIT` |
| `h-titlebar` | 56px | 标题栏高度 | `.titlebar` `.edit-titlebar` | `H_TITLEBAR` |
| `h-statusbar` | 64px | 状态栏高度 | `.statusbar` | `H_STATUSBAR` |
| `w-sidebar` | 96px | 编辑页导航栏宽 | `.sidebar` | `W_SIDEBAR` |
| `h-nav-item` | 80px | 导航项高 | `.nav-item` | `H_NAV_ITEM` |
| `s-avatar` | 100px | 头像直径 | `.avatar` | `S_AVATAR` |
| `s-btn-launch` | 110px | 启动按钮直径 | `.btn-launch` | `S_BTN_LAUNCH` |
| `h-input` | 40px | 输入框/下拉框高 | `.input-dark` `.select-dark` | `H_INPUT`(flet 实机 48, 字段卡内 TextField 用默认高 ~63px、Dropdown 用 64 匹配) |
| `h-btn-bar` | 34px | 顶栏按钮高 | `.btn-bar` | `H_BTN_BAR` |
| `h-btn-run` | 32px | 运行按钮高 | `.btn-run` | `H_BTN_RUN` |
| `w-btn-win` | 28px | 窗口控制钮 | `.win-btn` | `W_BTN_WIN` |
| `s-dot` | 8px | 状态圆点直径 | `.server-dot` | `S_DOT` |
| `w-divider-v` | 1px | 竖向分割线 | `.divider-v` | (ft.VerticalDivider) |
| `s-crop-canvas` | 480px | 裁剪画布边长 | `.crop-canvas` | `S_CROP_CANVAS` |
| `s-crop-handle` | 14px | 裁剪把手边长 | `.crop-handle` | `S_CROP_HANDLE` |
| `crop-min` | 32px | 裁剪框最小边长 | JS `CROP_MIN` | `CROP_MIN` |
| `s-preview-avatar` | 96px | 头像预览直径 | `.preview-avatar` | `S_PREVIEW_AVATAR` |
| `w-avatar-side` | 200px | 修改头像右栏宽 | `.avatar-side` | `W_AVATAR_SIDE` |
| `h-btn-av` | 36px | 头像操作按钮高 | `.btn-av` | `H_BTN_AV` |

---

## 6. 字体族 Font Families

| Token | 字体栈 | 用途 |
|-------|--------|------|
| `font-cn` | `HarmonyOS Sans SC`(400/500/700/800) → 回退 Microsoft YaHei | 全部界面文字 |
| `font-mono` | `JetBrains Mono`(400/700) → 回退 Consolas | 代码键名、启动参数、版本号、人数 |

> 鸿蒙字体 woff2 本地自包含于 `docs/fonts/sc/`(免费商用);Flet 版回退 Microsoft YaHei 或随包打包。
