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
| `bg-input` | 输入控件底 | `rgba(0,0,0,0.2)` | 输入框/下拉框背景 | `var(--bg-input)` | `COL_BG_INPUT` |
| `bg-ghost` | 幽灵底(白4%) | `rgba(255,255,255,0.04)` | 服务器状态胶囊、chip 默认底、编码切换组底 | `var(--bg-ghost)` | `COL_BG_GHOST` |
| `bg-ghost-2` | 幽灵底(白3%) | `rgba(255,255,255,0.03)` | 工具栏按钮底、卡片 hover 底 | `var(--bg-ghost-2)` | `COL_BG_GHOST_2` |
| `bg-ghost-3` | 幽灵底(白2%) | `rgba(255,255,255,0.02)` | 推荐项面板底、滚动条轨道 | `var(--bg-ghost-3)` | `COL_BG_GHOST_3` |
| `page-bg` | 预览页面底(非产品) | `#05060a` | HTML 预览 body 底色, 不进产品 | `var(--page-bg)` | (无) |
| `toolbar-bg` | 预览工具栏底(非产品) | `#0a0b10` | HTML 预览工具栏, 不进产品 | `var(--toolbar-bg)` | (无) |

### 1.2 品牌色 (Brand, 矢车菊蓝系)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `brand` | 品牌主色 | `#6495ED` | 启动按钮、保存按钮、运行按钮、激活导航、输入 focus、编码激活 | `var(--brand)` | `COL_BRAND` |
| `brand-hover` | 主色 hover | `#4F7FE0` | 主按钮悬停、启动中态 | `var(--brand-hover)` | `COL_BRAND_HOVER` |
| `brand-light` | 主色浅 | `#9DB9F3` | 版本徽章字、头像占位字、chip 已添加字、类别标签字 | `var(--brand-light)` | `COL_BRAND_LIGHT` |
| `brand-soft` | 主色柔 | `#8FB1F0` | 激活导航图标/文字 | `var(--brand-soft)` `var(--blue-light)` | `COL_BRAND_SOFT` |
| `brand-bg-10` | 主色底 10% | `rgba(100,149,237,0.1)` | 导航激活底 | `var(--brand-bg-10)` | `COL_BRAND_BG_10` |
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
| `hover-winbtn` | 窗口按钮 hover | `rgba(255,255,255,0.08)` | `.win-btn:hover` `.chip:hover` | 窗口按钮/chip 悬停提亮 | `COL_WINBTN_HOVER`(浅色 slate 8%) |
| `hover-scrollbar` | 滚动条 hover | `rgba(255,255,255,0.2)` | `.content::-webkit-scrollbar-thumb:hover` | 滚动条滑块悬停 | (未逐态实现, thumb 单色) |
| `shadow-window` | 窗口投影 | `0 24px 80px rgba(0,0,0,0.6)` | `.window` | 窗口浮起投影 | `SHADOW_WINDOW` |
| `shadow-btn` | 按钮投影 | `0 2px 8px rgba(0,0,0,0.35)` | `.btn-launch` | 按钮常态投影 | `SHADOW_BTN` |
| `shadow-btn-hover` | 按钮投影 hover | `0 4px 12px rgba(0,0,0,0.4)` | `.btn-launch:hover` | 按钮悬停投影 | `SHADOW_BTN_HOVER` |
| `float-shadow` | 浮层投影 | `0 8px 24px rgba(0,0,0,0.4)` | `.dd-menu` `.server-panel` `.menu-panel` | 下拉/悬停面板/菜单浮层投影 | `SHADOW_FLOAT`(浅 `0 8px 24px rgba(30,41,59,0.16)`) |
| `dialog-shadow` | 弹窗投影 | `0 16px 48px rgba(0,0,0,0.5)` | `.form-dialog` | 表单弹窗投影 | (AlertDialog 引擎默认, 未逐值实现) |

> ⚠ 收编后 Flet 实现中**禁止再出现** `#4F7FE0`/`#10b981` 字面量,统一引用 `COL_BRAND_HOVER`/`COL_OK`。

### 1.7 裁剪相关 (Crop, 2026-08-23 修改头像页新增)

