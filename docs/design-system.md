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
| 15 | 代码键名标签 CodeTag | `.code-tag` | 常用设置 |
| 16 | 输入框 InputDark | `.input-dark` | 编辑页 |
| 17 | 下拉框 SelectDark | `.select-dark` | 常用设置 |
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

> **Flet 原生豁免标注 (deep-review 7轮 F4 定稿)**: 以下组件在 Flet 中由原生控件直接表达
> (rules.md §1.4 原生豁免, 不需要也不应封装成 ui.* 组件, 页面直用):
> - #1 Window → `ft.Container`(圆角裁切+边框, main.py 顶层容器)
> - #2 TitleBar / #9 EditTitleBar → `ft.Row` + `ui.win_btn`/`ft.OutlinedButton`/`ft.FilledButton` 组合
> - #10 BarButton → `ft.OutlinedButton`/`ft.FilledButton`(样式经 ButtonStyle)
> - #11 SidebarNav → `ft.NavigationRail`(indicator 透明, 选中色走 selected_*_text_style)
> - #27 EncGroup → `ft.SegmentedButton`
> - #28 Switch → `ft.Switch`
> 其余 #3-#8/#12-#26 已全部实现为 `ui.*` 组件(flet_app/components/ui.py)。

---

## 组件详述

### 1. 窗口外壳 Window

- **用途**: 应用窗口容器,承载标题栏 + 内容;圆角裁切 + 浮起投影
- **Props**:
  - `size`: `launcher`(360×510)/ `edit`(784×600)
  - `label`: 窗口标注文本(仅预览用)
- **何时用**: 两个主视图各一个
- **何时不用**: 弹窗/对话框不套窗口外壳
- **Flet**: `ft.Window`(frameless, 透明底, border_radius=16, shadow `shadow-window`) + `ft.Row`/`ft.Column` 内容

### 2. 标题栏 TitleBar(主页)

- **用途**: 主页顶部栏:左=版本徽章+产品名,右=窗口控制(配置/最小化/关闭)
- **Props**: 无(固定结构)
- **何时用**: 仅主页
- **何时不用**: 编辑页用 EditTitleBar(组件 9)
- **Flet**: `ft.Container`(h=56, bg `bg-deep`, 下边框 `border-subtle`)内 Row

### 3. 版本徽章 VersionTag

- **用途**: 显示客户端版本号(如 v1.35.7.7)
- **Props**: `text`
- **何时用**: 主页标题栏左端
- **何时不用**: 不放正文/卡片内
- **Flet**: `ft.Container`(pill, bg `brand` 20% 底, border `border-brand`, text `brand-light` mono 10px 700)

### 4. 窗口控制按钮 WinBtn

- **用途**: 无边框图标按钮:配置(齿轮)/最小化/关闭
- **Props**: `icon`(i-settings/i-minus/i-x), `variant`(normal/close)
- **何时用**: 标题栏右上角;配置按钮仅主页
- **何时不用**: 不用于主操作(主操作用 BarButton/RunButton)
- **Flet**: `ft.IconButton`(28×28, radius 6, hover bg `rgba(255,255,255,0.08)`;close hover bg `status-red`)

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

- **用途**: 显示服务器在线状态 + 人数胶囊
- **Props**: `status`(`online`/`offline`), `label`(在线/离线), `count`(人数,offline 时隐藏)
- **何时用**: 主页昵称下方
- **何时不用**: 无服务器地址时不显示人数(数据契约见 DESIGN.md)
- **⚠ 数据红线**: 人数必须来自 A2S 真实查询,离线禁止展示人数(JS 已实现隐藏逻辑)
- **Flet**: `ft.Container`(pill, bg `bg-ghost`, border `border-subtle`)内 Row: 圆点(8px `status-green`+3px 浅绿晕/离线 `text-dim`)+ 标签(15px mono `text-dim`)+ 人数(15px 600 mono `text-secondary`)

### 8. 启动按钮 LaunchButton

- **用途**: 主页主操作:启动游戏(圆形纯图标)
- **Props**: `state`(idle/launching/running,控制底色与 title), `icon`(默认 i-rocket)
- **何时用**: 主页唯一主按钮
- **何时不用**: 不承载文字;不用作编辑页操作按钮
- **Flet**: `ft.Container`(110×110 圆, bg `brand` → hover `brand-hover` → busy `launch-busy` → done `launch-done`+`launch-glow`, 居中 Icon rocket 44px 白)
- 交互: 点击后依次 busy(1.5s)→ done(4s)→ 复位;期间防重复点击

