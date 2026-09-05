# 设计系统组件库 — 汤圆启动器 Rev.Ini 编辑器

> 唯一事实源: `docs/preview v1.html`(HTML 是唯一事实源,本文件随它维护)
> 配套: `tokens.md`(令牌字典)/ `rules.md`(编码约束)
> 维护义务: 组件变更必须同步本文件 + tokens.md + rules.md(见 rules.md §同步义务)
> 命名: 组件语义名 = HTML class 根名;Flet 实现落点 `flet_app/components/ui/`(见 rules.md)
> 例外: Flet 原生基础控件(ft.Text/Container/TextField/Dropdown/Switch/Row/Column 等)**不受"只能用 ui 组件"限制**(rules.md §原生豁免)

---

## 组件索引

| # | 组件 | HTML 类 | 所在视图 |
|---|------|---------|---------|
| 1 | 窗口外壳 Window | `.window` | 两视图 |
| 2 | 标题栏 TitleBar | `.titlebar` | 主页 |
| 3 | 版本徽章 VersionTag | `.version-tag` | 主页 |
| 4 | 窗口控制按钮 WinBtn | `.win-btn` | 两视图 |
| 5 | 头像 Avatar | `.avatar` | 主页 |
| 6 | 昵称 Nickname | `.nickname` | 主页 |
| 7 | 服务器状态胶囊 ServerMonitor | `.server-monitor` | 主页 |
| 8 | 启动按钮 LaunchButton | `.btn-launch` | 主页 |
| 9 | 编辑页标题栏 EditTitleBar | `.edit-titlebar` | 编辑页 |
| 10 | 顶栏按钮 BarButton | `.btn-bar` | 编辑页 |
| 11 | 侧栏导航 SidebarNav | `.sidebar` `.nav-item` | 编辑页 |
| 12 | 页头 PageHead | `.page-head` | 编辑页 |
| 13 | 字段网格 FieldGrid | `.field-grid` | 常用设置 |
| 14 | 配置卡片 ConfigCard | `.config-card` | 常用设置 |
| 15 | ~~代码键名标签 CodeTag~~ → 已删 (v2.3.1 三轮, rules §4.3 落实; 需要时走 tooltip) | — | — |
| 16 | 输入框 InputDark | `.input-dark` | 编辑页 |
| 17 | 下拉框 Dropdown | `.dd` `.dd-menu` | 常用设置/CFG |
| 18 | 推荐项 Chip | `.chips` `.chip` | 加载器 |
| 19 | 推荐面板 RecPanel | `.rec-panel` | 加载器 |
| 20 | 启动分栏 LaunchSplit | `.launch-split` | 加载器 |
| 21 | 工具卡片 ToolCard | `.tool-card` | 修复工具 |
| 22 | 类别标签 CatTag | `.cat-tag` | 修复工具 |
| 23 | 风险标签 RiskTag | `.risk-tag` | 修复工具 |
| 24 | 运行按钮 RunButton | `.btn-run` | 修复工具 |
| 25 | 工具状态 ToolStatus | `.tool-status` | 修复工具 |
| 26 | 状态栏 StatusBar | `.statusbar` | 编辑页 |
| 27 | 编码切换 EncGroup | `.enc-group` `.enc-btn` | 编辑页 |
| 28 | 开关 Switch | `.switch` | 预留 |
| 29 | 头像修改提示 AvatarHint | `.avatar-hint` | 主页 |
| 30 | 裁剪画布 CropCanvas | `.crop-canvas` | 修改头像 |
| 31 | 裁剪框 CropBox | `.crop-box` `.crop-handle` | 修改头像 |
| 32 | 头像预览 PreviewAvatar | `.preview-avatar` | 修改头像 |
| 33 | 头像操作按钮 AvatarActionBtn | `.btn-av` | 修改头像 |
| 34 | 服务器悬停面板 ServerPanel | `.server-panel` `.sp-row` | 主页 |
| 35 | ~~副启动按钮 AltLaunchBtn~~ → 练枪并入标题栏 WinBtn (v2.3.1 二轮) | — | — |
| 36 | 主题菜单 ThemeMenu | `.menu-panel` `.menu-item` | 主页/编辑页 |
| 37 | 表单弹窗 FormDialog | `.dialog-mask` `.form-dialog` | 通用 |
| 38 | 提示条 HintBar | `.hint-bar` | CFG 配置 |

