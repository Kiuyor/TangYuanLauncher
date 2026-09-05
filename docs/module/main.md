# main.py (根入口)

> 最后核对: 2026-09-05 · 共 20 行

## 一句话职责

进程入口：注入仓库根到 sys.path、配置 Nuitka 打包模式的 Flutter 引擎路径、以
隐藏窗口模式启动 flet 应用。

## 公开接口

无（纯脚本）。唯一动作：`ft.run(flet_main, view=ft.AppView.FLET_APP_HIDDEN)`，
其中 `flet_main` 来自 `flet_app.main`。

## 关键实现决策

- **FLET_VIEW_PATH 指向 exe 同级 `engine/`**（打包版）：Flutter 客户端引擎随包
  分发，避免首次运行联网下载引擎。目录名不能叫 `flet/`——那是 flet 包数据文件
  目录，会被覆盖。
- **`FLET_APP_HIDDEN` 隐藏启动**：main() 构建完 UI 后 `page.window.visible=True`
  才一次性显示，消除启动时 Flutter 默认空白窗口一闪而过（用户反馈 2026-08）。
- 打包模式判定同时用 `sys.frozen` 与 `"__compiled__" in globals()`（两种 Nuitka
  形态）。

## 坑与禁忌

- `FLET_VIEW_PATH` 必须在 `ft.run` 之前设置，晚了引擎已经选路。
- 开发版（非打包）不动任何环境变量，走 .venv 的 flet。

## 依赖与被依赖

- 依赖：`flet`、`flet_app.main`。
- 被依赖：`run.bat`（开发启动）、`packaging/build_nuitka.bat`（打包目标脚本）。

## 关联文档

- packaging/README_分发版.md（引擎随包分发与体积）
- [flet_app/main](flet_app/main.md)