### 9. 编辑页标题栏 EditTitleBar

- **用途**: 编辑页顶部操作栏:返回/打开cfg文件夹/指定目录/打开文件/保存 + 窗口控制
- **Props**: 无(固定结构)
- **何时用**: 仅编辑页
- **何时不用**: 主页用 TitleBar
- **Flet**: `ft.Container`(h=56, bg `bg-deep`, 下边框 `border-subtle`)内两个 Row(left/right)

### 10. 顶栏按钮 BarButton

- **用途**: 编辑页顶部文字按钮(返回/打开/指定/保存)
- **Props**: `icon`, `label`, `variant`(normal/primary)
- **何时用**: 编辑页标题栏;primary 变体用于「保存」
- **何时不用**: 不作为内容区按钮(内容区用 RunButton);不带图标不放这里
- **Flet**: `ft.OutlinedButton` 风格 Container(h=34, radius 8, border `border-subtle`, bg `bg-ghost-2`)→ primary: bg `brand` 白字 700

### 11. 侧栏导航 SidebarNav

- **用途**: 编辑页分组导航(常用设置/加载器/修复工具)
- **Props**: `items`(icon+label 列表), `activeIndex`
- **何时用**: 编辑页左侧固定栏
- **何时不用**: 主页无导航;不超过 3 项
- **Flet**: `ft.Container`(w=96, bg `bg-sidebar`, 右边框 `border-subtle`)内 Column;激活项: bg `brand` 10% + 左 3px `brand` 指示条 + 文字/图标 `brand-soft`

### 12. 页头 PageHead

- **用途**: 编辑页各分区页头:代码键名 kicker + 标题 + 描述
- **Props**: `code`(kicker 文本,自动大写), `title`, `desc`
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

- **用途**: 设置项容器:标题行(标题+CodeTag)+ 描述 + 输入控件
- **Props**: `title`, `desc`, `tag`(可选 CodeTag), `control`(Input/Select), `title_expand`(标题撑满,键名徽章贴右), `desc_lines`(>0 时描述固定行高容器,双列等高用 2)
- **何时用**: 常用设置字段
- **何时不用**: 工具卡用 ToolCard;双列内 hover 不右移
- **Flet**: `ui.config_card()`(padding 16, radius 8, bg `bg-card`, border `border-subtle`;hover bg `bg-ghost-2` + border `border-brand`, 双列内无位移;desc_lines=2 时 desc 容器高 36px)

### 15. 代码键名标签 CodeTag

- **用途**: 显示 rev.ini 键名(如 `Emulator.Language`)
- **Props**: `text`
- **何时用**: 配置卡片标题右侧
- **何时不用**: 不用于显示用户输入值
- **Flet**: `ft.Container`(radius 4, bg `brand` 10%, text mono 10px `brand`)

### 16. 输入框 InputDark

- **用途**: 单行文本输入(昵称/标签/端口等);`mono` 变体用于 IP:端口
- **Props**: `value`, `placeholder`, `mono`, `multiline`, `height`, `fontSize`, `width`(字段卡内 236), `onChange`, `maxLength`, `textAlign`
- **何时用**: 需文本输入的字段
- **何时不用**: 选项类用 SelectDark;布尔用 Switch
- **Flet**: `ui.input_dark()`(组件库实现;radius 6, bg `bg-input`, border `border-visible`, focus border `brand`;textarea: multiline 多行 16px mono;字段卡内传 height=None 保持 flet 默认 ~63px 高——用户否决过 40px 扁框)

### 17. 下拉框 SelectDark

- **用途**: 选项下拉(界面语言/段位)
- **Props**: `options`, `selected`, `placeholder`, `width`, `height`, `onSelect`, `filled`/`fillColor`(0.86.5 必须 filled 才绘制底色), `borderColor`
- **何时用**: 需选项的字段
- **何时不用**: 文本输入用 InputDark;布尔用 Switch
- **Flet**: `ui.select_dark()`(组件库实现;字段卡内 width=236 height=64 filled 匹配 TextField 高度;注意: Dropdown 弹出层可能被圆角窗口裁切——Flet 落地已实测)

### 18. 推荐项 Chip

