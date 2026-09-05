# flet_app/components/ui.py

> 最后核对: 2026-09-05 · 共 1372 行

## 一句话职责

唯一组件库：主页/编辑页/头像页全部 UI 组件的实现（rules §1 禁止页面内联伪组件）。

## 公开接口（按域）

- **通用**：`win_btn`(窗口钮, 显式 28×28)、`version_tag`、`avatar`、`nickname`、
  `page_head`、`_is_hovered`(on_hover 布尔兼容)。
- **主页**：`LaunchButton`(110 圆启动钮, 状态机 idle/launching/running + rocket-nudge
  抖动)、`ServerMonitor`(状态胶囊+呼吸点+轮询接入口)、`ServerPanel`(悬停分服面板)。
- **字段页**：`field_grid`(双列网格, spacing=10)、`config_card`、`input_dark`、
  `SelectDark`/`select_dark`(自绘下拉)、`Chip`、`launch_split`/`rec_panel`(启动命令
  3:2 分栏)。
- **工具页**：`tool_card`(附 `_run_btn`/`_status` 引用)、`cat_tag`、`risk_tag`、
  `RunButton`、`tool_status`。
- **编辑壳/头像页**：`EncGroup`(编码选择器, `selected` property 支持静默回填)、
  `status_bar`、`btn_av`、`preview_avatar`、`CropCanvas`(1:1 裁剪画布)。

## 关键实现决策

- **SelectDark 基于 ft.PopupMenuButton 自绘**：引擎弹出层只承担定位/外点关闭/滚动，
  视觉全自绘。不用纯 Stack 的原因：字段卡在 ListView 内会被视口裁切且无跨控件层级，
  引擎 overlay 无此缺陷。
- **input_dark 的 maxLength 不传引擎**：flet 0.86.5 引擎设限必自带 "0/32" 计数器
  （TextField 无 counter_text 参数，藏不掉），组件在 on_change 内手动截断，上限
  语义不变（2026-09-05）。
- LaunchButton 状态机只管样式/切换，业务在 main.py；抖动 `_NUDGE_SEQ` 仅 rotate
  （offset 分量已降级删去）。
- EncGroup 类化的核心是 `selected` property 静默回填——load_file 时 UI 可反向同步
  编码显示。

## 坑与禁忌

- Control 子类实例属性禁用 `_values/_dirty/_frozen`（基类响应式存储同名会覆盖）。
- on_hover 的 `e.data` 在 0.86.5 是真布尔——一律经 `_is_hovered` 比较。
- ServerMonitor 呼吸线程：`_ever_attached` 区分"未挂载继续等"与"已分离自停"；
  `set_status` 的 update 包 try（进编辑页 6s 竞态窗口）。

## 依赖与被依赖

- 依赖：`flet_app/theme`（全部取色动态访问）。
- 被依赖：`flet_app/main`（唯一消费方）。

## 关联文档

- docs/design-system.md（组件规格 #1-#37 事实源）
- [flet_app/theme](theme.md)