> 另有 v2.3.1 三轮新增两个材质令牌 (登记于 CSS/flet):
> `card-shadow` 卡片柔影 — 深 `0 2px 10px rgba(0,0,0,0.25)` / 浅 `0 2px 10px rgba(30,41,59,0.06)`, Flet `SHADOW_CARD`;
> `home-wash` 主页品牌氛围垫层 — 深 `rgba(100,149,237,0.07)` / 浅 `rgba(100,149,237,0.06)`, radial 椭圆置于主页内容区底层 (非发光)

| Token | 语义名 | 色值 | 用途 | HTML | Flet |
|-------|--------|------|------|------|------|
| `crop-canvas-bg` | 裁剪画布底 | `#0a0b10` | 裁剪区画布背景(比 bg-deep 更深) | (CSS 内联) | `COL_CROP_CANVAS_BG` |
| `crop-mask` | 裁剪遮罩 | `rgba(0,0,0,0.55)` | 裁剪框外遮罩、头像 hover 遮罩(avatar-hint) | (CSS 内联) | `COL_CROP_MASK` |
| `crop-grid` | 裁剪九宫格线 | `rgba(255,255,255,0.25)` | 裁剪框内九宫格线 | (CSS 内联) | `COL_CROP_GRID` |

> 裁剪把手白边 `#ffffff` 复用 `text-primary`(`COL_TEXT_PRIMARY`),不单列。

### 1.8 浅色主题 (v2.3.1 收编, v2.3.0 起存在于 Flet)

