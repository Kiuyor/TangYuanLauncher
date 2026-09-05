# packaging/prepare_chunks.py

> 最后核对: 2026-09-05 · 共 389 行

## 一句话职责

打包时游戏预处理：对游戏目录就地补丁 → 植入默认集合（s0up 预设/练枪图/物品库/
autoexec 桥接）→ 7z 分块压缩 → 生成 chunks.iss 契约文件。

## 公开接口

`python packaging/prepare_chunks.py <game_dir> <out_dir>`（**game_dir 会被就地修改**，
每项幂等+备份）。

**对 installer.iss 的契约**（改动必须双向同步）：
- 分块命名 `game.partNN.7z`（NN 两位十进制 00 起）；
- 分块内路径相对 game 根，解压到 `{app}\game` 即还原；
- `build/chunks.iss` 内容 = `#define ChunkCount N` + `[Files]` dontcopy 条目，
  installer.iss `#include`。

## 关键实现决策

- **PATCHES**（字节补丁，幂等判定=目标字节已在）：startgame.bat timeout 10→2、
  rev.ini Language English→schinese。**新字节末尾不带空格**——`b"timeout /t 2 "`
  的尾随空格会造出双空格（deep-review 6轮 Low-7）。
- **FILE_REPLACEMENTS**（整文件替换，幂等=md5 已为目标）：扩展版 items_730.bin
  （6350 记录，旧版备份 assets/items_730.bin.bak_ext1891_20260831）。
- **植入项**：s0up 预设 13 个文件进 `csgo/cfg/`（清单从 `app/cfg_fields.S0UP_FILES`
  import——**单一事实源**，运行时 CFG 页共用）；`aim_botz.bsp` 进 `csgo/maps/`
  （一键练枪，v2.3.0）；autoexec.cfg 桥接（`exec auto.cfg`，内容不同先备份）。
- **构建机隔离**：config.cfg/键位历史等构建机私有文件被剔除，不把打包机的键位/
  统计强加给所有玩家。
- 分块目标 1200MB；`_chunk_fingerprint` + manifest 跳过未变化分块（重跑增量）。
- 7-Zip 定位：已知位置优先 + 常见路径回退（硬编码单路径换机即断）。

## 坑与禁忌

- bytes 字面量内嵌中文转义会静默失败——统一 `.encode("utf-8")` 写法。
- `--onefile` 不适用：本脚本与 build_release.bat 的目录版流水线配套。

## 依赖与被依赖

- 依赖：`app/cfg_fields`（S0UP_FILES）、7z、仓库 assets/。
- 被依赖：`packaging/build_release.bat` → `installer.iss`（#include chunks.iss）。

## 关联文档

- [app/cfg_fields](../app/cfg_fields.md)
- packaging/installer.iss、packaging/README_分发版.md