> **Flet 原生豁免标注 (deep-review 7轮 F4 定稿)**: 以下组件在 Flet 中由原生控件直接表达
> (rules.md §1.4 原生豁免, 不需要也不应封装成 ui.* 组件, 页面直用):
> - #1 Window → `ft.Container`(圆角裁切+边框, main.py 顶层容器)
> - #2 TitleBar / #9 EditTitleBar → `ft.Row` + `ui.win_btn`/`ft.OutlinedButton`/`ft.FilledButton` 组合
> - #10 BarButton → `ft.OutlinedButton`/`ft.FilledButton`(样式经 ButtonStyle)
> - #11 SidebarNav → `ft.NavigationRail`(indicator 透明, 选中色走 selected_*_text_style)
> - #27 EncGroup → `ui.enc_group`(自绘, 2026-08 从 SegmentedButton 迁出, 见 #27)
> - #28 Switch → `ft.Switch`
> 其余 #3-#8/#12-#26 已全部实现为 `ui.*` 组件(flet_app/components/ui.py)。

---

## 组件详述

### 1. 窗口外壳 Window

- **用途**: 应用窗口容器,承载标题栏 + 内容;**Win11 圆角边缘**(v2.3.1 二轮用户决策,推翻 2026-08-22 矩形化 — 窗口走 Win11 原生 DWM 路线 `DwmSetWindowAttribute(Windows_DWM_WINDOW_CORNER_PREFERENCE)`, 系统级渲染无黑边;失败自动回退矩形并留档)
- **Props**:
  - `size`: `launcher`(360×510, v2.3.1 二轮回归)/ `edit`(784×600)
  - `label`: 窗口标注文本(仅预览用)
- **何时用**: 两个主视图各一个
- **何时不用**: 弹窗/对话框不套窗口外壳
- **Flet**: `ft.Window`(frameless, 深色背景 `bg-deep`) + ctypes DWM 圆角 + `ft.Row`/`ft.Column` 内容

### 2. 标题栏 TitleBar(主页)

- **用途**: 主页顶部栏:左=版本徽章+产品名(15px, 5 钮布局防换行),右=窗口控制(练枪/主题/配置/最小化/关闭)
- **Props**: 无(固定结构)
- **何时用**: 仅主页
- **何时不用**: 编辑页用 EditTitleBar(组件 9)
- **Flet**: `ft.Container`(h=56, bg `bg-deep`, 下边框 `border-subtle`)内 Row

### 3. 版本徽章 VersionTag

- **用途**: 显示客户端版本号(如 v1.35.4.2)
- **Props**: `text`
- **何时用**: 主页标题栏左端
- **何时不用**: 不放正文/卡片内
- **Flet**: `ft.Container`(pill, bg `brand` 20% 底, border `border-brand`, text `brand-light` 10px 700, font-cn — v2.3.1 三轮去 mono)

### 4. 窗口控制按钮 WinBtn

- **用途**: 无边框图标按钮:练枪(准星, 仅主页)/主题(月亮/太阳, 随当前方案切换)/配置(齿轮, 仅主页)/最小化/关闭
- **Props**: `icon`(i-crosshair/i-settings/i-minus/i-x; 主题=i-moon/i-sun), `variant`(normal/close)
- **何时用**: 标题栏右上角;练枪/配置按钮仅主页;主题按钮=主页+编辑页(修改头像页不放)
- **何时不用**: 不用于主操作(主操作用 BarButton/RunButton);练枪点击 = `on_launch_click(practice=True)` 直接进本地练枪图
- **Flet**: `ft.IconButton`(28×28, 圆角 4px (Win11 控件档, v2.3.1), hover bg `hover-winbtn`;close hover bg `status-red`)

### 5. 头像 Avatar

- **用途**: 显示玩家头像;无头像文件时显示昵称首字
- **Props**: `image`(可选), `fallbackText`(昵称首字)
- **何时用**: 主页昵称上方
- **何时不用**: 编辑页不出现
- **Flet**: `ft.Container`(100×100 圆, bg `bg-card-2`, 边框 2px `border-visible`, overflow clip)+ 首字 Text(36px 700 `brand-light`)

### 6. 昵称 Nickname

- **用途**: 主页玩家昵称,单行省略
- **Props**: `text`, `size`(默认 18,主页大昵称 24)
- **何时用**: 主页昵称
- **何时不用**: 编辑页字段(用 ConfigCard)
- **Flet**: `ui.nickname()`(组件库实现;单行 + ELLIPSIS 省略,防超长昵称撑爆固定 360×510 布局)