> 原则: 换的只是底色/文字/边框色阶; **品牌主色族(#6495ED 系)、功能色、半透明主色底(brand-bg-10/15/18/20)、focus-ring、launch-*、crop-mask/crop-grid、阴影色之外的对象深浅共用**。
> 事实源: 本表与 `preview v1.html` 的 `html[data-scheme="light"]` 块、`flet_app/theme.py` `_LIGHT` 三方双向一致。
> Flet 消费铁律: 颜色一律 `theme.COL_X` 属性动态访问(from-import 会冻结深色值, set_scheme 换装后不可见)。

| Token | 深色值 | 浅色值 | 说明 |
|-------|--------|--------|------|
| `bg-deep` | `#0c0e14` | `#eef1f8` | 浅灰蓝纸面 |
| `bg-main` | `#0f1117` | `#f6f8fc` | 内容区 |
| `bg-card` | `#161922` | `#ffffff` | 纯白卡片 |
| `bg-card-2` | `#1e293b` | `#e3eaf6` | |
| `bg-sidebar` | `#11141d` | `#f0f3fa` | |
| `bg-input` | `rgba(0,0,0,0.2)` | `rgba(30,41,59,0.05)` | slate 5% |
| `bg-ghost` | 白4% | `rgba(30,41,59,0.04)` | slate 4% |
| `bg-ghost-2` | 白3% | `rgba(30,41,59,0.03)` | |
| `bg-ghost-3` | 白2% | `rgba(30,41,59,0.02)` | |
| `brand-light` | `#9DB9F3` | `#3d63c9` | 浅色底下改深品牌保对比 |
| `brand-soft` | `#8FB1F0` | `#5a7fd6` | |
| `text-primary` | `#ffffff` | `#1e293b` | 深墨字阶 (slate) |
| `text-secondary` | `#e2e8f0` | `#334155` | |
| `text-muted` | `#a0aec0` | `#64748b` | |
| `text-dim` | `#64748b` | `#94a3b8` | |
| `text-disabled` | `#6b7280` | `#a8b3c4` | |
| `border-subtle` | 白5% | `rgba(30,41,59,0.05)` | |
| `border-visible` | 白10% | `rgba(30,41,59,0.12)` | |
| `btn-bar-hover` | 白7% | `rgba(30,41,59,0.07)` | |
| `crop-canvas-bg` | `#0a0b10` | `#e6e9f1` | |
| `switch-inactive-track` | `#2A2730` | `#c7d0de` | |
| `switch-inactive-thumb` | `#8A8494` | `#ffffff` | |
| 阴影(全部) | 黑色系 | slate 灰低透明 | `SHADOW_*` 换装时整体重建 (`_rebuild_shadows`) |
| hover-winbtn / hover-chip | 白8% | slate 8% | |
| scroll-thumb(-hover) | 白10%/20% | slate 15%/25% | Flet 侧暂用原生滚动条 |

---

## 2. 字号 Font Sizes

| Token | 值 | 用途 | 场景 | Flet |
|-------|-----|------|------|------|
| `font-44` | 44px | 启动按钮图标 | `.btn-launch .ic` | `FONT_44` |
| `font-36` | 36px | 头像占位首字 | `.avatar span` | `FONT_36` |
| `font-24` | 24px | 主页大昵称 (700) | `.nickname` | `FONT_24` |
| `font-20` | 20px | 页面标题 (700) | `.page-head h2` | `FONT_20` |
| `font-20-ic` | 20px | 导航图标 | `.nav-item .ic` | `FONT_20_IC` |
| `font-18` | 18px | 编辑页窗口标题 (700, 如「修改头像」) | `.edit-titlebar span` | `FONT_18`(主页标题栏产品名 v2.3.1 二轮改 15px=FONT_15, 5 钮布局防换行) |
| `font-16` | 16px | 启动命令输入框 (mono) | `.launch-split textarea` | `FONT_16` |
| `font-15` | 15px | 在线人数/在线标签/状态图标 | `.sm-count` `.sm-label` | `FONT_15` |
| `font-14` | 14px | 卡片标题/工具名 (700)、按钮图标、下拉框值 | `.card-title` `.tool-name` `.select-dark` `.btn-bar .ic` | `FONT_14` |
| `font-15` | 15px | 输入框值(字段卡) | `.input-dark` | (并入 FONT_15) |
| `font-13` | 13px | 下拉框值 | `.select-dark` | `FONT_13` |
| `font-12` | 12px | 描述/按钮文字/状态消息 | `.card-desc` `.btn-bar` `.status-msg` `.tool-status` | `FONT_12` |
| `font-11` | 11px | 标签/提示/风险/chips | `.rec-title` `.risk-tag` `.chip` `.enc-btn` | `FONT_11` |
| `font-10` | 10px | 徽章/类别/导航字 | `.version-tag` `.cat-tag` `.nav-item span` | `FONT_10` |

> 数字命名直接对应 px 值,新增字号须走 design-system.md 评审并登记。

---

## 3. 圆角 Radius

> **v2.3.1 二轮用户决策 (2026-08-30): 推翻 2026-08-22 矩形化, 改 Win11 圆角档位**。
> 窗口外壳走 Win11 原生 DWM 圆角 (系统级渲染无黑边; 失败自动回退矩形并留档);
> 卡片/面板 8px, 控件 4px; 正圆/胶囊保留。

| Token | 值 | 用途 | 场景 | Flet |
|-------|-----|------|------|------|
| `radius-window` | DWM 系统值 (~8px) | 窗口外壳 (系统控制, 不可自定数值) | 真实窗口 | ctypes `DwmSetWindowAttribute`, 失败回退 0 |
| `radius-lg` | 8px | 卡片/工具卡/面板/弹窗/菜单/悬停面板 | `.config-card` `.tool-card` `.rec-panel` `.form-dialog` `.menu-panel` `.server-panel` | `RADIUS_CARD`(8) |
| `radius-xs` | 4px | 按钮/输入框/下拉/chip/标签/窗口控制钮/导航项/提示条 | `.btn-*` `.input-dark` `.select-dark` `.chip` `.code-tag` `.cat-tag` `.win-btn` `.nav-item` `.hint-bar` | `RADIUS_CTRL`(4) |
| `radius-pill` | 999px | 胶囊: 版本徽章/状态胶囊/开关 | `.version-tag` `.server-monitor` `.switch-track` | `RADIUS_PILL` |
| `radius-circle` | 50% | 头像/启动按钮/滑块 | `.avatar` `.btn-launch` `.thumb` | `RADIUS_CIRCLE` |
| `radius-md` | 12px | 预览工具栏(非产品) | `.toolbar` | `RADIUS_MD` |

> 历史: v1 圆角(16/8/6/4) → 2026-08-22 矩形化 → v2.3.1 二轮 Win11 档位(8/4)。
> 旧常量 `RADIUS_LG/SM/XS/2XS` 由 `RADIUS_CARD/RADIUS_CTRL` 取代 (theme.py)。

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
| `win-launcher` | 360×510 | 主页窗口 (v2.3.1 二轮回归 510: 直连/练枪移出卡片, 悬停面板为覆盖层) | `.window-launcher` | `WIN_LAUNCHER` |
| `win-edit` | 784×600 | 编辑页窗口 | `.window-edit` | `WIN_EDIT` |
| `h-titlebar` | 56px | 标题栏高度 | `.titlebar` `.edit-titlebar` | `H_TITLEBAR` |
| `h-statusbar` | 64px | 状态栏高度 | `.statusbar` | `H_STATUSBAR` |
| `w-sidebar` | 96px | 编辑页导航栏宽 | `.sidebar` | `W_SIDEBAR` |
| `h-nav-item` | 80px | 导航项高 | `.nav-item` | `H_NAV_ITEM` |
| `s-avatar` | 100px | 头像直径 | `.avatar` | `S_AVATAR` |
| `s-btn-launch` | 110px | 启动按钮直径 | `.btn-launch` | `S_BTN_LAUNCH` |
| `h-input` | 40px | 输入框/下拉框高 (独立场景: 弹窗/超时行) | `.input-dark` `.select-dark` | `H_INPUT`(flet 实机 48; 字段卡内 **48px + 字 15px** — v2.3.1 二轮用户反馈定稿: 64px 框配 12-14px 字头重脚轻, 40px 曾被否决, 48 为平衡值) |
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

## 7. 动效 Motion (v2.3.1 三轮新增)

| Token | 值 | 用途 |
|-------|-----|------|
| `motion-fast` | 150ms | 面板/菜单/弹窗进出、遮罩淡入 |
| `motion-normal` | 220ms | 视图切换、换装淡入 |
| `group-in` 时长 | 180ms | 编辑页分组切换 (一次性, 可并入 fast 档) |
| `ease-standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | 全部动效唯一缓动 |

> 纪律: 动画只动 opacity/transform (offset/scale); 循环动画每页 ≤1 个;
> 一律引用本表令牌, 禁止散落裸数值; 实机卡顿就地降级为即时切换 (rules.md §4.7)。
> 现役动画清单: 视图入场 view-in / 分组 group-in / 面板 panel-in(-center) / 弹窗 dialog-in+mask-in /
> 在线点 dot-breathe (唯一循环) / 启动中火箭 rocket-nudge (有限 2 次) / chip 勾选 chip-pop (有限 1 次) /
> 下拉箭头聚焦旋转 (transform 过渡 motion-fast, v2.3.1 四轮)。原生 select 系统弹出列表不属产品动效。
>
> **Flet 落地映射与降级留档 (v2.3.1 批次③/④, 2026-08-30)**:
> - 保留: dot-breathe = `Container.animate_opacity` 1s 往返 (纯 opacity); rocket-nudge = `_icon_box.rotate`
>   有限 6 步 (offset 分量删去); chip-pop = `animate_scale` 0.94→1; 下拉展开 = 引擎弹出层过渡 (~150ms)。
> - 降级为即时切换: view-in / group-in / panel-in / 换装淡入 (opacity+offset 两段) 与 hover 位移
>   (按钮上移 -2px / 卡片右移 +4px) — flet 0.86.5 实机上 `offset` 位移动画反复破坏布局
>   (内容区空白/控件叠错位, 多轮复现), 按 rules §4.6 就地降级; 弹窗 dialog-in/mask-in 用引擎默认过渡。
>   offset 类动效待 flet 升级后再试。

---

## 6. 字体族 Font Families

| Token | 字体栈 | 用途 |
|-------|--------|------|
| `font-cn` | `HarmonyOS Sans SC`(400/500/700/800) → 回退 Microsoft YaHei | 全部界面文字 |
| `font-mono` | `JetBrains Mono`(400/700) → 回退 Consolas | 仅真代码: 启动命令输入框、启动参数 chips、IP:端口/CFG 数值输入 (v2.3.1 三轮收窄: 版本号/人数/kicker/键名已改 font-cn) |

> 鸿蒙字体 woff2 本地自包含于 `docs/fonts/sc/`(免费商用);Flet 版回退 Microsoft YaHei 或随包打包。
