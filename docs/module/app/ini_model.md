# app/ini_model.py

> 最后核对: 2026-09-05 · 共 433 行

## 一句话职责

rev.ini 的解析 / 定向修改 / 序列化模型——只改键值，不破坏注释、空行、行尾风格与
编码。

## 公开接口

- `RevIni.load(path) / from_text(text)` — 解析（自动探测编码）。
- `get(section, key, default) / get_bool / has / keys(section)` — 读（键名大小写与
  section 均不敏感）。
- `set(section, key, value) / remove` — 定向写/删（新键插入到对应 section
  尾，行号索引自动平移）。
- `to_text() / save(path, encoding)` — 序列化/保存（编码由 UI 编码选择器指定）。
- `RevIni.backup(path)` — `.bak` 备份。
- `decode_ini_bytes / encode_ini_text`（utf-8/gbk 探测与编码）、`default_ini_text()`。

## 关键实现决策

- **格式零漂移**：记录 `trailing_newline`（splitlines 会丢末尾换行，不还原则每保存
  一次文件尾变一次）与 `line_ending`（CRLF 文件整体还原，不混写 LF）。
- **双编码兼容**：revLoader（2017 C++）按 ANSI(GBK) 读 ini，现代编辑器用 UTF-8；
  读取自动探测，保存由 UI 编码选择器决定。
- 键索引按 `(section_lower, key_lower)`；`set` 走行内替换，`remove` 后 `_shift_from`
  平移全部索引。

## 坑与禁忌

- 绝不要用 configparser 重写本文件——注释/空行/行尾/编码全丢。
- `save` 是原子写（tmp + os.replace）；调用方负责保存前 `.bak` 备份语义。
- 键名带引号的形态由 `_unquote` 归一，比较前一律 unquote。

## 依赖与被依赖

- 依赖：`app`（VERSION）。
- 被依赖：`flet_app/main`（编辑页 load/save/编码切换）。

## 关联文档

- [app/fields](fields.md)
- [flet_app/main](../flet_app/main.md)
