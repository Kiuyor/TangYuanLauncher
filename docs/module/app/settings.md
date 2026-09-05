# app/settings.py

> 最后核对: 2026-09-05 · 共 89 行

## 一句话职责

用户设置持久化到 `%APPDATA%\RevIniEditor\settings.json`，全失败安全（不抛异常）。

## 公开接口

- `load_settings() -> dict` — 读盘 + DEFAULTS 合并；损坏/缺失静默回退默认。
- `save_settings(data: dict) -> bool` — 合并保存，成功 True；空字符串值 = 删除该键。
- `get_user_csgo_dir() -> str | None` / `set_user_csgo_dir(path)`。
- `DEFAULTS`：`user_csgo_dir`、`theme_mode`(dark|light|scheduled)、
  `theme_dark_start/end`、`server_presets`、`server_selected`。

## 关键实现决策

- **位置在用户配置目录而非源码目录**：Nuitka 打包后 `__file__` 指向临时解压目录，
  程序退出即清理，设置会丢。
- **原子写**：tmp + fsync + `os.replace`；失败清理 tmp 返回 False（deep-review 7轮
  F3：直接 open(w) 截断后 dump，磁盘满/杀软会留损坏 JSON → user_csgo_dir 重启遗忘）。

## 坑与禁忌

- save 传入空串是"清键"语义不是"写空串"——调用方要写空值需换哨兵。
- load 对非 dict JSON 同样回退 DEFAULTS；新增键必须进 DEFAULTS 才有默认值兜底。

## 依赖与被依赖

- 依赖：无（纯标准库）。
- 被依赖：`app/locator`（用户指定目录）、`flet_app/main`（主题三态/服务器预设/
  工具超时等所有持久化读写的唯一通道）。

## 关联文档

- [app/locator](locator.md)