### 7. 服务器状态胶囊 ServerMonitor

- **用途**: 显示**主服**(常用设置 ConnectServer 目标)的在线状态 + 人数胶囊;右侧淡 chevron 提示可悬停展开 ServerPanel(#34)
- **Props**: `status`(`online`/`offline`), `label`(在线/离线/服名), `count`(人数,offline 时隐藏)
- **何时用**: 主页昵称下方;悬停 = ServerPanel 展开触发器
- **何时不用**: 编辑页/头像页;无 ConnectServer 配置时只显示「离线」不显示人数
- **⚠ 数据红线**: 人数必须来自状态 API (`cs.suchitems.top/api/status`) 真实查询,离线禁止展示人数
- **Flet**: `ft.Container`(pill, bg `bg-ghost`, border `border-subtle`)内 Row: 圆点(8px `status-green`+3px 浅绿晕/离线 `text-dim`)+ 标签(15px **`text-muted`**)+ 人数(15px 600 `text-secondary`, tabular-nums)+ chevron(10px `text-dim`, hover 旋转 180°)。标签用 text-muted 而非 text-dim: 灰字对比度实测偏低,提亮一档保证低亮度屏可读(2026-08 UI 审查落地)

### 8. 启动按钮 LaunchButton

- **用途**: 主页主操作:启动游戏(圆形纯图标)
- **Props**: `state`(idle/launching/running,控制底色与 title), `icon`(默认 i-rocket)
- **何时用**: 主页唯一主按钮
- **何时不用**: 不承载文字;不用作编辑页操作按钮
- **Flet**: `ft.Container`(110×110 圆, bg `brand` → hover `brand-hover` → busy `launch-busy` → done `launch-done`+`launch-glow`, 居中 Icon rocket 44px 白)。启动中态: 火箭图标 rocket-nudge 旋转抖动 0.45s×2 (有限次非循环, v2.3.1 三轮; offset 分量已降级删去, tokens §7)。hover 上移 -2px 已试做并降级 — offset 位移动画实机破坏 Column 布局 (批次④留档), 保留变色+阴影加深
- 交互: 点击后依次 busy(1.5s)→ done(4s)→ 复位;期间防重复点击。UAC 提权流程 (2026-09-05): 弹窗前 tooltip「等待管理员确认…」复用 launching 态, 确认后进「启动中…」统一轮询, 取消复位 idle + 状态栏红字 — 按钮不新增状态档

### 9. 编辑页标题栏 EditTitleBar

- **用途**: 编辑页顶部操作栏:返回/打开cfg文件夹/指定目录/打开文件/保存 + 窗口控制
- **Props**: 无(固定结构)
- **何时用**: 仅编辑页(修改头像页用其变体: 返回+标题, **不放主题按钮** — 裁剪中换装会丢进度)
- **何时不用**: 主页用 TitleBar
- **Flet**: `ft.Container`(h=56, bg `bg-deep`, 下边框 `border-subtle`)内两个 Row(left/right)
- **v2.3.1**: 右侧 win-controls 最左新增主题按钮(WinBtn 变体, 月亮/太阳图标随当前方案)

### 10. 顶栏按钮 BarButton

- **用途**: 编辑页顶部文字按钮(返回/打开/指定/保存)
- **Props**: `icon`, `label`, `variant`(normal/primary)
- **何时用**: 编辑页标题栏;primary 变体用于「保存」
- **何时不用**: 不作为内容区按钮(内容区用 RunButton);不带图标不放这里
- **Flet**: `ft.OutlinedButton`(h=34, 圆角 4px (Win11 控件档, v2.3.1), bg `bg-ghost-2` → hover `hover-btnbar`, border `border-subtle` → hover `border-visible`, 字 12px 500 `text-secondary`)→ primary: `ft.FilledButton`(h=34, bg `brand` 白字 700)。灰底细边框低调化,保存实心突出主操作(2026-08 UI 审查落地, HTML `.btn-bar` 同款)

### 11. 侧栏导航 SidebarNav

- **用途**: 编辑页分组导航(常用设置/加载器/修复工具/CFG 配置)
- **Props**: `items`(icon+label 列表), `activeIndex`
- **何时用**: 编辑页左侧固定栏
- **何时不用**: 主页无导航;共 4 项(2026-08-23 起, CFG 配置图标=文档)
- **Flet**: `ft.NavigationRail`(min_width=96, bg `bg-sidebar`, 右边框 `border-subtle`;激活项: indicator `brand` 10% 半透明底 + 圆角 8 + 图标/文字 `brand-soft`)。HTML 的左 3px 主色指示条 NavigationRail 无法表达,以半透明 indicator 底近似——实心 indicator 会盖住图标(用户实机反馈 2026-08),10% 半透明只提亮背景不遮图标(2026-08 UI 审查落地)

### 12. 页头 PageHead

- **用途**: 编辑页各分区页头:标题 + 描述 (v2.3.1 三轮: 代码注释 kicker 已删 — 典型 web coding 味装饰)
- **Props**: `title`, `desc`
- **何时用**: 每个编辑页分区顶部(常用设置/加载器/修复工具)
- **何时不用**: 主页
- **Flet**: `ui.page_head()`(组件库实现, deep-review 7轮 F4 从页面内联抽取;padding 18/10/18/14)

### 13. 字段网格 FieldGrid

- **用途**: 双列字段卡片网格,奇数个末行单卡
- **Props**: `fields`, `buildRow`(单卡构建回调), `spacing`, `header`(可选页头)
- **何时用**: 编辑页字段分区
- **何时不用**: 工具页(2×2 用 ToolCard)
- **Flet**: `ui.field_grid()`(组件库实现, deep-review 7轮 F4 抽取;ListView + 双列 Row expand, 等高靠内容统一)

### 14. 配置卡片 ConfigCard

- **用途**: 设置项容器:标题行(标题)+ 描述 + 输入控件 (v2.3.1 三轮: CodeTag 已删)
- **Props**: `title`, `desc`, `control`(Input/Select), `desc_lines`(>0 时描述固定行高容器,双列等高用 2)。标题/描述/控件文字**左对齐** (v2.3.1 曾试水平居中, 用户否决回退 — **不要再提居中**)
- **何时用**: 常用设置字段
- **何时不用**: 工具卡用 ToolCard;双列内 hover 不右移
- **Flet**: `ui.config_card()`(padding 16, 圆角 8px (Win11 卡片档, v2.3.1), bg `bg-card`, border `border-subtle`, shadow `SHADOW_CARD`;hover bg `bg-ghost-2` + border `border-brand`, 双列内无位移;desc_lines=2 时 desc 容器高 36px)。hover 右移 +4px 已试做并降级 — offset 位移动画在 flet 0.86.5 实机破坏 ListView 内卡片渲染 (批次④留档, tokens §7)

### 15. ~~代码键名标签 CodeTag~~(已删, v2.3.1 三轮)

- rev.ini 键名是对用户无价值的内部细节 (rules.md §4.3 红线), 也是"web coding 味"的主要来源之一, 从 UI 移除;
  编号保留防错位。极少数需要键名的场景用控件 tooltip 呈现, 不占版面。

### 16. 输入框 InputDark

- **用途**: 单行文本输入(昵称/标签/端口等);`mono` 变体用于 IP:端口
- **Props**: `value`, `placeholder`, `mono`, `multiline`, `height`, `fontSize`, `width`(字段卡内 236), `onChange`, `maxLength`(组件内手动截断, 见 Flet 注), `textAlign`
- **何时用**: 需文本输入的字段
- **何时不用**: 选项类用 SelectDark;布尔用 Switch
- **Flet**: `ui.input_dark()`(组件库实现;圆角 4px (Win11 控件档, v2.3.1), bg `bg-input`, border `border-visible`, focus border `brand`;textarea: multiline 多行 16px mono;**字段卡内高 48px + 字 15px**(v2.3.1 定稿: 64px 框小字头重脚轻, 用户否决过 40px), 弹窗/独立场景 40px 设计高);**maxLength 不传引擎** — flet 0.86.5 引擎设限必自带 "0/32" 计数器(TextField 无 counter_text 参数, 藏不掉)且误传即启动崩溃, 由组件在 onChange 内截断, 上限语义不变 (2026-09-05)

### 17. 下拉框 Dropdown(v2.3.1 四轮重构, 原生 select/Dropdown 弃用)

- **用途**: 选项下拉(界面语言/段位/CFG 枚举)。**收起态** = InputDark 同款 (同宽 236/同高 48/同边框圆角, 箭头距右缘 8px); **展开态** = 应用同款菜单: `bg-card` 底 + `border-visible` + 圆角 8 + float-shadow, 选中项 `brand-bg-10` 底 + `brand-soft` 字 600, 悬停 `bg-ghost`
- **Props**: `options`([(值, 标签)]), `selected`, `onSelect`, `width`, `height`
- **何时用**: 需选项的字段
- **何时不用**: 文本输入用 InputDark;布尔用 Switch
- **动效**: 展开 = panel-in 150ms; 箭头展开旋转 180° + 变 `brand`; 外点/选中即收
- **Flet**: `ui.select_dark()` 重构为自绘 (`ft.PopupMenuButton` + 自定义 content/items — 引擎弹出层只承担定位/外点关闭/超长滚动, 视觉全部自绘; 字段卡在 ListView 内, 纯 Stack 面板会被视口裁切、被后续行卡片盖住, 故走引擎 overlay 路线; 展开=引擎弹出过渡 ~150ms 近似 panel-in) — 原生 ft.Dropdown 的弹出层是引擎样式, 与设计脱节且曾报圆角窗口裁切问题, 弃用; 菜单超 6 项加滚动

### 18. 推荐项 Chip

- **用途**: 可点击标签;点击切换 added 态(前缀 ✓)。**与启动命令双向联动**(v2.3.1 三轮定稿, 与实装同语义): 勾选 = 启动命令末尾追加该参数行, 取消 = 从启动命令移除该行; chip 的 added 态以参数是否存在于命令中为准。**勾选弹跳** (v2.3.1 四轮): 切换时 chip-pop scale 0.94→1 (160ms, 有限次非循环)
- **Props**: `label`, `added`(bool)
- **何时用**: 加载器推荐启动项(右栏竖排)
- **何时不用**: 不作为普通信息标签(用 CatTag/RiskTag)
- **Flet**: `ft.Container`(圆角 4px (Win11 控件档, v2.3.1), border `border-visible`, bg `bg-ghost`;added: bg `brand` 18% + border `border-brand` + 字 `brand-light`;11px, mono 仅限启动参数语义 (v2.3.1 三轮))
- ⚠ 竖排时: 单行省略(width 100%, nowrap + ellipsis + min-width 0),防溢出

### 19. 推荐面板 RecPanel

- **用途**: 加载器右栏容器:「推荐启动项」标题 + 竖排 Chips
- **Props**: `title`, `chips`, `expand`(Row 内分栏比例,LaunchSplit 右栏 2)
- **何时用**: 仅加载器右栏
- **何时不用**: 内容区其他位置
- **Flet**: `ui.rec_panel()`(组件库实现, deep-review 7轮 F4 抽取;padding 12, 圆角 8px (Win11 卡片档, v2.3.1), bg `bg-ghost-3`, border `border-subtle`)

### 20. 启动分栏 LaunchSplit

- **用途**: 启动命令左右分栏(左=textarea 手动输入,右=RecPanel)
- **Props**: `ta`, `rec`, `gapWidth`(默认 14)
- **何时用**: 仅加载器「启动命令」卡
- **何时不用**: 其他字段
- **Flet**: `ui.launch_split()`(组件库实现, deep-review 7轮 F4 抽取;Row expand, 左 ta.expand=3 右 rec.expand=2, 两栏等高)

### 21. 工具卡片 ToolCard

- **用途**: 修复工具条目:顶行(类别+风险|运行按钮)→ 工具名 → 状态
- **Props**: `catTag`, `risk`(低/中/高 或 low/mid/high), `name`, `onRun`, `expand`(2×2 网格等宽);返回 Container 附带 `_run_btn`/`_status` 引用供驱动状态
- **何时用**: 修复工具页
- **何时不用**: 设置字段用 ConfigCard
- **Flet**: `ui.tool_card()`(padding 16, 圆角 8px (Win11 卡片档, v2.3.1), bg `bg-card`, border `border-subtle`;hover border `border-brand`;内部组合 CatTag + RiskTag + RunButton + ToolStatus);2×2 网格行列距均 space-10(tokens.md §4, 2026-09-05 补齐 — 原 ListView 漏传 spacing 两行卡片贴死)

### 22. 类别标签 CatTag

- **用途**: 工具类别(缓存清理/注册表修复/物品库/启动优化)
- **Props**: `text`
- **何时用**: ToolCard 顶行左侧
- **何时不用**: 非工具上下文
- **Flet**: `ft.Container`(圆角 4px (Win11 控件档, v2.3.1), bg `brand` 15%, border `border-brand`, 字 `brand-light` 10px 600)

### 23. 风险标签 RiskTag

- **用途**: 工具风险等级文字
- **Props**: `level`(低/中/高 或 low/mid/high;绿/琥珀/红), `text`(可选覆盖文案)
- **何时用**: ToolCard 顶行类别旁
- **何时不用**: 非工具上下文
- **Flet**: `ui.risk_tag()`(`ft.Text` 11px 600, color `status-green`/`status-amber`/`status-red`;未知 level 回退绿)

### 24. 运行按钮 RunButton

- **用途**: 工具运行触发;运行中禁用 + 图标切 clock + 文字「运行中」
- **Props**: `label`(运行/运行中), `disabled`, `icon`(play/clock)
- **何时用**: ToolCard 顶行右侧
- **何时不用**: 编辑页顶栏操作用 BarButton
- **Flet**: `ft.FilledButton`(h=32, 圆角 4px (Win11 控件档, v2.3.1), bg `brand`, 白字 700 12px;disabled opacity 0.5)

### 25. 工具状态 ToolStatus

- **用途**: 工具运行状态文本(待运行/运行中…/完成/失败)
- **Props**: `state`(idle/running/ok/fail)
- **何时用**: ToolCard 底部
- **何时不用**: 非工具上下文
- **Flet**: `ft.Text`(11px, 右对齐;running=`status-amber`, ok=`status-green`, fail=`status-red`, idle=`text-dim`)

### 26. 状态栏 StatusBar

- **用途**: 编辑页底部:左=状态图标(仅图标)+可选状态消息,右=编码切换
- **Props**: `encSelector`, `statusMsg`(可选 Text,加载/保存错误临时显示;None 时仅图标), `statusIcon`(可选 Icon,调用方持有引用以便错误时切红 ERROR 图标;None 时内部创建默认绿勾)
- **何时用**: 仅编辑页底部
- **何时不用**: 主页不放状态栏(坑位记录);常驻状态文字已删,只留图标
- **Flet**: `ui.status_bar()`(h=64, bg `bg-deep`, 上边框 `border-subtle`)内 Row: 左 Icon(check-circle 15px `status-green`;错误时切 error-outline `status-red`)+ 可选消息,右 EncGroup。常态仅图标: 成功/普通状态不显示文字,错误才显示中文错误消息(2026-08 UI 审查落地)

### 27. 编码切换 EncGroup

- **用途**: ANSI/UTF-8 分段切换
- **Props**: `segments`([(value, label)]), `selected`(当前值), `onChange`(选中回调)
- **何时用**: 状态栏右侧
- **何时不用**: 其他位置
- **Flet**: `ui.enc_group()`(组件库实现, 2026-08 UI 审查落地: 原 ft.SegmentedButton 的 style 只能整体应用、选中/未选中无法分离样式, 亮蓝实心被用户反馈难看 → 自绘 HTML `.enc-group` 结构: ghost 底容器 + 细边框 + 分段按钮(外组 4px / 段内 3px, v2.3.1 Win11 档); 选中段 = `brand` 20% 浅底 + `brand-light` 字 + `border-brand` 边框, 未选中 = 透明 + `text-dim` 字; 11px/600; 与 chip 已添加态/导航激活态同一视觉语言; 2026-08-30 审查起为 `EncGroup` 类, 提供 `selected` property (接受 str/[str], 静默回填不触发 on_change — load_file 按文件实际编码回填显示, 此前裸 Container 上赋值是 no-op, 显示与保存编码脱钩))

### 28. 开关 Switch(预留)

- **用途**: 布尔设置项
- **Props**: `checked`
- **何时用**: 未来布尔字段
- **何时不用**: 当前字段无布尔项(显示头像已删)
- **Flet**: `ft.Switch`(track 40×22 pill, on 时 bg `brand`, thumb 18px 白)

### 29. 头像修改提示 AvatarHint

- **用途**: 头像 hover 时叠加半透明遮罩 + 相机图标,提示头像可点击修改
- **Props**: 无(内部 i-camera 图标)
- **何时用**: 主页头像 hover(头像入口 2026-08-23 新增: 点击进入修改头像页)
- **何时不用**: 无头像修改入口时;编辑页头像不出现
- **Flet**: Avatar 内 `ft.Container`(bg `avatar-hint` 半透明黑, opacity 0 → hover 1)+ 居中 `ft.Icon(camera_alt, 18, white)`

### 30. 裁剪画布 CropCanvas

- **用途**: 修改头像页左栏裁剪区容器,承载原图 + 裁剪框(CropBox)
- **Props**: `image`(原图 src), `cropBox`(CropBox 引用)
- **何时用**: 仅修改头像页
- **何时不用**: 其他视图;图片无裁剪需求时直接 Image
- **Flet**: `ft.Container`(480×480 矩形, bg `crop-canvas-bg`(比 bg-deep 更深), border `border-subtle`, 内 Stack: `ft.Image`(fit=COVER) + CropBox)

### 31. 裁剪框 CropBox

- **用途**: 1:1 方形裁剪框;拖动框体移动、拖动四角缩放、滚轮缩放,外圈半透明遮罩 + 内九宫格线
- **Props**: `size`(边长, 32 ~ 画布边长), `x`/`y`(左上角), `onChange`(裁剪区域变化回调, 驱动预览同步)
- **何时用**: 修改头像页裁剪区
- **何时不用**: 无
- **Flet**: `ft.Container`(方形, border 2px `brand`)+ 四角 handle(14×14 `brand` + 白边, 矩形)+ 九宫格线(1px `crop-grid`) + `ft.GestureDetector`(on_pan_update 移动 / on_scale_update 缩放);遮罩 = 底层半透明 `crop-mask`。⚠ 屏幕坐标 → 原图像素坐标换算需按 cover 缩放反推(见 HTML `applyPreviewTo`)

### 32. 头像预览 PreviewAvatar

- **用途**: 实时预览裁剪结果(96px 圆形),跟随 CropBox 裁剪区域同步
- **Props**: 无(由 CropBox onChange 驱动, 用 background 定位裁剪区域)
- **何时用**: 修改头像页右栏
- **何时不用**: 主页头像用 Avatar(组件 5)
- **Flet**: `ft.Container`(96×96 圆, border 2px `border-visible`, 内 `ft.Image` 按裁剪区域 clip)

### 33. 头像操作按钮 AvatarActionBtn

- **用途**: 修改头像页操作按钮(选择图片/恢复默认/取消/保存)
- **Props**: `label`, `icon`, `variant`(primary/ghost/normal)
- **何时用**: 修改头像页右栏;primary=选择图片/保存(主操作), ghost=恢复默认, normal=取消
- **何时不用**: 顶栏操作用 BarButton;工具运行用 RunButton;**主页练枪按钮用 AltLaunchBtn(#35), 不再借用本组件**(v2.3.1 收编修正)
- **Flet**: primary=`ft.FilledButton`(h=36 圆角4px, bg `brand` 白字 700)/ ghost=`ft.OutlinedButton`(h=36 圆角4px, 透明底)

### 34. 服务器悬停面板 ServerPanel(v2.3.1 二轮, 取代一代的 ServerSelect 直连下拉)

- **用途**: 悬停 ServerMonitor 胶囊展开的覆盖层:逐行列出预设服务器(专用启动器, 现役两个服), 每行 = 状态点(8px) + 名称(13px/600) + 人数(`N / M`, 11px tabular-nums) + 「进入」钮(28×28 纯图标 →, **悬停该行才出现**, tooltip 进入服务器)。数据源 = `cs.suchitems.top/api/status` + 预设 `sid` 映射
- **Props**: `servers`([{name, addr, sid, status, players, maxplayers}]), `onEnter(addr)`
- **何时用**: 仅主页, 锚定状态胶囊下方(覆盖层, 不占布局)
- **何时不用**: 编辑页/头像页;预设列表为空时显示引导文案(去常用设置配 ConnectServer)
- **交互**: 悬停胶囊展开 / 移出 150ms 后收起(防误关);「进入」= 一次性 `+connect` 该服启动,**不改动**常用设置的 ConnectServer 配置
- **⚠ 数据红线**: 在线状态与人数只来自状态 API 真实查询;API 失败该行显示「获取失败」灰点, 禁止编造
- **Flet**: 覆盖层 = `ft.Stack` + `ft.Container`(w=264, 圆角 8px, bg `bg-card`, border `border-visible`, shadow)定位胶囊下方;行 hover 用 `on_hover` 切 bg `bg-ghost` + 显示进入钮(`ft.IconButton` 28×28 圆角 4px)

### 35. ~~副启动按钮 AltLaunchBtn~~(已删, v2.3.1 二轮)

- 练枪启动改放**主页标题栏 WinBtn 练枪变体**(准星图标, 见 #4);此组件从 UI 与组件库移除, 编号保留防错位。

### 36. 主题菜单 ThemeMenu(v2.3.1 收编)

- **用途**: 标题栏主题按钮(WinBtn 变体, 图标=月亮[深]/太阳[浅])点击弹出的方案菜单:深色/浅色/定时切换(选中项 ✓) + 分割线 + 「深色时段设置…」
- **Props**: `mode`(当前 dark/light/scheduled), `onChange(mode)`, `onOpenPeriod`
- **何时用**: 主页 + 编辑页标题栏;**修改头像页不放**(裁剪中换装丢进度)
- **何时不用**: 其他任何位置
- **Flet**: `ft.PopupMenuButton` 或沿用现有 AlertDialog 菜单(main.py `_open_theme_menu`);菜单项图标=当前选中 ✓(brand), 未选中=各自语义图标;弹层圆角 8px、bg `bg-card`、border `border-visible`、阴影
- 定时模式说明文案:「区间内深色、其余浅色; 支持跨午夜 (如 19:00-07:00)」

### 37. 表单弹窗 FormDialog(v2.3.1 收编)

- **用途**: 轻量表单弹窗共用形态:标题(15px/700) + 表单行 + 说明小字(11px) + 右下操作(取消=透明文字钮, 保存=主色实心钮)。现役实例:深色时段(开始/结束 HH:MM mono 输入)。(自定义服务器弹窗已随直连下拉一并删除, v2.3.1 二轮)
- **Props**: `title`, `content`(行列表), `desc`(可选), `onCancel`, `onSave`
- **何时用**: 需要少量输入的确认型交互
- **何时不用**: 无输入的纯提示(用 Snackbar/状态栏错误);复杂流程(整页)
- **Flet**: `ft.AlertDialog`(modal=False, bgcolor `bg-card`);取消=`ft.TextButton`, 保存=`ft.FilledButton`(bg `brand` 白字, radius 8);遮罩为 Flet 原生 barrier
- ⚠ 弹窗不套窗口外壳(见 #1 何时不用)

### 38. 提示条 HintBar(v2.3.1 收编, 原 CFG 页内联结构)

- **用途**: CFG 配置页顶部条件提示:警告(琥珀底+边框, 缺 `+exec auto.cfg`, 动作「一键添加」)/错误(红底+边框, 预设文件缺失, 动作「重新植入」)。图标 16px + 文案 12px + 右侧动作按钮
- **Props**: `variant`(warn/err), `text`, `action`(按钮文案+回调)
- **何时用**: CFG 页条件显示(两个条件都成立时上下堆叠)
- **何时不用**: 常驻信息(那是 page-head 的 desc);工具运行状态(用 ToolStatus)
- **Flet**: `ft.Container`(bg `warn-bg`/`err-bg`, border 1px `status-amber`/`status-red`, padding 12/8)内 Row: Icon(warning_amber/error_outline 16px)+Text(expand)+OutlinedButton(主色实心, h=28)

---

## 视图结构速查(供 Flet 翻译对照)

```
主页 (360×510, v2.3.1 二轮)
└─ Window (DWM 圆角) → TitleBar(VersionTag + 产品名15px | WinBtn: 练枪/主题/配置/最小化/关闭)
   → launcher-card: Avatar → Nickname(24px) → ServerMonitor(主服状态+chevron) → LaunchButton(110 圆)
   ├─ ServerPanel (悬停胶囊展开: 预设服逐行, 悬停行出「进入」钮)
   └─ ThemeMenu (主题按钮弹出)

编辑页 (784×600)
└─ Window → EditTitleBar(BarButton×4 + Save | WinBtn: 主题/最小化/关闭)
   → edit-body: SidebarNav(nav-item×4) + content [+ ThemeMenu]
   ├─ group-0 常用设置: PageHead + FieldGrid(ConfigCard×6)
   ├─ group-1 加载器:   PageHead + ConfigCard(LaunchSplit: textarea + RecPanel)
   ├─ group-2 修复工具: PageHead + 超时行 + ToolGrid(ToolCard×4)
   └─ group-3 CFG 配置: 顶部说明 + HintBar×N + 组标题×4 + ConfigCard×23
   → StatusBar(Icon + EncGroup)

修改头像 (784×600, 无主题按钮)
└─ Window → EditTitleBar 变体(返回 + 标题「修改头像」+ WinBtn×2)
   → avatar-body: crop-stage(CropCanvas: Image + CropBox) + avatar-side
   └─ avatar-side: PreviewAvatar(96px 圆) + 提示 + AvatarActionBtn×4(选择图片/恢复默认/取消/保存)

全局覆盖层
└─ FormDialog(深色时段) — 跨窗口居中遮罩
```
