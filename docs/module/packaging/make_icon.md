# packaging/make_icon.py

> 最后核对: 2026-09-05 · 共 90 行

## 一句话职责

应用图标抠图生成（v3 算法）：从原图分离内圈圆角方块图标与 alpha 版，一次性工具。

## 公开接口

改脚本顶部 `SRC` 常量后 `python packaging/make_icon.py`；输出
`packaging/assets/icon_alpha.png` / `icon_preview.png`。

## 关键实现决策

- 像素级判定：`dist_inner`（到内圈方块距离）与 `dist_outer` 的符号区分内外圈——
  白色主体保留、方块外角落蓝色裁掉。
- 源路径是本机 Downloads 绝对路径（一次性工具惯例，不参数化）。

## 坑与禁忌

- 输出路径历史上写过 D:\cs\，D 盘迁移后已改 D:\re-la——再迁移时搜 `packaging\\assets`
  全部硬编码。
- 产物进 packaging/assets/（会随仓库分发），重生成前确认 git 状态。

## 依赖与被依赖

- 依赖：PIL。
- 被依赖：无自动化消费方（产出由人工确认后用于 ico 转换）。

## 关联文档

- packaging/installer.iss（SetupIconFile）
