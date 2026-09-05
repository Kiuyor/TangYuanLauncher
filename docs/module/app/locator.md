# app/locator.py

> 最后核对: 2026-09-05 · 共 229 行

## 一句话职责

CS:GO 安装目录 / rev.ini / cfg 目录的自动定位（注册表 + 约定路径启发式，纯函数
无 UI）。

## 公开接口

- `find_csgo_dir() -> str | None` — 自动定位游戏根目录，永不抛异常（OSError 兜底）。
- `locate_rev_ini(csgo_dir=None) -> str | None` — 显式目录 → 用户指定(settings) →
  自动探测 → cwd 四级优先。
- `find_cfg_dir(csgo_dir) -> str | None` — 推导 `csgo/cfg`，不存在返回 None。

## 关键实现决策

- **候选优先级**：exe 同级 `game\`（内嵌游戏版）强命中（含 rev.ini 或 csgo.exe）
  立即返回；注册表卸载信息（HKLM→WOW6432Node→HKCU × 两级 Uninstall 路径）与
  cwd/常见路径收进候选列表，最后统一过 `_looks_like_csgo_dir` 验证（严格要求
  csgo.exe，防父目录误判）。
- **弱命中不遮蔽**：`game\` 只有 Loader.exe 时仅进候选不直接返回——否则残留目录
  会抢走注册表里的完整安装（deep-review 7轮 F5）。**2026-09-05 诊断实录**：开发机
  注册表里 D:\CSGO_backup 的卸载项排在 D:\re-la\CSGO 之前，导致自动定位落到备份
  目录、启动走了原版 Loader.exe。
- `_clean_reg_path` 处理 DisplayIcon 的 `"路径",0` 引号/图标索引形态。

## 坑与禁忌

- 注册表枚举顺序决定命中，诊断"为什么定位到了奇怪目录"先看 Uninstall 全量清单。
- `find_cfg_dir` 不存在的目录返回 None（不返回"最可能路径"）——os.startfile 对
  不存在路径会抛未捕获 OSError（deep-review F8）。
- 非 Windows 环境 winreg 为 None，全部启发式静默跳过。

## 依赖与被依赖

- 依赖：`app.settings`（get_user_csgo_dir，locate_rev_ini 的第 2 级）。
- 被依赖：`flet_app/main`（启动链/工具页/CFG 页）。

## 关联文档

- [app/settings](settings.md)
- [flet_app/main](../flet_app/main.md)（启动链对目录的消费）
