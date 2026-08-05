# Design Tokens — Rev.Ini 编辑器

> Material Design 3 暗色主题 · 琥珀橙主色
> 本文为单一事实源,与 `app/style.py` 中 `MD3` dict 一一对应(已通过审计脚本验证零偏差)

---

## 色彩系统

### Primary(主色 — 琥珀橙)

| Token | 值 | 用途 |
|-------|-----|------|
| `primary` | `#ffb868` | 主操作按钮、选中态、链接 |
| `on_primary` | `#4a2800` | primary 上的文字/图标 |
| `primary_container` | `#6d3c00` | 选中态容器、flash 高亮背景 |
| `on_primary_container` | `#ffdcc0` | primary_container 上的文字 |
| `primary_hover` | `#f0ac5f` | primary hover 态(派生, +8% on-primary 叠加) |

### Secondary / Tertiary

| Token | 值 | 用途 |
|-------|-----|------|
| `secondary` | `#dbc5a6` | 次要文字、非选中 chip |
| `on_secondary` | `#3d2e1a` | secondary 上的文字 |
| `secondary_container` | `#5c462d` | 次要容器 |
| `on_secondary_container` | `#f9dfc4` | secondary_container 上的文字 |
| `tertiary` | `#b8cca4` | 第三色(极少用) |
| `tertiary_container` | `#3e4f31` | 第三容器 |
| `on_tertiary_container` | `#d3e9be` | 第三容器上的文字 |

### Error

| Token | 值 | 用途 |
|-------|-----|------|
| `error` | `#ffb4ab` | 错误文字、危险操作 |
| `error_container` | `#93000a` | 错误容器背景 |
| `on_error_container` | `#ffdad6` | 错误容器上的文字 |

### Surface 层级(暗色主题 — elevation overlay)

暗色主题不用投影,通过 surface 提亮 + 主色 tint overlay 建立层次。

| Token | 值 | 层级 | 用途 |
|-------|-----|------|------|
| `surface` | `#121212` | 0 | 底层背景(窗口背景) |
| `surface_dim` | `#121212` | 0 | dim 表面 |
| `surface_lowest` | `#0d0d0d` | — | 最低容器(未使用) |
| `surface_low` | `#1b1b1b` | 1 | 卡片背景(Filled Card / 字段行) |
| `surface_container` | `#211f1e` | 2 | 标准容器(导航栏) |
| `surface_high` | `#2c2a28` | 3 | 高容器(hover/raised, 搜索框) |
| `surface_highest` | `#373533` | 4 | 最高容器(弹窗/下拉/搜索面板) |
| `surface_bright` | `#3a3836` | — | 亮色表面(未使用) |
| `surface_tint` | `#ffb868` | — | elevation overlay tint(= primary) |
| `card_hover` | `#2b2b2b` | — | 卡片 hover(派生, surface_low + 8% on-surface) |
| `field_hover` | `#454341` | — | 字段 hover(派生, surface_highest + 8% on-surface) |
| `tonal_hover` | `#67523b` | — | tonal 按钮 hover(派生, secondary_container + 8% on-secondary) |
| `field_border` | `#5c544d` | — | 输入控件常态底部边框 |

### 文字 / 边框

| Token | 值 | 用途 |
|-------|-----|------|
| `on_surface` | `#e6e1df` | 表面主文字 |
| `on_surface_variant` | `#cdc5bf` | 表面次要文字(描述、键名) |
| `outline` | `#9a8f88` | 边框、分割线 |
| `outline_variant` | `#4e4640` | 弱分割线(搜索框边框) |
| `scrim` | `#000000` | 遮罩层 |

### Inverse(反色)

| Token | 值 | 用途 |
|-------|-----|------|
| `inverse_surface` | `#e6e1df` | 反色表面(Snackbar 背景) |
| `inverse_on_surface` | `#1b1b1b` | 反色表面上的文字 |
| `inverse_primary` | `#6d3c00` | 反色主色(Snackbar action 按钮) |

### 状态层(State Layers, #AARRGGBB)

| Token | 值 | 用途 |
|-------|-----|------|
| `state_layer_on_surface_5` | `#0ce6e1df` | on-surface ≈5% (alpha 12/255, tab hover) |
| `state_layer_on_surface_6` | `#0fe6e1df` | on-surface ≈6% (alpha 15/255, 下拉项 hover) |
| `state_layer_on_surface_7` | `#12e6e1df` | on-surface ≈7% (alpha 18/255, combo 箭头状态层) |
| `state_layer_on_surface_8` | `#14e6e1df` | on-surface ≈8% (alpha 20/255, 导航/卡片/按钮 hover) |
| `state_layer_on_surface_9` | `#16e6e1df` | on-surface ≈9% (alpha 22/255, spinbox 按钮 hover) |
| `state_layer_on_surface_12` | `#1ee6e1df` | on-surface ≈12% (alpha 30/255, pressed) |
| `state_layer_error_12` | `#1effb4ab` | error ≈12% (alpha 30/255, 危险按钮 hover) |
| `state_layer_error_16` | `#2affb4ab` | error ≈16% (alpha 42/255, 危险按钮 pressed) |
| `state_layer_error_container_7` | `#1293000a` | error_container ≈7% (alpha 18/255, Snackbar 错误 action hover) |
| `state_layer_error_container_12` | `#1e93000a` | error_container ≈12% (alpha 30/255, Snackbar 错误 action pressed) |

---

## 字体

| 用途 | 字体栈 | Design.md 名称 |
|------|--------|---------------|
| UI 文字 | Noto Sans SC | Google Sans + Noto Sans SC |
| 数值/代码 | JetBrains Mono | JetBrains Mono |

---

## 形状(Shape)

| Token | 值 | 用途 |
|-------|-----|------|
| shape-small | 8px | 控件(下拉项、搜索结果项) |
| shape-medium | 12px | 卡片(字段行) |
| shape-large | 16px | 大容器(对话框) |
| shape-full | pill | 按钮、chip、状态徽章 |

---

## 尺寸规范

| 组件 | 尺寸 | 来源 |
|------|------|------|
| Navigation Rail 宽度 | 88px | design.md |
| Top App Bar 高度 | 64px | design.md |
| Bottom Bar 高度 | 40px | design.md |
| Nav item 高度 | 72px | design.md |
| Filled Card 内边距 | 16px | design.md |
| 切页动画时长 | 300ms | design.md Shared Axis |
| 切页滑入距离 | 30px | design.md translateX |
| 搜索框高度 | 30px | 新增(本轮) |
| 搜索面板宽度 | 380px | 新增(本轮) |
| 搜索结果行高 | 36px | 新增(本轮) |
| 快照像素预算 | 12M px | 新增(本轮,防 4K+高DPR 内存尖峰) |
| Snackbar 高度 | 44px | design.md |
