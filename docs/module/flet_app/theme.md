# flet_app/theme.py

> 最后核对: 2026-09-05 · 共 282 行

## 一句话职责

设计令牌唯一来源（颜色/阴影/字号/圆角/间距/布局/字体族/动效时长）+ 深浅双主题
整体换装 `set_scheme()`。

## 公开接口

- 令牌常量：`COL_*`（背景/品牌/文字/功能色/边框/裁剪/启动态/开关）、`SHADOW_*`、
  `FONT_10..44`、`RADIUS_CARD(8)/CTRL(4)/PILL(999)`、`SPACE_4..48`、
  `WIN_LAUNCHER(360,510)/WIN_EDIT(784,600)`、`H_INPUT=48`、`FONT_CN/FONT_MONO`、
  `MOTION_FAST/GROUP/NORMAL`、`EASE_STANDARD`。
- `set_scheme("dark"|"light")` / `get_scheme()`。

## 关键实现决策

- **深色 = 模块常量即事实源**；浅色 = `_LIGHT` 覆盖表，未覆盖的 token 深浅通用
  （品牌主色族/功能色/间距字号布局共用）。import 时快照 `_DARK`，切回深色按快照
  整体还原。
- **阴影对象不可原地改色** → `_rebuild_shadows(light)` 换装时整体重建（浅色用 slate
  灰低透明度档）。
- `_rebuild_derived()` 维护派生色（ON_BRAND/CHIP_ADDED_BG/INPUT_BORDER/INPUT_FILL），
  随换装同步。
- `set_scheme` 只动本模块全局——已创建控件不会自动变，**重建可见视图是调用方
  （main.py rebuild）的责任**。

## 坑与禁忌

- **消费铁律（v2.3.0）**：颜色/阴影一律 `theme.COL_X` 属性访问；**from-import 会
  冻结启动时的深色值**，换装后不可见。默认参数引用 `theme.*` 同样冻结（select_dark
  的 border_color 因此改 None 兜底）。
- 历史别名 `COL_BG/COL_CARD` 必须是模块常量——只写进 `_LIGHT` 而不在深色区定义的
  话 `_DARK` 快照缺它，切回深色残留浅色值（根容器白底白字）。
- 新增 token：深色区定义 + 需要差异化才进 `_LIGHT`；换装快照自动收录 `COL_/SHADOW_`
  前缀。

## 依赖与被依赖

- 依赖：flet（BoxShadow/AnimationCurve）。
- 被依赖：`flet_app/main`、`flet_app/components/ui`（全部取色走此处）。

## 规范令牌未消费清单 (2026-09-05 令牌接线专项留档)

以下令牌在 tokens.md 有户口、Flet 侧暂无消费点，**保留不删**（删除=撕规范一角）：

- `SHADOW_WINDOW`：Flet 桌面窗口无外阴影 API（HTML-only）
- `MOTION_GROUP / MOTION_NORMAL`：offset 类动效已降级为即时切换（tokens.md §7），
  flet 升级恢复动效时启用
- `H_NAV_ITEM`：NavigationRail 项高由引擎自管，无设置 API
- `COL_FOCUS_RING / COL_TEXT_DISABLED`：无对应控件态消费点
- `COL_SWITCH_INACTIVE_THUMB / COL_SWITCH_INACTIVE_TRACK / SHADOW_THUMB`：bool 字段
  用原生 ft.Switch，design-system #28 自绘开关未实装（接线=新建组件，超范围）
- `RADIUS_CIRCLE / RADIUS_MD`：正圆惯用「尺寸/2」写法（tokens.md 两种都认可）；
  RADIUS_MD 属非产品预览工具栏

本次已接线（原字面量双份事实已消）：`WIN_LAUNCHER/WIN_EDIT`（删 main.py 本地
WIN_HOME/WIN_EDIT/WIN_MIN）、`W_SIDEBAR`、`H_BTN_BAR`、`H_TITLEBAR`、`H_STATUSBAR`、
`S_DOT`、`FONT_16`、`FONT_20_IC`、`COL_BG_SIDEBAR`（导航栏底色对齐事实源，2026-09-05
拷问定稿 B 档）、`COL_LAUNCH_BUSY/DONE`（2026-09-05 清理轮）。

## 关联文档

- docs/tokens.md（设计事实源，与 preview v1.html 双向一致）
- docs/design-system.md、docs/DESIGN.md 坑位表
