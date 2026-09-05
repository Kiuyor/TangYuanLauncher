# app/tools.py

> 最后核对: 2026-09-05 · 共 392 行

## 一句话职责

修复工具的元数据与执行（REPAIR_TOOLS / run_tool）+ 内置资源安装（newloader、皮肤
库、启动提速、注册表清理）。

## 公开接口

- `RepairTool` dataclass：name/file/category/desc/action/risk/confirm/handler。
  `file=None` = python 内置 handler，否则为游戏目录内 bat。
- `REPAIR_TOOLS` — 工具页卡片清单（4 项：清除武器皮肤缓存 / 修复 Steam 客户端错误 /
  清理 RevEMU 注册表残留 / 更新皮肤库 / 启动提速——**「安装优化 Loader」手动工具
  已删**，2026-09-05 改由启动链自动就位）。
- `run_tool(csgo_dir, tool, on_done, timeout=120)` — 异步执行；回调 `on_done(ok, msg)`
  来自工作线程，**UI 更新必须经 page.run_thread 回主线程**（H1）。
- `_install_loader(csgo_dir, on_done)` — 装 assets/Loader_opt23.exe 为 newloader.exe，
  **md5 幂等、不覆盖原件**；回退=删除 newloader.exe。
- `_update_items`（皮肤库 6350 记录覆盖+备份）/ `_speedup_startgame`（timeout 10→2s，
  行首锚定正则保 CRLF）/ `_clean_reg_leftover`（只删模拟器写的 SteamClientDll/pid）。
- `ASSETS_DIR / ASSET_LOADER / ASSET_ITEMS`、`_backup_file`（时间戳备份）。

## 关键实现决策

- **幂等判定用 MD5 内容比较**而非大小（大小撞车会误判跳过，2026-08 拷问 A1 定稿）。
- bat 修改走字节级正则替换，不重编码整个文件（保留原 CRLF/编码）；正则必须
  `(?m)^[ \t]*` 行首锚定——否则 banner/ECHO 文本里的同形字样先命中，假报幂等
  （deep-review 7轮 F1）。
- `run_tool` 超时杀进程树（`_kill_process_tree`），输出 stdout/stderr 合并解码兜底。
- 资源目录判定：打包版 exe 同级 assets\（app 包内嵌 exe 后 `__file__` 不再指向源码
  路径），开发版仓库根 assets\。

## 坑与禁忌

- 注册表清理只删 `SteamClientDll`/`pid` 两个值——正版 Steam 的 SteamClientDll64/
  Universe/ActiveUser 不动。
- 新增工具：file 与 handler 二选一；confirm 文案必填（UI 强制确认弹窗）。

## 依赖与被依赖

- 依赖：`assets/`（Loader_opt23.exe、items_730.bin）。
- 被依赖：`flet_app/main`（工具页 + 启动链 `_install_loader(d, None)`）、
  `scripts/verify_tools`（回归闭环）。

## 关联文档

- [flet_app/main](../flet_app/main.md)（启动链与工具页）
- [scripts/verify_tools](../scripts/verify_tools.md)
