# app/cfg_fields.py

> 最后核对: 2026-09-05 · 共 282 行

## 一句话职责

CFG 配置页的字段定义 + s0up 预设（auto.cfg / crosshair.cfg）的解析与行内写回引擎。

## 公开接口

- `CfgField`（frozen dataclass）：key/label/kind(float|int|enum)/min_v/max_v/default/
  options/file/unit/**scale**；`validate(raw) -> (ok, err)`（空串=未填不校验）。
- `GROUPS`（鼠标/准星/声音/性能四组）、`FIELD_INDEX`（key → CfgField）。
- `S0UP_FILES` — 预设随包文件清单**单一事实源**（packaging/prepare_chunks 也 import）。
- `parse_cfg(path) -> {命令名: (值, 注释段, 行号0基)}` — 值已去引号。
- `apply_values(cfg_dir, updates) -> {文件路径: 修改行数}` — 行内替换 + 缺失命令按组
  追加；updates 必须已是最终**文件值**（scale 换算在 UI 层完成）。

## 关键实现决策

- **写回 = 行内值替换**：保留原行缩进/分隔空格/行尾注释（s0up 预设的排版是命令名
  后多空格对齐值列）；auto.cfg 裸值、crosshair.cfg 带引号。
- **scale 换算放 UI 层**：准星透明度显示 0-100%、文件值 0-255（scale=2.55）；换算
  不在 apply_values 做，是为了用原始文件值精确判断「未修改」，防 round 往返丢精度。
- **缺失命令追加锚点**：按组匹配 auto.cfg 分节标题（`_GROUP_TITLE_KEYWORDS`）插入
  标题行后，从后往前插避免行号偏移；crosshair.cfg 无分节走文件尾。
- `validate` 显式拦截 NaN/inf——`float("nan")` 不抛 ValueError 且与 min/max 比较恒
  False，会绕过范围检查把 `sensitivity nan` 写进 cfg（deep-review 12轮）。
- 写回原子写（tmp + os.replace，2026-09-05 审查统一）。

## 坑与禁忌

- parse 忽略 `alias/exec/echo/clear/host_writeconfig/unbindall` 行——不要把可执行
  行当字段。
- `updates` 的值若未做 scale 换算会直接写错量纲。
- 新增字段要同时进 GROUPS（决定追加锚点组）与目标 file 属性。

## 依赖与被依赖

- 依赖：无（纯标准库 + dataclass）。
- 被依赖：`flet_app/main`（CFG 页全流程）、`packaging/prepare_chunks.py`（**跨层
  引用**：S0UP_FILES 清单）。

## 关联文档

- [flet_app/main](../flet_app/main.md)（CFG 页：范围标红/保存备份/+exec 检测）
- [packaging/prepare_chunks](../packaging/prepare_chunks.md)