- **用途**: 可点击标签;点击切换 added 态(前缀 ✓)
- **Props**: `label`, `added`(bool)
- **何时用**: 加载器推荐启动项(右栏竖排)
- **何时不用**: 不作为普通信息标签(用 CatTag/RiskTag)
- **Flet**: `ft.Container`(pill, border `border-visible`, bg `bg-ghost`;added: bg `brand` 18% + border `border-brand` + 字 `brand-light`;mono 11px)
- ⚠ 竖排时: 单行省略(width 100%, nowrap + ellipsis + min-width 0),防溢出

### 19. 推荐面板 RecPanel

- **用途**: 加载器右栏容器:「推荐启动项」标题 + 竖排 Chips
- **Props**: `title`, `chips`, `expand`(Row 内分栏比例,LaunchSplit 右栏 2)
- **何时用**: 仅加载器右栏
- **何时不用**: 内容区其他位置
- **Flet**: `ui.rec_panel()`(组件库实现, deep-review 7轮 F4 抽取;padding 12, radius 8, bg `bg-ghost-3`, border `border-subtle`)

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
- **Flet**: `ui.tool_card()`(padding 16, radius 8, bg `bg-card`, border `border-subtle`;hover border `border-brand`;内部组合 CatTag + RiskTag + RunButton + ToolStatus)

### 22. 类别标签 CatTag

- **用途**: 工具类别(缓存清理/注册表修复/Loader)
- **Props**: `text`
- **何时用**: ToolCard 顶行左侧
- **何时不用**: 非工具上下文
- **Flet**: `ft.Container`(radius 4, bg `brand` 15%, border `border-brand`, 字 `brand-light` 10px 600)

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
- **Flet**: `ft.FilledButton`(h=32, radius 8, bg `brand`, 白字 700 12px;disabled opacity 0.5)

### 25. 工具状态 ToolStatus

- **用途**: 工具运行状态文本(待运行/运行中…/完成/失败)
- **Props**: `state`(idle/running/ok/fail)
- **何时用**: ToolCard 底部
- **何时不用**: 非工具上下文
- **Flet**: `ft.Text`(11px, 右对齐;running=`status-amber`, ok=`status-green`, fail=`status-red`, idle=`text-dim`)

### 26. 状态栏 StatusBar

- **用途**: 编辑页底部:左=状态图标(仅图标)+可选状态消息,右=编码切换
- **Props**: `encSelector`, `statusMsg`(可选 Text,加载/保存错误临时显示;None 时仅图标)
- **何时用**: 仅编辑页底部
- **何时不用**: 主页不放状态栏(坑位记录);常驻状态文字已删,只留图标
- **Flet**: `ui.status_bar()`(h=64, bg `bg-deep`, 上边框 `border-subtle`)内 Row: 左 Icon(check-circle 15px `status-green`) + 可选消息,右 EncGroup

### 27. 编码切换 EncGroup

- **用途**: ANSI/UTF-8 分段切换
- **Props**: `active`(ansi/utf8)
- **何时用**: 状态栏右侧
- **何时不用**: 其他位置
- **Flet**: `ft.Container`(分段控件: bg `rgba(255,255,255,0.05)` radius 8 padding 3;激活项 bg `brand` 白字)

### 28. 开关 Switch(预留)

- **用途**: 布尔设置项
- **Props**: `checked`
- **何时用**: 未来布尔字段
- **何时不用**: 当前字段无布尔项(显示头像已删)
- **Flet**: `ft.Switch`(track 40×22 pill, on 时 bg `brand`, thumb 18px 白)

---

## 视图结构速查(供 Flet 翻译对照)

```
主页 (360×510)
└─ Window → TitleBar(VersionTag + WinBtn×3) → launcher-body
   └─ launcher-card: Avatar → Nickname → ServerMonitor → LaunchButton

编辑页 (784×600)
└─ Window → EditTitleBar(BarButton×4 + Save + WinBtn×2)
   → edit-body: SidebarNav(nav-item×3) + content
   ├─ group-0 常用设置: PageHead + FieldGrid(ConfigCard×6)
   ├─ group-1 加载器:   PageHead + ConfigCard(LaunchSplit: textarea + RecPanel)
   └─ group-2 修复工具: PageHead + 超时行 + ToolGrid(ToolCard×4)
   → StatusBar(Icon + EncGroup)
```
