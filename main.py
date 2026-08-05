"""Rev.Ini 编辑器 — 入口"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Nuitka 打包模式 (standalone): Flutter 客户端引擎随包分发在 exe 同目录 engine/ 下,
# 通过 FLET_VIEW_PATH 让 flet_desktop 直接使用, 避免首次运行联网下载
# (注意: 不能叫 flet/, 那是 flet 包数据文件目录, 会被覆盖)
if getattr(sys, "frozen", False) or "__compiled__" in globals():
    engine = os.path.join(os.path.dirname(sys.executable), "engine")
    if os.path.isdir(engine) and not os.environ.get("FLET_VIEW_PATH"):
        os.environ["FLET_VIEW_PATH"] = engine

from flet_app.main import main as flet_main
import flet as ft

# FLET_APP_HIDDEN: 引擎窗口隐藏启动, main() 构建完 UI 后 page.window.visible=True
# 才一次性显示 —— 避免启动时 Flutter 默认空白窗口一闪而过 (用户反馈 2026-08)
ft.run(flet_main, view=ft.AppView.FLET_APP_HIDDEN)