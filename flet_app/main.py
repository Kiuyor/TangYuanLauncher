"""Rev.Ini 编辑器 — Flet 版 (汤圆启动器)

暗黑二次元启动器大改: 主页=居中竖卡片启动台, 配置编辑收进二级页。
设计定稿见 skill: flet-desktop-apps → references/revini-editor-launcher-redesign.md
实施计划见: plan.md
"""
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

import flet as ft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import VERSION
from app.cfg_fields import (
    FIELD_INDEX,
    GROUPS,
    S0UP_FILES,
    apply_values,
    parse_cfg,
)
from app.fields import (
    FIELD_GROUPS,
    RANK_DISPLAY,
    rank_level_to_name,
    rank_name_to_level,
)
from app.ini_model import RevIni, default_ini_text
from app.locator import find_cfg_dir, find_csgo_dir, locate_rev_ini
from app.settings import set_user_csgo_dir
from flet_app.components import ui
from flet_app.theme import (
    COL_BG_CARD as COL_CARD,  # 卡片底 (bg-card #161922)
)

# ==================== 汤圆启动器主题色板 (矢车菊蓝纯色体系, docs/theme.py 令牌) ====================
# 2026-08-08 推翻天蓝 #87CEEB 主题: 矢车菊蓝 #6495ED 纯色, 无渐变/发光。
# 令牌定义在 flet_app/theme.py (rules.md §2: 禁止硬编码色值, 统一引用令牌)
from flet_app.theme import (
    COL_BG_DEEP as COL_BG,  # 窗口背景 (bg-deep #0c0e14)
)
from flet_app.theme import (
    COL_BG_GHOST_2,
    COL_BG_INPUT,  # 输入控件底
    COL_BG_MAIN,  # 内容区 (bg-main #0f1117)
    COL_BORDER_BRAND,
    COL_BORDER_SUBTLE,
    COL_BORDER_VISIBLE,
    COL_BRAND,  # 品牌主色 #6495ED
    COL_BRAND_BG_10,  # 导航激活底 10% (design-system #11)
    COL_BRAND_LIGHT,  # 浅 #9DB9F3
    COL_BRAND_SOFT,  # 柔 #8FB1F0
    COL_BTN_BAR_HOVER,  # 顶栏按钮 hover 提亮 (tokens §1.6 hover-btnbar)
    COL_ERR,
    COL_ERR_BG,  # 错误提示条底 (CFG 页缺失提示)
    COL_OK,  # 成功/在线 #10b981
    COL_SWITCH_INACTIVE_THUMB,
    COL_SWITCH_INACTIVE_TRACK,
    COL_TEXT_DIM,  # 辅助文字 #a0aec0
    COL_TEXT_PRIMARY,  # 主文字原名 (ON_BRAND 引用)
    COL_TEXT_SECONDARY,  # 次文字 #e2e8f0
    COL_WARN,
    COL_WARN_BG,  # 警告提示条底
    FONT_36,
    FONT_CN,
    FONT_MONO,
    SHADOW_CARD,
)

ON_BRAND = COL_TEXT_PRIMARY        # 主色底上的文字/图标: 白字 (对比 3.5:1, 大字号可读; 2026-08 新主题)
CHIP_ADDED_BG = COL_BRAND_LIGHT     # chip 已添加态底 (浅主色)
INPUT_BORDER = COL_BORDER_VISIBLE   # 输入控件边框
INPUT_FILL = COL_BG_INPUT           # 输入控件深色填充


def find_avatar_path(csgo_dir):
    """CSGO 目录头像: platform/avatar.dat 优先, avatar1.dat 备选; 均失败返回 None"""
    if not csgo_dir:
        return None
    for name in ("avatar.dat", "avatar1.dat"):
        p = os.path.join(csgo_dir, "platform", name)
        if os.path.isfile(p):
            return p
    return None


# 主页卡片尺寸
CARD_W = 360
AVATAR_D = 100   # 头像直径 (design-system.md #5, 100px)
BTN_W = 288   # 卡片宽 80%
BTN_H = 52

# 窗口尺寸随布局切换: 主页 360×510 竖卡(窗口即卡) / 编辑 784×600 横屏, 向心步进缓动
WIN_HOME = (360, 510)
WIN_EDIT = (784, 600)
WIN_MIN = (360, 510)


def _strip_connect_arg(val: bytes) -> bytes:
    """从启动参数中剥离已有的 +connect <地址> 参数(含其前导空白), 返回清理后字节。
    无 +connect 时原样返回。用于自动进服更新时替换旧地址 (deep-review F2):
    残留/手写的旧 +connect 不清理的话, 新地址永远进不去。
    词边界: +connect 后必须紧跟空白或串尾, 防误剥 +connectivity 等参数 (deep-review 4轮 LOW5)。
    循环剥离全部 +connect (deep-review 8轮 F1): 原实现只剥第一个,
    多个 +connect 时第二个残留, 空值剥离模式清理不彻底。"""
    while True:
        low = val.lower()
        i = low.find(b"+connect")
        while i >= 0:
            j = i + len(b"+connect")
            if j == len(low) or low[j:j + 1] in (b" ", b"\t"):
                break
            i = low.find(b"+connect", j)
        if i < 0:
            return val
        j = i + len(b"+connect")
        while j < len(val) and val[j:j + 1] in (b" ", b"\t"):
            j += 1                       # 跳过 +connect 与地址之间的空白
        while j < len(val) and val[j:j + 1] not in (b" ", b"\t"):
            j += 1                       # 跳过地址 token (到下一个空白或串尾)
        k = i
        while k > 0 and val[k - 1:k] in (b" ", b"\t"):
            k -= 1                       # 向前吃掉 +connect 前的空白
        val = (val[:k] + val[j:]).strip()


def _procname_patch(ini_path, new_value):
    """临时把 [Loader] ProcName 行替换为 原值 + ' +connect <server>'
    (Loader.exe 读取该文件构建 csgo.exe 命令行, 自动进服用)。
    纯字节级行内替换: 不经过 model/编码往返, 保证无关字节零改动。
    返回 (原始行字节, patch 后新行字节) (供启动后恢复; 恢复前比对当前行,
    被用户保存覆盖时跳过恢复); 失败/无需改动返回 None。
    大小写不敏感 (通过 lowercase 副本定位, 切片仍取原字节)。"""
    nv = str(new_value or "").strip()
    try:
        with open(ini_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    low = raw.lower()
    li = low.find(b"[loader]")
    while li >= 0:
        ls0 = low.rfind(b"\n", 0, li) + 1
        le0 = low.find(b"\n", li)
        if le0 < 0:
            le0 = len(low)
        if low[ls0:li].strip() == b"" and low[li:le0].strip() == b"[loader]":
            break   # 找到真正的 section 头行
        li = low.find(b"[loader]", li + 1)   # 注释/值里的误匹配, 继续找
    if li < 0:
        return None
    # section 结束: 下一个真正的 section 头行 (行首到 [ 只有空白)。
    # 原实现找任意 [ 会被段内注释/值里的 [ 提前截断 (deep-review F1 同族加固)
    sec_end = len(raw)
    ni = li + 8
    while True:
        ni = low.find(b"[", ni)
        if ni < 0:
            break
        nls = low.rfind(b"\n", 0, ni) + 1
        if low[nls:ni].strip() == b"":
            sec_end = ni
            break
        ni += 1
    # 定位 ProcName 键行: 必须是非注释行 (行首到键名只有空白)。
    # 注释行含 procname 字样时, 原实现把 +connect 追加到注释行 (deep-review F1)
    pi = -1
    p = li
    while True:
        p = low.find(b"procname", p, sec_end)
        if p < 0:
            break
        pls = raw.rfind(b"\n", 0, p) + 1
        if raw[pls:p].strip() == b"":
            pi = p
            break
        p += 1
    if pi < 0:
        return None
    ls = raw.rfind(b"\n", 0, pi) + 1      # 行首 (含 CRLF 的 \r 之前)
    le = raw.find(b"\n", pi)              # 行尾换行符位置
    if le < 0:
        le = len(raw)
    line = raw[ls:le]                      # 原始行 (CRLF 时含行尾 \r)
    eq = line.find(b"=")
    if eq < 0:
        return None
    val_raw = line[eq + 1:]                # = 后的原始空白 + 值
    old_val = val_raw.strip()
    ws = val_raw[:len(val_raw) - len(val_raw.lstrip())]   # 仅 = 与值之间的前导空白
    # 已有 +connect (手动或上次残留): 剥离旧地址再追加新值, 保证新地址生效 (deep-review F2)
    old_val = _strip_connect_arg(old_val)
    if nv:
        new_line = line[:eq + 1] + ws + old_val + b" +connect " + nv.encode("ascii", errors="replace")
    elif old_val != val_raw.strip():
        # 自动进服已禁用 (nv 为空): 剥离上次残留的 +connect 后写回。
        # 残留来源: 启动后 10s 窗口内退出应用, poll 线程的 _procname_restore
        # 未执行 → 旧地址永久留在 rev.ini, 下次启动仍连旧服 (deep-review 7轮 task-1 HIGH)。
        # 返回 None: 剥离是清理不是临时 patch, 不进 restore 链。
        new_line = line[:eq + 1] + ws + old_val
    else:
        return None   # 无残留, 无需改动
    if line.endswith(b"\r"):   # CRLF 文件: 保留行尾 \r, 避免中间态混行尾
        new_line += b"\r"
    try:
        with open(ini_path, "wb") as f:
            f.write(raw[:ls] + new_line + raw[le:])
    except OSError:
        return None
    return (line, new_line) if nv else None


def _procname_restore(ini_path, orig_line, new_line=None):
    """启动完成后把 [Loader] ProcName 行恢复为原始字节 (csgo 命令行已固化,
    文件恢复不影响已启动进程)。失败静默: 残留 +connect 无害——
    下次启动 _procname_patch 会剥离旧地址再追加新值 (deep-review F2)。
    new_line: patch 写入的新行; 传入后先比对当前行——若已被其它方(如用户保存)
    改写则不恢复, 避免用旧行覆盖用户新值 (deep-review 4轮 LOW4)。"""
    if not orig_line:
        return
    try:
        with open(ini_path, "rb") as f:
            raw = f.read()
    except OSError:
        return
    low = raw.lower()
    li = low.find(b"[loader]")
    while li >= 0:
        ls0 = low.rfind(b"\n", 0, li) + 1
        le0 = low.find(b"\n", li)
        if le0 < 0:
            le0 = len(low)
        if low[ls0:li].strip() == b"" and low[li:le0].strip() == b"[loader]":
            break   # 找到真正的 section 头行
        li = low.find(b"[loader]", li + 1)   # 注释/值里的误匹配, 继续找
    if li < 0:
        return
    # section 结束: 下一个真正的 section 头行 (行首到 [ 只有空白), 与 _procname_patch 一致
    sec_end = len(raw)
    ni = li + 8
    while True:
        ni = low.find(b"[", ni)
        if ni < 0:
            break
        nls = low.rfind(b"\n", 0, ni) + 1
        if low[nls:ni].strip() == b"":
            sec_end = ni
            break
        ni += 1
    # 定位 ProcName 键行: 必须是非注释行 (与 _procname_patch 一致, deep-review F1)
    pi = -1
    p = li
    while True:
        p = low.find(b"procname", p, sec_end)
        if p < 0:
            break
        pls = raw.rfind(b"\n", 0, p) + 1
        if raw[pls:p].strip() == b"":
            pi = p
            break
        p += 1
    if pi < 0:
        return
    ls = raw.rfind(b"\n", 0, pi) + 1
    le = raw.find(b"\n", pi)
    if le < 0:
        le = len(raw)
    # 启动窗口期(≤10s)内文件可能被用户保存覆盖: 当前行不是 patch 写入的行时跳过,
    # 避免用旧行覆盖用户新值 (deep-review 4轮 LOW4)
    if new_line is not None and raw[ls:le] != new_line:
        return
    try:
        with open(ini_path, "wb") as f:
            f.write(raw[:ls] + orig_line + raw[le:])
    except OSError:
        pass


def _screen_center():
    """逻辑像素屏幕中心。DPI-unaware 进程的 GetSystemMetrics 返回虚拟像素,
    与 Flutter 窗口逻辑像素同尺度(125%/150% 缩放下数值一致);
    失败返回 None → 调用方退化为保持原中心。"""
    try:
        import ctypes
        sw = ctypes.windll.user32.GetSystemMetrics(0)   # SM_CXSCREEN
        sh = ctypes.windll.user32.GetSystemMetrics(1)   # SM_CYSCREEN
        return sw / 2, sh / 2
    except Exception:  # noqa: BLE001 - ctypes 调用兜底, 失败退化为保持原中心
        return None


def _preset_src_dir() -> str | None:
    """s0up 预设备份源 (CFG 页一键重新植入 / 打包链共用):
    开发 = 仓库 assets/s0up_preset; 打包后 = 安装目录 assets/s0up_preset (installer.iss 随包)。"""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cands = [
        os.path.join(here, "assets", "s0up_preset"),
        os.path.join(os.path.dirname(sys.executable), "assets", "s0up_preset"),
    ]
    for c in cands:
        if os.path.isdir(c):
            return c
    return None


def main(page: ft.Page):
    page.title = "Rev.Ini 编辑器 · CS:GO 配置工具"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=COL_BRAND, font_family=FONT_CN)
    page.padding = 0
    page.bgcolor = ft.Colors.TRANSPARENT
    # 窗口背景透明 (2026-08-23 实机定位: bgcolor 不透明后 Flutter 窗口点击事件失效,
    # 用户反馈"设置按钮有悬停反馈但点击没反应", 日志确认事件未到 Python)。
    # 黑边问题已随矩形化消失 — 容器无圆角铺满窗口, 窗口背景不外露, 无需不透明兜底
    page.window.bgcolor = ft.Colors.TRANSPARENT
    page.window.width, page.window.height = WIN_HOME
    page.window.min_width, page.window.min_height = WIN_MIN
    page.window.frameless = True
    page.window.shadow = False   # 关窗口阴影: frameless+透明背景下 DWM 阴影在圆角边缘
    # 渲染成绿色/青色光晕(用户报告"一圈绿色光晕", 2026-08), 关闭后消失
    # 窗口图标: 任务栏/Alt+Tab 显示 (Flutter 引擎默认图标, 2026-08 用户反馈)
    # 打包版 = exe 旁 icon.ico; 开发版 = packaging/assets/revini.ico
    _icon_candidates = [
        os.path.join(os.path.dirname(sys.executable), "icon.ico"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "packaging", "assets", "revini.ico"),
    ]
    for _ic in _icon_candidates:
        if os.path.isfile(_ic):
            page.window.icon = _ic
            break

    # -- 状态 --
    # 播种 csgo_dir: 自动定位优先, 未命中回退用户持久化目录 (deep-review 7轮 工具链 F4:
    # 原只由 find_csgo_dir() 播种, get_user_csgo_dir() 仅被 locate_rev_ini() 消费 —
    # 持久化目录的 rev.ini 缺失/损坏时工具页/启动报"未定位", 尽管该目录有 startgame.bat)
    auto_dir = find_csgo_dir()
    if not auto_dir:
        from app.settings import get_user_csgo_dir
        auto_dir = get_user_csgo_dir() or ""
    st = {"ini_path": "", "csgo_dir": auto_dir,
          "cfg_dirty": False,
          "dir_source": "自动定位" if auto_dir else "未定位",
          "loaded_name": "NO FILE LOADED", "dirty": False}
    model = None
    field_rows = []  # [(field, value_ref, control)]
    nav_index = 0

    # -- UI 引用 --
    # 状态栏 (design-system.md #26): 常态仅绿勾图标, 无文字 (v1.16 定稿);
    # status_msg 仅错误时显示 (set_status err 分支), status_icon 错误时切红 ERROR 图标
    status_msg = ft.Text("", size=12, color=COL_ERR)
    status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=COL_OK)
    # 编码选择: ui.enc_group 自绘分段 (design-system #27)。原 SegmentedButton
    # 亮蓝实心被用户反馈"难看"且选中/未选中无法分离样式 (0.86.5 style 整体应用),
    # 改为 ghost 底容器 + 20% 主色浅底选中段 (2026-08 UI 审查)
    enc_selector = ui.enc_group([("gbk", "ANSI"), ("utf-8", "UTF-8")], "gbk",
                                on_change=lambda v: _on_enc_change(v))
    save_btn = None   # 实际定义在标题栏构建处 (editor_head, 2026-08 新设计: 保存移顶栏)
    content_area = ft.Container(expand=True, bgcolor=COL_BG_MAIN)

    # -- 工具函数 --
    def set_status(text, ok=False, err=False):
        # 仅图标定稿 (v1.16): 成功/普通状态不显示文字, 只留绿勾;
        # 错误时显示中文错误文字 + 红色 ERROR 图标 (临时显示, 可被下次状态覆盖)
        if ok:
            status_msg.value = ""
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = COL_OK
        elif err:
            status_msg.value = text
            status_msg.color = COL_ERR
            status_icon.name = ft.Icons.ERROR_OUTLINE
            status_icon.color = COL_ERR
        else:
            status_msg.value = ""
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = COL_OK
        page.update()

    # 临时提示 (2026-08 保存反馈): v1.16 常态仅图标, 但保存等关键操作无任何
    # 文字反馈会显得"没反应"(用户反馈 CFG 保存状态栏不提示) — 显示 3 秒后自动清除
    _flash_seq = {"n": 0}

    def _flash_status(text, err=False):
        _flash_seq["n"] += 1
        seq = _flash_seq["n"]
        status_msg.value = text
        status_msg.color = COL_ERR if err else COL_OK
        status_icon.name = ft.Icons.ERROR_OUTLINE if err else ft.Icons.CHECK_CIRCLE
        status_icon.color = COL_ERR if err else COL_OK
        page.update()
        threading.Timer(3.0, lambda: _clear_flash(seq)).start()

    def _clear_flash(seq):
        if seq != _flash_seq["n"]:
            return   # 已有更新的提示, 不提前覆盖
        def _do():
            try:
                status_msg.value = ""
                page.update()
            except Exception:  # noqa: BLE001, S110 - 清除兜底
                pass
        try:
            page.run_thread(_do)
        except Exception:  # noqa: BLE001, S110 - 清除兜底
            pass

    def confirm_discard(on_confirm, title="未保存的修改", message="当前修改尚未保存。继续将丢弃这些修改。"):
        """有未保存修改时弹确认; 用户确认后执行 on_confirm"""
        def _close():
            # 关键: pop_dialog 只更新 dialog 自身, 必须 page.update()
            # 否则 modal barrier 残留在屏幕上, 挡住标题栏按钮(用户报告过"无法关闭")
            page.pop_dialog()
            page.update()
        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.OutlinedButton("取消", on_click=lambda e: _close(),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),  # 矩形 (2026-08 去圆角)
                ft.FilledButton("丢弃并继续", on_click=lambda e: (_close(), on_confirm()),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),  # 矩形 (2026-08 去圆角)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
        )
        page.show_dialog(dlg)

    def guard_dirty(action):
        """dirty 时弹确认, 否则直接执行"""
        if st["dirty"]:
            confirm_discard(action)
        else:
            action()

    def update_title():
        base = "Rev.Ini 编辑器 · CS:GO 配置工具"
        page.title = ("* " if st["dirty"] else "") + base
        page.update()

    def refresh_dir():
        page.update()

    # -- 文件对话框 (PowerShell, 不依赖 tkinter) --
    def _ps_quote(s) -> str:
        """PowerShell 单引号字符串转义: 路径含 $ ` ' 等特殊字符时防截断/防注入 (M1)"""
        return "'" + str(s).replace("'", "''") + "'"

    def _ps_dialog(dialog_type, title, initial_dir="", initial_file=""):
        """dialog_type: OpenFileDialog / SaveFileDialog / FolderBrowserDialog"""
        # 所有用户可控值(title/initial_dir/initial_file)统一经 _ps_quote 转义,
        # 不再直接拼接进双引号字符串 (M1: 路径含 $ 会被当变量插值, 含 ' 会截断脚本)
        ps_code = f'''
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$d = New-Object System.Windows.Forms.{dialog_type}
$d.Title = {_ps_quote(title)}
'''
        if dialog_type in ("OpenFileDialog", "SaveFileDialog"):
            ps_code += '$d.Filter = "配置文件 (*.ini)|*.ini|所有文件 (*.*)|*.*"\n'
        if initial_dir:
            ps_code += f'$d.InitialDirectory = {_ps_quote(initial_dir)}\n'
        if initial_file:
            ps_code += f'$d.FileName = {_ps_quote(initial_file)}\n'
        if dialog_type == "FolderBrowserDialog":
            ps_code += f'$d.Description = {_ps_quote(title)}\n'
        ps_code += '''
$r = $d.ShowDialog()
if ($r -eq [System.Windows.Forms.DialogResult]::OK) {
'''
        if dialog_type == "FolderBrowserDialog":
            ps_code += '    [Console]::WriteLine($d.SelectedPath)\n'
        else:
            ps_code += '    [Console]::WriteLine($d.FileName)\n'
        ps_code += '''} else {
    [Console]::WriteLine("")
}
'''
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps_code],
                capture_output=True, text=True, timeout=300,
                encoding="utf-8",   # ps_code 已设 OutputEncoding=UTF8, 与环境 fsencoding 无关
                creationflags=subprocess.CREATE_NO_WINDOW, check=False)   # GUI 子系统下不闪控制台 (2026-08)
            out = r.stdout.strip()
            return out if out else ""
        except subprocess.TimeoutExpired:
            # 对话框被超时终止: 明确提示, 不再静默吞掉用户选择
            set_status("对话框超时(5 分钟),请重试", err=True)
            return ""
        except Exception:  # noqa: BLE001 - 对话框调用兜底, 失败返回空选择
            return ""

    def pick_open():
        d = os.path.dirname(st["ini_path"]) if st["ini_path"] else os.getcwd()
        p = _ps_dialog("OpenFileDialog", "选择 rev.ini", d)
        if p:
            if st["dirty"]:
                confirm_discard(lambda: load_file(p), title="打开新文件",
                                message=f"将打开 {os.path.basename(p)},当前未保存的修改将被丢弃。")
            else:
                load_file(p)

    def pick_folder():
        d = st["csgo_dir"] or os.getcwd()
        p = _ps_dialog("FolderBrowserDialog", "选择 CS:GO 安装目录", d)
        if p:
            from app.locator import _looks_like_csgo_dir

            def _apply():
                st["csgo_dir"] = p
                st["dir_source"] = "用户指定"
                ok = set_user_csgo_dir(p)
                if not ok:
                    # 持久化失败: 会话内仍生效, 但重启后遗忘 (deep-review 7轮 工具链 F3)
                    set_status("目录已使用,但保存到本机失败(重启后需重新指定)", err=True)
                    refresh_dir()
                    ini = os.path.join(p, "rev.ini")
                    if os.path.isfile(ini):
                        load_file(ini)
                    return
                refresh_dir()
                ini = os.path.join(p, "rev.ini")
                if os.path.isfile(ini):
                    load_file(ini)
                set_status(f"已指定目录: {p}", ok=True)

            if not _looks_like_csgo_dir(p):
                # 非 CSGO 目录: 弹确认让用户知情选择, 而不是警告后被成功消息瞬间覆盖 (deep-review F6)
                def _close():
                    page.pop_dialog()
                    page.update()
                dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("目录不像 CS:GO 安装目录"),
                    content=ft.Text(f"{p} 未检测到 csgo.exe。仍要使用该目录吗?\n"
                                    "(启动游戏/修复工具可能无法正常定位)"),
                    actions=[
                        ft.OutlinedButton("取消", on_click=lambda e: _close(),
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),  # 矩形 (2026-08 去圆角)
                        ft.FilledButton("仍然使用", on_click=lambda e: (_close(), guard_dirty(_apply)),
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))),  # 矩形 (2026-08 去圆角)
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                    shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
                )
                page.show_dialog(dlg)
            else:
                guard_dirty(_apply)

    def pick_save():
        d = os.path.dirname(st["ini_path"]) if st["ini_path"] else os.getcwd()
        p = _ps_dialog("SaveFileDialog", "保存 rev.ini", d, "rev.ini")
        if p:
            st["ini_path"] = p
            st["loaded_name"] = os.path.basename(p)
            on_save()

    # -- 核心逻辑 --
    def populate_all():
        if model is None:
            return
        for field, vr, ctrl in field_rows:
            sec, key = field["section"], field["key"]
            raw = model.get(sec, key, "")
            if raw == "" and model.has(sec, key) is False:
                raw = field.get("default", "")
            ftype = field["type"]
            if ftype == "rank":
                try:
                    lvl = int(raw)
                except (ValueError, TypeError):
                    lvl = -1
                if 1 <= lvl <= len(RANK_DISPLAY):
                    raw = rank_level_to_name(lvl)
                    vr["bad"] = False
                else:
                    # 非法段位值: 标记 bad, collect 时跳过写回, 避免触碰后覆盖原值 (deep-review F11)
                    vr["bad"] = True
            if ftype == "bool":
                # 完整真值解析(与 get_bool 一致): true/1/yes/on 均为开
                vr["v"] = str(raw).strip().lower() in ("true", "1", "yes", "on")
                if isinstance(ctrl, ft.Switch):
                    ctrl.value = vr["v"]
            elif ftype == "int":
                # 解析失败: 保留原文并标记 bad, 显示原文让用户看到真实值;
                # collect_all 对 bad 字段跳过写回, 避免把文件原值静默改成 0 (deep-review F3)
                raw_s = str(raw)
                try:
                    vr["v"] = int(raw_s)
                    vr["bad"] = False
                except ValueError:
                    vr["v"] = raw_s
                    vr["bad"] = True
                if isinstance(ctrl, ft.TextField):
                    ctrl.value = raw_s
                    ctrl.error_text = "原值非整数, 保存将保留原文" if vr.get("bad") else None
            elif ftype in ("combo", "rank"):
                vr["v"] = str(raw)
                if isinstance(ctrl, ft.Dropdown):
                    keys = [o.key for o in ctrl.options]
                    if vr["v"] in keys:
                        ctrl.value = vr["v"]
                        ctrl.error_text = None
                    else:
                        # 大小写不敏感匹配 (2026-08 实机: 文件 Language=English 大写 vs
                        # items 小写 english → 误报"不在选项中"红字; 命中则选中对应项,
                        # 不改 vr["v"], collect 时值相同不写回, 文件原值保留)
                        low_match = next((k for k in keys if str(k).lower() == vr["v"].lower()), None)
                        if low_match:
                            ctrl.value = low_match
                            ctrl.error_text = None
                        else:
                            # 原值不在选项中(rank 非法值/combo 未知值): 不静默显示默认项,
                            # 用 error_text 暴露真实值; collect 对 bad 字段跳过写回 (deep-review 4轮 M3)
                            ctrl.value = None
                            ctrl.error_text = "原值 " + repr(vr["v"]) + " 不在选项中, 保存将保留原文"
            elif ftype == "textarea":
                vr["v"] = str(raw)
                # v2 UI: ctrl 是 ft.Row([ta, gap, rec_panel]) 3:2 分栏 (deep-review 5轮 HIGH-1:
                # 旧版是 ft.Column, v2 改 Row 后 isinstance(ft.Column) 恒 False, ta.value 永不回填,
                # 用户看到的启动命令是默认值, 编辑/点 chips 后保存会覆盖文件真实 ProcName)
                if isinstance(ctrl, ft.Row) and ctrl.controls:
                    ctrl.controls[0].value = vr["v"]
                sync = vr.get("sync")
                if sync:
                    sync()
            else:
                vr["v"] = str(raw)
                if isinstance(ctrl, ft.TextField):
                    ctrl.value = vr["v"]

    def collect_all():
        if model is None:
            return
        for field, vr, _ in field_rows:
            sec, key = field["section"], field["key"]
            v = vr["v"]
            ftype = field["type"]
            if ftype == "bool":
                # 值未变则跳过,保留原文件格式(如 1/yes/on),避免静默翻转
                if model.has(sec, key) and model.get_bool(sec, key) == bool(v):
                    continue
                new = "true" if v else "false"
            elif ftype == "int":
                if vr.get("bad"):
                    # 原值非法且用户未修正: 跳过写回, 保留文件原样 (deep-review F3)
                    continue
                new = str(int(v))
                if model.has(sec, key):
                    old = model.get(sec, key).strip()
                    if len(old) > 1 and old.isdigit() and old[0] == "0":
                        new = new.zfill(len(old))
            elif ftype == "rank":
                if vr.get("bad"):
                    # 原段位值非法且未修正: 跳过写回, 保留文件原样 (deep-review F11)
                    continue
                new = str(rank_name_to_level(v)) if v in RANK_DISPLAY else str(v)
            elif ftype == "combo":
                new = str(v)
            elif ftype == "textarea":
                # 每个参数一行 → 保存时合并为一行(空格分隔),与字段描述一致
                new = " ".join(str(v).split())
            else:
                new = str(v)
            if not model.has(sec, key):
                model.set(sec, key, new)
            else:
                old = model.get(sec, key)
                # 大小写敏感字段(昵称/启动参数)不能折叠比较
                if (old or "").strip() != new.strip():
                    model.set(sec, key, new)

    def load_file(path, preloaded=None, preloaded_warning=False):
        """加载 rev.ini 到 model。成功返回 True, 失败 (OSError) 返回 False (deep-review R5)。
        preloaded/preloaded_warning: 已由工作线程解析好的 RevIni 及编码损坏警告 (M2/H1:
        _prep 线程只做磁盘 IO+解析, 此函数只做主线程 UI 应用, 避免工作线程直改控件)"""
        nonlocal model
        if preloaded is None:
            import warnings
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    preloaded = RevIni.load(path)
            except OSError as e:
                set_status(f"加载失败: {e}", err=True)
                return False
            preloaded_warning = any(issubclass(w.category, RuntimeWarning) for w in caught)
        model = preloaded
        enc_warning = preloaded_warning
        load_state["loading"] = False   # M2: 加载完成, 解除互斥(失败路径在调用方复位)
        st["ini_path"] = path
        # 仅当文件位于 CSGO 根目录时才联动 csgo_dir——否则打开外部备份/下载的 rev.ini
        # 会把启动目录改靶, 主页启动/修复工具/cfg 全部错 (deep-review F4)
        from app.locator import _looks_like_csgo_dir
        if _looks_like_csgo_dir(os.path.dirname(path)):
            st["csgo_dir"] = os.path.dirname(path)
        st["dirty"] = False
        st["loaded_name"] = os.path.basename(path)
        if enc_selector and model.source_encoding in ("gbk", "utf-8"):
            enc_selector.selected = [model.source_encoding]
            st["enc"] = model.source_encoding
        populate_all()
        refresh_dir()
        update_title()
        if enc_warning:
            set_status(f"已加载 {st['loaded_name']},编码异常,已用替换字符加载,保存前请确认备份", err=True)
        else:
            set_status(f"已加载 {st['loaded_name']}", ok=True)
        return True

    def on_save(_=None):
        if not st["ini_path"]:
            pick_save()
            return
        bak = RevIni.backup(st["ini_path"]) if os.path.exists(st["ini_path"]) else None
        collect_all()
        enc = st.get("enc") or "gbk"
        try:
            model.save(st["ini_path"], encoding=enc)
        except (UnicodeError, OSError, ValueError) as e:
            # ValueError: 未知编码 (L1: save 不再静默回退 UTF-8, 直接报错)
            set_status(f"保存失败: {e}", err=True)
            return
        st["dirty"] = False
        update_title()
        enc_label = "ANSI" if enc == "gbk" else "UTF-8"
        # 成功态不显示文字 (仅图标定稿); 文案保留供将来 tooltip/日志用
        set_status(f"已保存 {st['loaded_name']} [{enc_label}]" +
                   (" (已备份)" if bak else ""), ok=True)
        # 0.86.5 Button 无 text 属性(只有 content), 改 content 才推送 UI (用户实测 2026-08)
        save_btn.content = "已保存"
        page.update()
        # Timer 回调是工作线程, 控件变更走 run_thread 回主线程 (项目规则, H1)
        threading.Timer(1.5, lambda: page.run_thread(
            lambda: (setattr(save_btn, 'content', '保存'), page.update()))).start()

    def mark_dirty(_=None):
        if not st["dirty"]:
            st["dirty"] = True
            update_title()

    def _on_enc_change(v):
        """编码分段切换 (ui.enc_group 自绘, 直接传 value 字符串)。
        白名单校验: 只认 gbk/utf-8, 未知值保持原编码, 避免污染 st['enc'] (L1)"""
        if v in ("gbk", "utf-8"):
            st["enc"] = v
        page.update()

    # 当前编码(默认 gbk, 加载文件后随 source_encoding 更新)
    st["enc"] = "gbk"

    # -- 按钮回调 --
    def on_open_file(_=None):
        pick_open()

    def on_pick_dir(_=None):
        pick_folder()

    def on_open_cfg(_=None):
        cfg = find_cfg_dir(st["csgo_dir"])
        if not cfg:
            set_status("未定位 cfg 文件夹", err=True)
            return
        try:
            os.startfile(cfg)
        except OSError as e:
            # 目录被删/权限受限时给出反馈, 而不是按钮静默无反应 (deep-review F8)
            set_status(f"打开 cfg 文件夹失败: {e}", err=True)
            return
        set_status(f"已打开: {cfg}", ok=True)

    # save_btn 实际定义在 editor_head (2026-08 新设计: 保存移顶栏), on_click 在
    # 定义处接线 (on_save 已在此前定义, 见 editor_head 构建)

    # -- 字段行构建 --
    def build_field_row(field):
        sec, key, label = field["section"], field["key"], field["label"]
        desc, ftype, default = field.get("desc", ""), field["type"], field.get("default", "")
        code_text = f"{sec}.{key}"
        vr = {"v": str(default) if default is not None else ""}

        if ftype == "bool":
            val = bool(default)
            vr["v"] = val
            ctrl = ft.Switch(value=val,
                active_color=ft.Colors.WHITE, active_track_color=COL_BRAND,   # 开启: 主色轨道+白滑块
                inactive_thumb_color=COL_SWITCH_INACTIVE_THUMB,
                inactive_track_color=COL_SWITCH_INACTIVE_TRACK,
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))
        elif ftype == "rank":
            # 伪装段位: 选项为 RANK_DISPLAY 段位名, 存储值 = 1-18 数字(保存时转换)
            opts = [ft.dropdown.Option(key=name, text=name) for name in RANK_DISPLAY]
            dflt_name = rank_level_to_name(default) if isinstance(default, int) else str(default)
            # 合法选择必须清除 bad, 否则非法原值字段永久无法通过 UI 修改 (deep-review R2)
            ctrl = ui.select_dark(
                opts, selected=dflt_name, width=236, height=64,
                filled=True, fill_color=INPUT_FILL, border_color=INPUT_BORDER,
                on_select=lambda e: (vr.__setitem__("v", e.control.value),
                                     vr.__setitem__("bad", False),
                                     setattr(e.control, "error_text", None), mark_dirty()))
        elif ftype in ("combo",):
            items = field.get("items", [])
            dm = field.get("display_map") or {}   # M4: 未提供 display_map 时不能 .get() None
            opts = [ft.dropdown.Option(key=i, text=dm.get(i, i)) for i in items]
            ctrl = ui.select_dark(
                opts, selected=str(default) if default else (items[0] if items else ""),
                width=236, height=64, filled=True, fill_color=INPUT_FILL,
                border_color=INPUT_BORDER,
                on_select=lambda e: (vr.__setitem__("v", e.control.value),
                                     setattr(e.control, "error_text", None), mark_dirty()))
        elif ftype == "int":
            # 非法输入(非整数/超范围)显示 error_text 而非静默转 0; 支持负数 (deep-review F3/R8)
            def _on_int_change(e, vr=vr):
                v = e.control.value.strip()
                try:
                    iv = int(v)   # int 兼容 "+5"/"-5", 拒绝 "--5"/"1e3"/"" 等
                except ValueError:
                    vr["bad"] = True
                    e.control.error_text = "请输入整数"
                    mark_dirty()
                    e.control.update()
                    return
                lo, hi = field.get("lo") or 0, field.get("hi") or 0
                if (lo or hi) and not (lo <= iv <= hi):
                    vr["bad"] = True
                    e.control.error_text = f"范围 {lo}~{hi}"
                    mark_dirty()
                    e.control.update()
                    return
                vr["v"] = iv
                vr["bad"] = False
                e.control.error_text = None
                mark_dirty()
                e.control.update()
            vr["bad"] = False
            ctrl = ui.input_dark(
                value=str(default) if default else "0",
                width=236, height=None,   # 保持 flet 默认高度 ~63px (用户否决过 40px 扁框)
                on_change=_on_int_change)
        elif ftype == "textarea":
            ta = ui.input_dark(
                value=str(default) if default else "",
                placeholder=field.get("placeholder") or None,   # 占位符接线 (视觉审计 2026-08: 原未传入)
                multiline=True, mono=True, font_size=16,
                min_lines=3, max_lines=6,   # 原内联实现的行数 (3-6), 迁移组件不改变视觉
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty(), _sync_chips()))
            # 推荐参数 chips (design-system.md #18): 点击 toggle 添加/移除
            chip_refs = []
            def _args_in_cur(args, cur):
                """chip 参数是否已存在: 按空白分词后集合比较(子串匹配会误判 -high vs -highp)"""
                return set(args.split()) <= set(cur.split())

            def _remove_args(args, cur):
                """按 token 移除 chip 参数, 保留其余参数顺序"""
                remove = set(args.split())
                return " ".join(t for t in cur.split() if t not in remove)
            def _sync_chips():
                cur = ta.value or ""
                for cdef, chip in chip_refs:
                    chip.set_added(_args_in_cur(cdef.get("args", "").strip(), cur))
                page.update()
            vr["sync"] = _sync_chips   # populate_all 加载后同步一次 chip 状态
            def make_cc(c):
                def on_chip(_=None):
                    args = c.get("args", "").strip()
                    cur = ta.value.strip()
                    if _args_in_cur(args, cur):
                        # 移除
                        ta.value = _remove_args(args, cur)
                    else:
                        # 追加 (单空格分隔)
                        ta.value = (cur + " " + args).strip() if cur else args
                    vr["v"] = ta.value
                    mark_dirty()
                    _sync_chips()
                    page.update()
                return on_chip
            chips = []
            for c in field.get("chips", []):
                chip = ui.Chip(c["label"], added=_args_in_cur(c.get("args", "").strip(),
                                                              str(default).strip()),
                               on_toggle=lambda label, added, cc=c: make_cc(cc)())
                chip_refs.append((c, chip))
                chips.append(chip)
            # 左右分栏 3:2 (design-system.md #20 LaunchSplit): 左=textarea 手动输入,
            # 右=RecPanel 推荐启动项(竖排 chips 单行省略)。expand 比例分配宽度:
            # ta expand=3 (左), 间隔 14px, rec_panel expand=2 (右)。
            # 组件库实现 (deep-review 7轮 F4: 原内联堆砌, 抽 rec_panel/launch_split)
            ctrl = ui.launch_split(ta, ui.rec_panel(chips))
        else:
            # max_length 应用字段定义的限制 (deep-review F10: 原实现忽略 maxlen,
            # 超长昵称可保存并在主页撑爆固定 360×510 布局)
            ctrl = ui.input_dark(
                value=str(default) if default else "",
                width=236, height=None,   # 保持 flet 默认高度 ~63px (用户否决过 40px 扁框)
                max_length=field.get("maxlen") or None,
                placeholder=field.get("placeholder") or None,   # 占位符接线 (视觉审计 2026-08)
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))

        if ftype == "textarea":
            # 多行字段卡片 (design-system.md #20 LaunchSplit): 加载器启动命令卡,
            # 通栏不参与双列网格; 内部 ctrl 已是 左textarea:右RecPanel 3:2 分栏
            row = ft.Container(
                content=ft.Column([
                    ft.Text(code_text, size=11, color=COL_BRAND_LIGHT, opacity=0.8,
                            font_family=FONT_MONO),
                    ft.Text(label, size=14, weight=ft.FontWeight.W_700),
                    ft.Text(desc, size=12, color=COL_TEXT_DIM, opacity=0.85) if desc else ft.Text(""),
                    ft.Container(height=6),
                    ctrl,
                ], tight=True, spacing=2),
                bgcolor=COL_CARD,  # 矩形 (2026-08 去圆角)
                border=ft.Border(top=ft.BorderSide(1, COL_BORDER_SUBTLE),
                                 right=ft.BorderSide(1, COL_BORDER_SUBTLE),
                                 bottom=ft.BorderSide(1, COL_BORDER_SUBTLE),
                                 left=ft.BorderSide(1, COL_BORDER_SUBTLE)),
                padding=ft.padding.Padding(left=16, top=16, right=16, bottom=16),
                margin=ft.margin.Margin(top=4, bottom=4, left=0, right=0))
            # hover 微交互 (LaunchSplit 内联卡无组件自带 hover, 手动加):
            # 卡片提亮一档 + 品牌边框 (design-system.md #14 同款)
            row.on_hover = lambda e, r=row: (
                setattr(r, "bgcolor", COL_BG_GHOST_2 if e.data == "true" else COL_CARD),
                setattr(r, "border", ft.Border(
                    top=ft.BorderSide(1, COL_BORDER_BRAND if e.data == "true" else COL_BORDER_SUBTLE),
                    right=ft.BorderSide(1, COL_BORDER_BRAND if e.data == "true" else COL_BORDER_SUBTLE),
                    bottom=ft.BorderSide(1, COL_BORDER_BRAND if e.data == "true" else COL_BORDER_SUBTLE),
                    left=ft.BorderSide(1, COL_BORDER_BRAND if e.data == "true" else COL_BORDER_SUBTLE))),
                r.update())
        else:
            # 单字段卡片 (design-system.md #14 ConfigCard): 纵向 — 标题行+键名在上, 控件在下
            # desc 固定 2 行高 (HTML field-grid 对齐: 双列卡 desc 行数不同会撑高卡片,
            # 用户反馈 2026-08 界面语言/自动进入服务器大小不一致)
            # 组件库实现 (rules.md §1, deep-review 5轮 MEDIUM-5): ui.config_card 支持
            # title_expand(标题撑满+键名徽章贴右) 与 desc_lines(固定行高容器, 双列等高);
            # hover 由组件自带 (deep-review 6轮: 不再手动覆盖, 消除双份实现)
            row = ui.config_card(
                title=label, desc=desc, tag=code_text,
                control=ft.Container(content=ctrl, alignment=ft.alignment.Alignment(0, 0)),
                title_expand=True, desc_lines=2,
            )
            row.margin = ft.margin.Margin(top=4, bottom=4, left=0, right=0)
        field_rows.append((field, vr, ctrl))
        return row

    def build_page(group):
        code_sec = group["fields"][0]["section"] if group.get("fields") else "GENERAL"
        # 页头 (design-system.md #12 PageHead): 组件库实现, 不再内联堆砌 (deep-review 7轮 F4)
        items = [ui.page_head(code_sec, group["title"], group.get("desc", ""))]
        # 字段双列网格 (design-system.md #13 FieldGrid): 组件库实现。
        # STRETCH 在 ListView 无界高度下塌陷 (两次实测 2026-08) → 用固定卡片高度:
        # 内容已统一 (desc 固定 2 行 36px + 控件统一 height=64), 卡片高度恒定 = 等高
        # (deep-review 7轮 F4: 原注释误写 height=40, 实际 Dropdown/TextField 均 64)
        return ui.field_grid(group.get("fields", []), build_field_row, header=items[0])

    def build_tools_page(group):
        from app.tools import REPAIR_TOOLS, run_tool
        items = [ui.page_head("TOOLS", group["title"], group.get("desc", ""))]

        # 执行超时设置 (2026-08): 脚本运行超过该秒数会被强制终止进程树
        # 默认 120s; 存字符串便于直接显示, 读取时解析+钳位
        timeout_field = ft.TextField(
            value="120", width=110, text_align=ft.TextAlign.CENTER,   # 数字居中 (用户指定 2026-08)
            label="执行超时(秒)", label_style=ft.TextStyle(size=11),
            border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
            border_radius=0,   # 方形 (2026-08 全 UI 去圆角)
        )

        def _parse_timeout() -> float:
            """解析超时输入: 非法/超范围回退默认 120s, 钳位 5~600s"""
            try:
                t = float((timeout_field.value or "").strip())
            except (TypeError, ValueError):
                return 120.0
            return max(5.0, min(600.0, t))

        def make_runner(tool, run_btn, status_txt):
            def run_tool_clicked(_=None):
                d = st["csgo_dir"] or find_csgo_dir() or ""
                if not d or (tool.file is not None and not os.path.isfile(os.path.join(d, tool.file))):
                    set_status(f"未定位 {tool.file or tool.name}", err=True)
                    return
                timeout = _parse_timeout()
                def _run():
                    # ui.RunButton 的 content 是 Row([Icon, Text]) — 用 set_busy 驱动
                    # 禁用+图标+文案, 直接赋字符串会破坏结构丢图标 (deep-review 6轮回归)
                    run_btn.set_busy(True)
                    status_txt.value = "运行中…"
                    status_txt.color = COL_WARN
                    page.update()

                    def on_done(ok, output):
                        # run_tool 的回调在工作线程触发, UI 变更统一回主线程 (H1)
                        page.run_thread(
                            lambda: _apply_tool_result(ok, output))

                    def _apply_tool_result(ok, output):
                        run_btn.set_busy(False)
                        if ok:
                            status_txt.value = "完成"
                            status_txt.color = COL_OK
                            set_status(f"完成: {tool.name}", ok=True)
                        else:
                            status_txt.value = "失败"
                            status_txt.color = COL_ERR
                            set_status(f"失败: {tool.name}: {output[:120]}", err=True)
                        page.update()

                    if not run_tool(d, tool, on_done=on_done, timeout=timeout):
                        # 脚本缺失/无法启动 (启动瞬间文件被删/占用): on_done 不会被回调,
                        # 必须在这里恢复按钮状态, 否则永久卡"运行中…" (2026-08 用户反馈)
                        page.run_thread(lambda: (
                            run_btn.set_busy(False),
                            setattr(status_txt, "value", "无法启动"),
                            setattr(status_txt, "color", COL_ERR),
                            set_status(f"无法启动: {tool.file or tool.name}", err=True),
                            page.update()))
                if st["dirty"]:
                    confirm_discard(_run, title="运行修复工具",
                                    message="配置尚未保存,工具将在旧配置目录上运行。仍要继续吗?")
                else:
                    _run()

            return run_tool_clicked

        # 超时设置行: 放工具列表最前, 与卡片同宽同圆角 (2026-08)
        items.append(ft.Container(
            content=ft.Row([
                timeout_field,
                ft.Text("超过该秒数未结束将被强制终止, 防止脚本卡死/注册表修改悬空",
                        size=12, color=COL_TEXT_DIM, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COL_CARD,  # 矩形 (2026-08 去圆角)
            border=ft.Border(top=ft.BorderSide(1, COL_BORDER_SUBTLE),
                             right=ft.BorderSide(1, COL_BORDER_SUBTLE),
                             bottom=ft.BorderSide(1, COL_BORDER_SUBTLE),
                             left=ft.BorderSide(1, COL_BORDER_SUBTLE)),
            padding=ft.padding.Padding(left=16, top=12, right=16, bottom=12),
            margin=ft.margin.Margin(left=0, top=4, right=0, bottom=4)))

        # 工具卡片 2×2 网格 (design-system.md #21 ToolCard, HTML tool-grid):
        # 顶行(类别标签+风险标签 | 运行按钮) → 工具名 → 状态文本
        # 描述与「执行: xxx」已删 (用户不需要知道内部命令)
        # 组件库实现 (rules.md §1: 禁止页面内联伪组件, deep-review 5轮 MEDIUM-5):
        # ui.tool_card 内部用 cat_tag/risk_tag/RunButton/tool_status,
        # card._run_btn / card._status 供 make_runner 驱动状态
        tool_cards = []
        for tool in REPAIR_TOOLS:
            card = ui.tool_card(tool.category, tool.risk, tool.name, expand=True)
            run_btn = card._run_btn  # type: ignore[attr-defined]
            status_txt = card._status  # type: ignore[attr-defined]
            run_btn.on_click = make_runner(tool, run_btn, status_txt)
            tool_cards.append(card)

        # 2 列一行: 每对卡并排 (HTML tool-grid 2×2; STRETCH 会塌陷, 同字段页)
        for i in range(0, len(tool_cards), 2):
            pair = tool_cards[i:i + 2]
            if len(pair) == 1:
                # 单卡也包 Row 约束宽度, 防撑满整行 (同 CFG 页单卡修复, 2026-08-23)
                items.append(ft.Row([pair[0]], spacing=0))
            else:
                items.append(ft.Row([
                    pair[0],
                    ft.Container(width=10),
                    pair[1],
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
        items.append(ft.Container(
            # 风险告知精简 (2026-08 UI 审查): 删内部实现细节(调用官方脚本/输出),
            # 只留对普通玩家有知情价值的注册表修改提示
            content=ft.Text("修复工具会修改本机的 CS:GO 配置与系统注册表,请按需使用。",
                            size=12, opacity=0.85),
            padding=ft.padding.Padding(left=0, top=8, right=0, bottom=0)))
        return ft.ListView(controls=items, padding=ft.padding.Padding(left=20, top=20, right=20, bottom=40), expand=True)

    # -- CFG 配置页 (2026-08-22 定稿: 表单化编辑 s0up 预设, 见 docs/DESIGN.md CFG 配置) --
    # 4 组 23 字段: 鼠标(auto.cfg)/准星(crosshair.cfg)/声音(auto.cfg)/性能(auto.cfg);
    # 范围校验标红不保存; 保存前 .bak 备份; 独立 dirty; ProcName +exec 检测; 缺失一键植入
    cfg_values: dict[str, str] = {}       # 命令名 -> 当前显示值 (页面快照)
    cfg_vrs: dict[str, dict] = {}         # 命令名 -> {"v": str, "bad": bool}
    cfg_missing: list[str] = []           # 缺失的预设文件
    cfg_file_values: dict[str, str] = {}  # scale 字段的原始文件值 (防 round 往返丢精度)

    def _cfg_load():
        """从 cfg 目录读取当前值 (打开页面/重新植入后调用)"""
        cfg_values.clear()
        cfg_vrs.clear()
        cfg_missing.clear()
        cfg_file_values.clear()
        cfg_dir = find_cfg_dir(st["csgo_dir"])
        if not cfg_dir or not os.path.isdir(cfg_dir):
            cfg_missing.extend(["auto.cfg", "crosshair.cfg"])
        else:
            for fn in ("auto.cfg", "crosshair.cfg"):
                p = os.path.join(cfg_dir, fn)
                if os.path.isfile(p):
                    for k, (v, _, _) in parse_cfg(p).items():
                        f = FIELD_INDEX.get(k)
                        if f and f.scale != 1.0:
                            cfg_file_values[k] = v   # 原始文件值 (如 "255")
                            # 文件值 → 显示值 (透明度 255 → 100%)
                            try:
                                v = str(round(float(v) / f.scale))
                            except ValueError:
                                pass
                        cfg_values[k] = v
                else:
                    cfg_missing.append(fn)
        for _, fs, _ in GROUPS:
            for f in fs:
                dflt = str(f.default) if f.default is not None else ""
                cfg_vrs[f.key] = {"v": cfg_values.get(f.key, dflt), "bad": False}

    def _cfg_procname_has_exec() -> bool:
        """rev.ini ProcName 是否已含 +exec auto.cfg (启动参数最后执行, 预设才真正生效)"""
        if not st["csgo_dir"]:
            return True
        ini = os.path.join(st["csgo_dir"], "rev.ini")
        if not os.path.isfile(ini):
            return True
        try:
            with open(ini, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
            m = re.search(r"(?im)^\s*ProcName\s*=.*$", txt)
            return bool(m and "+exec auto.cfg" in m.group(0))
        except OSError:
            return True

    def _cfg_add_exec(_=None):
        """rev.ini ProcName 追加 +exec auto.cfg (备份后写回, 字节级保留 CRLF)"""
        if not st["csgo_dir"]:
            set_status("未定位游戏目录", err=True)
            return
        ini = os.path.join(st["csgo_dir"], "rev.ini")
        if not os.path.isfile(ini):
            set_status("未找到 rev.ini", err=True)
            return
        try:
            with open(ini, "rb") as f:
                data = f.read()
            # 字节级: bytes([13])/bytes([10]) 代替反斜杠r/反斜杠n字面量 (CRLF 文件字节替换会吞反斜杠r)
            lines = data.split(bytes([10]))
            idx = None
            for i, ln in enumerate(lines):
                s = ln.lstrip()
                if s.lower().startswith(b"procname") and b"=" in s:
                    idx = i
                    break
            if idx is None:
                set_status("rev.ini 无 ProcName 行", err=True)
                return
            line = lines[idx]
            ends_cr = line.endswith(bytes([13]))
            body = line[:-1] if ends_cr else line
            if b"+exec auto.cfg" in body.lower():
                set_status("启动参数已包含 +exec auto.cfg", ok=True)
                return
            bak = ini + ".bak_" + time.strftime("%Y%m%d%H%M%S")
            shutil.copy2(ini, bak)
            new_body = body.rstrip() + b" +exec auto.cfg"
            lines[idx] = new_body + (bytes([13]) if ends_cr else b"")
            with open(ini, "wb") as f:
                f.write(bytes([10]).join(lines))
            set_status("已添加启动参数 +exec auto.cfg, 重启游戏生效", ok=True)
        except OSError as exc:
            set_status(f"添加失败: {exc}", err=True)

    def _cfg_restore_preset(_=None):
        """从随包 assets/s0up_preset 重新植入缺失的预设文件"""
        src = _preset_src_dir()
        cfg_dir = find_cfg_dir(st["csgo_dir"])
        if not src or not os.path.isdir(src):
            set_status("预设备份缺失, 无法重新植入", err=True)
            return
        if not cfg_dir or not os.path.isdir(cfg_dir):
            set_status("未定位 CFG 目录", err=True)
            return
        n = 0
        for fn in S0UP_FILES:
            s = os.path.join(src, fn)
            d = os.path.join(cfg_dir, fn)
            if os.path.isfile(s) and not os.path.isfile(d):
                shutil.copy2(s, d)
                n += 1
        if not n:
            set_status("预设文件已齐全, 无需重新植入", ok=True)
        else:
            _cfg_load()
            content_area.content = build_cfg_page()
            page.update()
            set_status(f"已重新植入 {n} 个预设文件", ok=True)

    def _on_cfg_change(e, vr, field):
        """CFG 字段输入: 范围校验标红 + 置 dirty (与 rev.ini 字段页同模式)"""
        v = getattr(e.control, "value", "")
        vr["v"] = "" if v is None else str(v)
        ok, err = field.validate(vr["v"])
        vr["bad"] = not ok
        e.control.error_text = err if not ok else None
        st["cfg_dirty"] = True
        e.control.update()

    def _save_cfg(_=None):
        """保存 CFG: 校验 → .bak 备份 → 写回 → 提示 (dirty 清除)"""
        bad = [k for k, vr in cfg_vrs.items() if vr["bad"]]
        if bad:
            set_status(f"{FIELD_INDEX[bad[0]].label} 超出范围, 无法保存", err=True)
            return
        cfg_dir = find_cfg_dir(st["csgo_dir"])
        if not cfg_dir or not os.path.isdir(cfg_dir):
            set_status("未定位 CFG 目录", err=True)
            return
        if cfg_missing:
            set_status("预设文件缺失, 请先重新植入", err=True)
            return
        try:
            for fn in ("auto.cfg", "crosshair.cfg"):
                p = os.path.join(cfg_dir, fn)
                if os.path.isfile(p):
                    shutil.copy2(p, p + ".bak_" + time.strftime("%Y%m%d%H%M%S"))
            # 构建 {命令名: 文件值}: scale 字段换算; 未修改的 scale 字段用文件原值
            # (显示值 round 往返丢精度, 如透明度 200→显示 78→写回 199, deep-review 12轮)
            updates: dict[str, str] = {}
            for k, vr in cfg_vrs.items():
                dv = vr["v"]
                if dv == "":
                    continue
                f = FIELD_INDEX[k]
                if f.scale != 1.0:
                    if k in cfg_file_values:
                        try:
                            orig_disp = str(round(float(cfg_file_values[k]) / f.scale))
                        except ValueError:
                            orig_disp = None
                        if orig_disp is not None and dv == orig_disp:
                            updates[k] = cfg_file_values[k]   # 未修改: 用文件原值, 不经换算
                            continue
                    try:
                        updates[k] = str(round(float(dv) * f.scale + 1e-9))
                    except ValueError:
                        updates[k] = dv
                else:
                    updates[k] = dv
            apply_values(cfg_dir, updates)
            st["cfg_dirty"] = False
            # 临时提示 + 按钮文字反馈 (与 rev.ini 保存一致; 状态栏 ok 分支仅图标, 2026-08)
            _flash_status("已保存, 重启游戏生效")
            save_btn.content = "已保存"
            page.update()
            threading.Timer(1.5, lambda: page.run_thread(
                lambda: (setattr(save_btn, 'content', '保存'), page.update()))).start()
        except OSError as exc:
            set_status(f"保存失败: {exc}", err=True)

    def build_cfg_page():
        """构建 CFG 配置页: 顶部说明 + 提示条(ProcName/缺失) + 4 组表单卡片"""
        _cfg_load()
        items: list[ft.Control] = []
        # 顶部说明 (2026-08-23 用户指定: 从页底移到最上面, 进入即见适用范围)
        items.append(ft.Container(
            content=ft.Text("修改会写入 s0up 预设 (auto.cfg / crosshair.cfg), 保存前自动备份。",
                            size=12, opacity=0.85),
            padding=ft.padding.Padding(left=0, top=2, right=0, bottom=8)))
        # 提示条 1: 启动参数缺 +exec auto.cfg (预设被 config.cfg 覆盖, 2026-08 拷问 F2)
        if not _cfg_procname_has_exec():
            items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=COL_WARN),
                    ft.Text("启动参数缺少 +exec auto.cfg, 预设可能被游戏配置覆盖", size=12,
                            color=COL_TEXT_PRIMARY, expand=True),
                    ft.OutlinedButton(
                        "一键添加", on_click=_cfg_add_exec, height=28,
                        style=ft.ButtonStyle(
                            bgcolor=COL_BRAND, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=0))),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COL_WARN_BG, border=ft.Border.all(1, COL_WARN),
                padding=ft.padding.Padding(left=12, top=8, right=8, bottom=8)))
        # 提示条 2: 预设文件缺失
        if cfg_missing:
            items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=COL_ERR),
                    ft.Text(f"预设文件缺失: {'、'.join(cfg_missing)}, 可重新植入", size=12,
                            color=COL_TEXT_PRIMARY, expand=True),
                    ft.OutlinedButton(
                        "重新植入", on_click=_cfg_restore_preset, height=28,
                        style=ft.ButtonStyle(
                            bgcolor=COL_BRAND, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=0))),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COL_ERR_BG, border=ft.Border.all(1, COL_ERR),
                padding=ft.padding.Padding(left=12, top=8, right=8, bottom=8)))
        # 4 组表单卡片 (2026-08-23 显示优化: 全部控件高 64px + desc 18px 等高,
        # 所有卡片结构完全一致 → 双列整齐; RGB 合并撤销 — 并排小框高度不齐)
        for gn, fields, _ in GROUPS:
            cards = []
            for f in fields:
                vr = cfg_vrs[f.key]
                if f.kind == "enum":
                    opts = [ft.dropdown.Option(key=str(v), text=t) for v, t in f.options]
                    ctrl = ui.select_dark(
                        opts, selected=vr["v"], width=236, height=64,
                        filled=True, fill_color=INPUT_FILL, border_color=INPUT_BORDER,
                        on_select=lambda e, vr=vr, f=f: _on_cfg_change(e, vr, f))
                else:
                    # 数字字段等宽字体 + 显式 64px 高 (与下拉一致, 卡片等高)
                    ctrl = ui.input_dark(
                        vr["v"], width=236, height=64, mono=True,
                        placeholder=str(f.default) if f.default is not None else "",
                        on_change=lambda e, vr=vr, f=f: _on_cfg_change(e, vr, f))
                # desc_lines=1 强制说明行等高, 双列卡片高度对齐
                cards.append(ui.config_card(f.label, f.unit, ctrl,
                                            title_expand=True, desc_lines=1))
            # 组标题 (15px/700 与卡片标题 14px 拉开层级, 2026-08-23 显示优化)
            items.append(ft.Container(
                content=ft.Text(gn, size=15, weight=ft.FontWeight.W_700,
                                color=COL_TEXT_SECONDARY),
                padding=ft.padding.Padding(left=0, top=18, bottom=6)))
            # 双列 (2 张一行, 同字段页 field-grid); 奇数行最后一张单卡也包 Row
            # 约束内容宽度 — 直接 append 会撑满整行 648px (准星透明度卡巨宽, 用户反馈 2026-08-23)
            for i in range(0, len(cards), 2):
                pair = cards[i:i + 2]
                if len(pair) == 1:
                    items.append(ft.Row([pair[0]], spacing=0))
                else:
                    items.append(ft.Row([pair[0], ft.Container(width=10), pair[1]],
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER))
        return ft.ListView(controls=items,
                           padding=ft.padding.Padding(left=20, top=20, right=20, bottom=40),
                           expand=True)

    # -- 导航 --
    nav_content = []
    # CFG 配置页在 FIELD_GROUPS 中的索引 (保存按钮语义切换用)
    CFG_NAV_INDEX = next((i for i, g in enumerate(FIELD_GROUPS) if g.get("type") == "cfg"), -1)
    icon_map = {"tune": ft.Icons.TUNE, "play": ft.Icons.PLAY_ARROW,
                "wrench": ft.Icons.BUILD, "cfg": ft.Icons.DESCRIPTION}
    nav_items = []
    for i, g in enumerate(FIELD_GROUPS):
        icon = icon_map.get(g.get("icon_key", "wrench"), ft.Icons.BUILD)
        nav_items.append(ft.NavigationRailDestination(
            icon=ft.Icon(icon, color=COL_TEXT_DIM),
            selected_icon=ft.Icon(icon, color=COL_BRAND_SOFT),
            label=ft.Text(g["title"], size=12)))
        if g.get("type") == "cfg":
            nav_content.append(build_cfg_page())
        elif g.get("type") == "tools":
            nav_content.append(build_tools_page(g))
        else:
            nav_content.append(build_page(g))
    content_area.content = nav_content[0]

    def on_nav_change(e):
        nonlocal nav_index
        target = e.control.selected_index
        if target == nav_index:
            return
        # 离开 CFG 页且 CFG 有未保存修改: 拦截确认 (CFG 独立 dirty, 2026-08 定稿 Q5)
        def _switch():
            nonlocal nav_index
            # 离开 CFG 页且 CFG 未保存: 真实丢弃 (清 dirty + 重建页面, 下次进入重新读盘)
            # (deep-review 12轮: 原实现只切 content 未清 cfg_dirty 未重建, 确认"丢弃"后修改残留)
            if nav_index == CFG_NAV_INDEX and st["cfg_dirty"]:
                st["cfg_dirty"] = False
                nav_content[CFG_NAV_INDEX] = build_cfg_page()
            nav_index = target
            content_area.content = nav_content[nav_index]
            # 顶栏保存按钮语义随页切换: CFG 页保存 CFG, 其他页保存 rev.ini
            save_btn.on_click = _save_cfg if nav_index == CFG_NAV_INDEX else on_save
            page.update()
        if nav_index == CFG_NAV_INDEX and st["cfg_dirty"]:
            confirm_discard(_switch, title="切换页面",
                            message="CFG 配置尚未保存, 切换将丢弃这些修改。")
        else:
            _switch()

    def start_drag(_=None):
        asyncio.create_task(page.window.start_dragging())

    def on_close_window(_=None):
        """关闭窗口: 有未保存修改时先确认 (与返回按钮行为一致, 2026-08 deep-review F1),
        确认后清掉可能残留的对话框, 再真正关闭
        (deep-review R8: 先弹掉已有 modal=False 对话框, 防止确认框栈式叠加)"""
        # 先清掉可能开着的其它对话框 (F6 目录确认等), 避免确认框叠加上层挡死下层
        try:
            page.pop_dialog()
        except Exception:  # noqa: BLE001, S110 - 弹框清理兜底, 失败静默
            pass
        page.update()

        def _do_close():
            try:
                page.pop_dialog()
            except Exception:  # noqa: BLE001, S110 - 弹框清理兜底, 失败静默
                pass
            page.update()
            asyncio.create_task(page.window.destroy())

        if st["dirty"] or st["cfg_dirty"]:
            confirm_discard(_do_close, title="关闭窗口",
                            message="配置尚未保存, 关闭将丢失这些修改。")
        else:
            _do_close()

    def on_minimize(_=None):
        # 0.86.5: Window 无 minimize() 方法, 用 minimized 属性
        page.window.minimized = True
        page.update()

    # ==================== 主页启动台 ====================
    def _apply_avatar(nick):
        """头像: avatar.dat → avatar1.dat → 主界面底色圆 + 昵称首字母"""
        src = find_avatar_path(st["csgo_dir"] or find_csgo_dir())
        if src:
            # 必须固定 width/height: Image 不设尺寸会按原始分辨率渲染
            # (实测 avatar.dat 235×315 撑破布局, 盖住昵称/头衔/胶囊)
            avatar.content = ft.Image(src=src, width=AVATAR_D, height=AVATAR_D,
                                      fit=ft.BoxFit.COVER,
                                      filter_quality=ft.FilterQuality.HIGH,  # 低清 avatar.dat 缩放平滑 (2026-08 UI 审查)
                                      border_radius=AVATAR_D // 2)
        else:
            avatar.content = ft.Text((nick or "汤")[:1], size=FONT_36,
                                     color=COL_BRAND_LIGHT, weight=ft.FontWeight.W_700)

    # 头像 (100px 正圆, 矢车菊蓝浅字, 无外发光; design-system.md #5)
    avatar = ui.avatar("汤")
    # 主页昵称: 组件库 Nickname (单行+省略号, 防超长昵称撑爆固定 360×510 布局 deep-review F10)
    nick_label = ui.nickname("未定位", size=24)
    unlocated_hint = ft.Text("⚠ rev.ini 未定位, 点配置指定目录", size=12, color=COL_TEXT_DIM)
    home_err = ft.Text("", size=12, color=COL_ERR)
    # 提示行动态容器: visible=False 的 Text 实测仍占布局空间(Flet 0.86.5),
    # 隐藏时会把主页中部撑出 ~74px 空白; 改用 controls 增删, 空则完全不占位
    hint_box = ft.Column([], spacing=0, tight=True)

    def refresh_launcher():
        """切回主页时重读磁盘 rev.ini 刷新昵称。
        身份源与启动目标一致: 优先读 csgo_dir 的 rev.ini (R7: F4 修复后打开外部文件
        不再联动 csgo_dir, 若主页仍读 ini_path 外部文件, 显示 A 进游戏 B 会误导用户)"""
        # 启动目标目录的 rev.ini 是身份/启动的事实来源
        launch_ini = os.path.join(st["csgo_dir"], "rev.ini") if st["csgo_dir"] else ""
        path = launch_ini if os.path.isfile(launch_ini) else (st["ini_path"] or locate_rev_ini())
        if path and os.path.isfile(path):
            try:
                m = RevIni.load(path)
            except OSError:
                m = None
            if m is not None:
                nick = (m.get("steamclient", "PlayerName", "Player") or "").strip() or "Player"
                nick_label.value = nick
                hint_box.controls = []
                home_err.value = ""
                _apply_avatar(nick)
                # 切回主页同步启动按钮状态: 游戏运行中保持"已启动 ✓" (R6)
                if not st.get("launching"):
                    if csgo_running():
                        launch_btn.set_state("running", "游戏运行中")
                    else:
                        launch_btn.set_state("idle")
                error_epoch["n"] += 1   # 使过期的 show_home_error Timer 失效 (R6)
                page.update()
                return
        # 未定位: 昵称占位 + 灰字提示, 不弹窗
        nick_label.value = "未定位"
        hint_box.controls = [unlocated_hint]
        home_err.value = ""
        _apply_avatar("汤")
        # 未定位时按钮复位 (R6)
        if not st.get("launching"):
            launch_btn.set_state("idle")
        error_epoch["n"] += 1   # 使过期的 show_home_error Timer 失效 (R6)
        page.update()

    # 错误提示 epoch 计数: 防止过期 Timer 清掉新状态 (deep-review F7/R6)
    error_epoch = {"n": 0}

    # 编辑页加载互斥 (M2): enter_editor 的 _prep 线程正在加载时置 True,
    # show_editor 的 lazy 加载跳过, 避免工作线程与主线程双 load_file/双 populate
    load_state = {"loading": False}

    def _use_default_template():
        """载入默认模板(主线程调用): 未定位 rev.ini 时的兜底 (M2)"""
        nonlocal model
        model = RevIni.from_text(default_ini_text())
        populate_all()
        set_status("rev.ini 未找到,已载入默认模板", err=True)
        load_state["loading"] = False   # M2: 模板载入完成, 解除互斥

    def _revini_located() -> bool:
        """rev.ini 是否已定位——与 refresh_launcher 同源判定 (deep-review R6:
        原 show_home_error 用 csgo_dir 非空代理, 与 locate_rev_ini() 不一致,
        csgo_dir 已设但 rev.ini 缺失时引导被 3s 定时器永久抹掉)"""
        return bool(locate_rev_ini())

    def show_home_error(msg):
        """主页红字提示, 3s 后自动消失; 未定位时保留常驻引导 (deep-review F7/R6)"""
        error_epoch["n"] += 1
        epoch = error_epoch["n"]
        home_err.value = msg
        # 错误不抹掉常驻引导: 未定位时两者并列显示
        hint_box.controls = [home_err] + ([unlocated_hint] if not _revini_located() else [])
        page.update()

        def _clear():
            if error_epoch["n"] != epoch:
                return  # 已有新错误/刷新, 过期回调直接丢弃
            home_err.value = ""
            hint_box.controls = [unlocated_hint] if not _revini_located() else []
            page.update()

        # Timer 回调是工作线程, 控件变更走 run_thread 回主线程 (项目规则)
        threading.Timer(3.0, lambda: page.run_thread(_clear)).start()

    def _proc_exists(name: str) -> bool:
        """tasklist 查进程是否存在。bytes + 显式 gbk+replace: 环境无关 (同 csgo_running)
        CREATE_NO_WINDOW: GUI 子系统下启动 tasklist 会闪现控制台 (2026-08 用户反馈"返回时闪控制台")"""
        try:
            r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"],
                               capture_output=True, timeout=5,
                               creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            return name.lower() in r.stdout.decode("gbk", errors="replace").lower()
        except Exception:  # noqa: BLE001 - tasklist 调用兜底, 失败视为不存在
            return False

    def csgo_running():
        try:
            # PYTHONUTF8=1 时 fsencoding=utf-8, tasklist 输出 GBK → text=True 解码崩溃
            # (stdout=None + 永久返回 False + 刷 _readerthread 错误噪音, 2026-08 实测)。
            # 用 bytes + 显式 gbk+replace: 环境无关, csgo.exe 为 ASCII 不受影响。
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq csgo.exe"],
                               capture_output=True, timeout=5,
                               creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            return "csgo.exe" in r.stdout.decode("gbk", errors="replace").lower()
        except Exception:  # noqa: BLE001 - tasklist 调用兜底, 失败视为不存在
            return False


    def on_launch_click(_=None):
        """轻检查 + 启动 Loader + 轮询 csgo.exe 反馈
        (2026-08 deep-review R1/R3/R4:
        - R1: Loader.exe 带 requireAdministrator 清单, 普通 Popen 抛 WinError 740 →
          用 ShellExecuteW runas 提权启动 (方案复用自 D:\\Launcher)
        - R4: 仅 csgo.exe 判定\"已启动\"; Loader 存活只拒绝二次 Popen, 不显示假成功"""
        if st.get("launching"):
            return
        # 进程级幂等: 仅以 csgo.exe 判定游戏在运行 (Loader 生命周期不可靠, R4)
        if csgo_running():
            launch_btn.set_state("running", "游戏运行中")
            page.update()
            return
        d = st["csgo_dir"] or find_csgo_dir() or ""
        # 优先优化版 newloader.exe, 回退原版 Loader.exe (2026-08: 工具安装不覆盖原件)
        loader_exe = (os.path.join(d, "newloader.exe")
                      if d and os.path.isfile(os.path.join(d, "newloader.exe"))
                      else os.path.join(d, "Loader.exe"))
        loader_name = os.path.basename(loader_exe)
        if not d or not os.path.isfile(loader_exe):
            show_home_error(f"未定位 {loader_name}, 请先在配置页指定目录")
            return
        # Loader 已在运行 (启动窗口期/挂起残留): 拒绝二次 Popen, 显示等待提示而非假"已启动 ✓" (R4)
        if _proc_exists("Loader.exe") or _proc_exists("newloader.exe"):
            show_home_error("Loader 已在运行, 请稍候游戏启动")
            return
        # 启动目标目录的 rev.ini 是身份/启动的事实来源 (R7/M3):
        # Loader.exe 在 cwd=d 下读取的是 csgo_dir/rev.ini, 外部打开的 ini_path
        # 不会生效——存在性检查必须与启动目标同源, 避免"检查通过但游戏用旧配置"
        ini = os.path.join(d, "rev.ini")
        if not os.path.isfile(ini):
            show_home_error("启动目录下无 rev.ini, 请先在配置页指定目录")
            return
        # 自动进入服务器 (2026-08): [Loader] ConnectServer 非空时, 把
        # "+connect <ip:port>" 临时追加到启动目标 rev.ini 的 ProcName 行
        # (Loader.exe 读此文件构建 csgo.exe 命令行, deep-review R7 同源规则),
        # csgo.exe 出现后由 poll 恢复原样。失败静默, 不影响正常启动。
        proc_orig = proc_new = None
        try:
            _m = RevIni.load(ini)
            auto_join = str(_m.get("Loader", "ConnectServer", "") or "").strip()
            if auto_join:
                # patch 内部会剥离残留/手写的旧 +connect 再追加新地址 (deep-review F2),
                # 不再用 "+connect not in _proc" 短路——否则旧地址残留时新地址永远进不去
                _patched = _procname_patch(ini, auto_join)   # 助手内部拼 " +connect <server>"
                if _patched:
                    proc_orig, proc_new = _patched
            else:
                # 自动进服已禁用: 剥离上次残留的 +connect (deep-review 7轮 task-1 HIGH:
                # 启动后 10s 窗口内退出应用 → poll 的 restore 未执行, 旧地址永久残留,
                # 下次启动仍连旧服; nv="" 剥离模式返回 None 不进 restore 链)
                _procname_patch(ini, "")
        except OSError:
            pass
        try:
            subprocess.Popen([loader_exe], cwd=d)
        except OSError as e:
            if getattr(e, "winerror", None) == 740:
                # Loader 需要管理员权限 (requireAdministrator manifest):
                # ShellExecuteW runas verb 提权启动, 弹出 UAC 确认 (R1)
                try:
                    import ctypes
                    res = ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", loader_exe, "", d, 1)
                except Exception:  # noqa: BLE001 - ShellExecuteW 调用兜底, 失败归入错误路径
                    res = 0
                if res <= 32:
                    _procname_restore(ini, proc_orig, proc_new)
                    show_home_error(f"{loader_name} 需要管理员权限, 请在 UAC 弹窗中确认")
                    return
                # 提权拉起成功, fall through 到统一轮询
            else:
                _procname_restore(ini, proc_orig, proc_new)
                show_home_error(f"启动失败: {e}")
                return

        st["launching"] = True      # 防连点
        launch_btn.set_state("launching", "启动中…")
        page.update()

        def poll():
            ok = False
            for _ in range(20):          # 10s 超时, 每 0.5s 检查 (慢机器 >5s 启动常见, 2026-08 deep-review F2)
                if csgo_running():
                    ok = True
                    break
                time.sleep(0.5)
            _procname_restore(ini, proc_orig, proc_new)   # 自动进服: 恢复 ProcName (无论成败, csgo 命令行已固化)
            # 轮询线程只做检测, UI 变更统一回主线程 (H1)
            page.run_thread(lambda: _apply_poll_result(ok))

        def _apply_poll_result(ok):
            if ok:
                launch_btn.set_state("running", "游戏运行中")
            else:
                launch_btn.set_state("idle")
                # 超时反馈必须走主页可见通道 (status_bar 在主页隐藏, R3)
                show_home_error("启动超时: 未检测到 csgo.exe, 游戏可能仍在启动, 请稍候")
            st["launching"] = False
            page.update()
        threading.Thread(target=poll, daemon=True).start()

    # 启动按钮: 110px 圆形纯图标 (矢车菊蓝纯色, 无渐变无发光; design-system.md #8)
    launch_btn = ui.LaunchButton(on_click=on_launch_click, tooltip="启动游戏")
    # 服务器状态胶囊 (主页, design-system.md #7): 拉取官网状态 API (真实数据, 禁止编造)。
    # 数据源: https://cs.suchitems.top/api/status (未烬官网, 心跳脚本 heartbeat.py 60s 上报
    # Upstash Redis, 官网 status.ts 聚合为 {online, lastBeat, players, maxPlayers})
    SERVER_STATUS_API = "https://cs.suchitems.top/api/status"
    server_monitor = ui.ServerMonitor(label="离线", count="", status="offline")

    def _refresh_server():
        """拉取状态 API → 在线=绿点+人数 / 离线=灰点「离线」/ 未知=灰点「未知」。

        线程安全: 工作线程调用, 控件变更经 page.run_thread 回主线程 (项目规则 H1)。
        红线 (rules.md §4.2): online=true 才显示人数, 否则隐藏; 网络失败显示「离线」不编造。
        """
        def _do():
            label, count, status = "离线", "", "offline"
            try:
                req = urllib.request.Request(SERVER_STATUS_API, headers={
                    "User-Agent": "RevIni-Editor/1.0", "Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    d = json.loads(resp.read().decode("utf-8", "replace"))
                now_s = time.time()
                if d.get("online") is True:
                    lb = d.get("lastBeat")
                    fresh = lb is not None and now_s - float(lb) <= 180
                    if fresh:
                        status, label = "online", "在线"
                        pl, mx = d.get("players"), d.get("maxPlayers")
                        if pl is not None:
                            count = f"{pl} / {mx if mx is not None else '?'} 人"
                    else:
                        status, label = "offline", "离线"
                elif d.get("online") is False:
                    status, label = "offline", "离线"
                else:
                    status, label = "offline", "未知"
            except Exception:  # noqa: BLE001 - 网络/JSON/类型兜底(URLError/JSONDecodeError/TypeError 均归离线)
                status, label = "offline", "离线"   # 网络失败: 不编造, 显示离线
            page.run_thread(lambda: server_monitor.set_status(status, label, count))

        threading.Thread(target=_do, daemon=True).start()

    def gap(h):
        return ft.Container(height=h)

    card = ft.Container(
        width=CARD_W,
        bgcolor=COL_CARD,
        # 矩形 (2026-08 用户决策去圆角: 主页大卡 24px 圆角最显眼)
        shadow=SHADOW_CARD,
        padding=ft.padding.Padding(top=28, left=36, right=36, bottom=30),
        content=ft.Column([
            avatar,
            gap(24),
            nick_label,
            gap(14),
            server_monitor,
            gap(20),
            launch_btn,
            # 错误/引导提示 (仅出错时占位, 常驻就绪提示已删 — design-system.md)
            hint_box,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
    )

    launcher_view = ft.Container(
        expand=True,
        alignment=ft.alignment.Alignment(0, 0),
        content=card,
    )

    # -- 布局切换 (主页 ↔ 编辑页) --
    # 服务器状态轮询: 每次回主页立即刷新一次, 之后每 30s 一次 (官网 StatusCard 同频)。
    # epoch 防护: 过期 Timer 不覆盖新状态 (与 error_epoch 同模式, deep-review F7)
    server_epoch = {"n": 0}

    def _server_poll_loop():
        while True:
            time.sleep(30)
            if _server_poll_epoch["n"] == 0:
                continue   # 已停 (进编辑页后 epoch 置 0 停止轮询)
            _refresh_server()

    _server_poll_epoch = server_epoch

    def show_launcher():
        refresh_launcher()
        title_bar.content = launcher_head
        view_switcher.content = launcher_view
        status_bar.visible = False   # 主页 360×510 窗口即卡, 状态栏放不下且无功能价值
        page.window.focused = True   # 主动聚焦: frameless 窗口未聚焦时首次点击被窗口管理器吞掉 (2026-08)
        # 启动/恢复服务器状态轮询: 立即刷一次 + 后台 30s 周期 (仅主页期间)
        server_epoch["n"] += 1
        _refresh_server()
        if not getattr(_server_poll_loop, "_started", False):
            _server_poll_loop._started = True
            threading.Thread(target=_server_poll_loop, daemon=True).start()
        page.update()

    def show_editor():
        server_epoch["n"] = 0   # 停服务器状态轮询 (编辑期间不刷主页 UI)
        if model is None and not load_state["loading"]:
            # 首次进入编辑页 lazy 加载 (仅当 enter_editor 的 _prep 未在加载时;
            # M2: 否则数据由 _prep 完成后的 run_thread 回调填充, 避免双加载/双 populate)
            auto = locate_rev_ini()
            if auto:
                load_file(auto)
            else:
                _use_default_template()
        title_bar.content = editor_head
        view_switcher.content = editor_view
        status_bar.visible = True
        page.window.focused = True   # 主动聚焦: 否则返回/保存等按钮首次点击被焦点吞掉 (2026-08)
        page.update()
        # 调试开关: REVINI_START_VIEW=cfg 启动直接落在 CFG 配置页 (验证用, 平时不设)
        if os.environ.get("REVINI_START_VIEW") == "cfg":
            nav_rail.selected_index = CFG_NAV_INDEX
            content_area.content = nav_content[CFG_NAV_INDEX]
            save_btn.on_click = _save_cfg
            page.update()

    def on_back_to_launcher(_=None):
        def _go():
            nonlocal model
            # 丢弃语义要真实生效: 重载磁盘 model + 清 dirty (deep-review F5/R5)
            if st["ini_path"]:
                if os.path.isfile(st["ini_path"]):
                    if load_file(st["ini_path"]):
                        st["dirty"] = False
                    # 重载失败 (文件被锁/IO 错): 保留旧 model, 不清 dirty——
                    # 避免"已丢弃"的编辑复活且被标记为干净 (R5)
                else:
                    # 文件被外部删除: 保留内存 model (原始配置还在), 仅清 dirty (R5)
                    st["dirty"] = False
                    set_status("文件已被删除,内存配置保留,保存将重建文件", err=True)
            else:
                # 无文件(默认模板场景): 重置为干净的默认模板
                model = RevIni.from_text(default_ini_text())
                populate_all()
                st["dirty"] = False
            # CFG 页独立 dirty 一并丢弃: 清标记 + 重建页面 (下次进入重新读盘, 2026-08 定稿 Q5)
            st["cfg_dirty"] = False
            if CFG_NAV_INDEX >= 0:
                nav_content[CFG_NAV_INDEX] = build_cfg_page()
            show_launcher()               # 先切回主页卡(宽屏中居中显示)
            _animate_window(*WIN_HOME)    # 再收拢窗口包住卡片
        if st["dirty"] or st["cfg_dirty"]:
            confirm_discard(_go, title="返回启动台",
                            message="配置尚未保存, 返回将丢弃这些修改。")
        else:
            _go()

    # -- 窗口切换 (方案 B 2026-08: 一次到位 + AnimatedSwitcher 内容过渡) --
    # 逐帧窗口 resize 每帧一次 Python→Flutter 往返, 无论怎么优化都有限;
    # 改为: 窗口一次 update 到位 + body 内容用 AnimatedSwitcher(SCALE) 原生过渡。
    resize_state = {"busy": False, "pending": None}

    def _animate_window(tw, th, on_done=None):
        """窗口一次到位到目标尺寸(保持当前中心); on_done 同步执行(主线程)。
        内部 run_thread: 工作线程(Timer/轮询)调用也可靠, 窗口字段仅主线程有效 (2026-08)。
        busy 时请求排队(pending), 完成后重放最后一次 — 快速连点不丢请求
        (deep-review 7轮 F4: 原实现 busy 直接 return, 连点时的第二次切换静默丢失)。"""
        if resize_state["busy"]:
            resize_state["pending"] = (tw, th, on_done)
            return
        resize_state["busy"] = True
        page.run_thread(lambda: _do_resize(tw, th, on_done))

    def _do_resize(tw, th, on_done):
        try:
            w0 = page.window.width or WIN_HOME[0]
            h0 = page.window.height or WIN_HOME[1]
            l0 = page.window.left if page.window.left is not None else 0
            t0 = page.window.top if page.window.top is not None else 0
            # 多显示器 (deep-review 7轮 F1/F5): 保持当前窗口中心, 不跳回主屏 —
            # 用户把窗口拖到副屏后进出编辑页, 位置不丢。仅当窗口仍在启动默认
            # 角标 (10,10)/(0,0) 未摆放时才用主屏中心居中。
            if (l0, t0) in ((0, 0), (10, 10)):
                sc = _screen_center()
                cx, cy = sc if sc else (l0 + w0 / 2, t0 + h0 / 2)
            else:
                cx, cy = l0 + w0 / 2, t0 + h0 / 2
            page.window.min_width, page.window.min_height = WIN_MIN
            page.window.width = tw
            page.window.height = th
            page.window.left = round(cx - tw / 2)
            page.window.top = round(cy - th / 2)
            page.update()
        finally:
            resize_state["busy"] = False
            pending = resize_state["pending"]
            resize_state["pending"] = None
            if on_done:
                on_done()
            if pending:
                _animate_window(*pending)

    def enter_editor(_=None):
        """配置按钮: 预构建编辑页内容(与窗口展开动画并行), 动画完成只做轻量切换。
        原实现: on_done=show_editor 在动画完成瞬间首次构建几百字段控件+全量推送,
        造成切换时明显卡顿 (2026-08 用户反馈)。
        M2/H1: _prep 线程只做磁盘 IO+解析(纯数据), UI 应用统一经 run_thread 回主线程,
        load_state 互斥防双加载。"""
        if load_state["loading"]:
            # 快速连点「配置」: 首次 _prep 仍在加载时直接忽略, 防双加载 (deep-review 4轮 LOW6)
            return
        # 主线程先置互斥再起线程: 保证 _prep 未跑到置位语句时 show_editor
        # 也能看到 loading=True, 杜绝"双加载"竞态窗口 (M2)
        load_state["loading"] = True
        def _prep():
            """工作线程: 只做 locate + RevIni.load(纯数据), 不碰任何 UI 控件 (H1/M2)"""
            if model is not None:
                # 已加载过: 防重复加载 (loading 标志是给 show_editor 看的)。
                # 早退也要复位互斥 — 否则第二次进编辑页后 loading 卡 True,
                # 第三次点「配置」被入口 if load_state["loading"]: return 永久拦截
                # (deep-review 5轮 HIGH-2, 第四轮 LOW6 防连点的副作用)
                load_state["loading"] = False
                return
            auto = locate_rev_ini()
            if auto:
                import warnings
                try:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        m = RevIni.load(auto)
                except OSError as e:
                    # 先取出消息再进 lambda: 避免闭包延迟绑定 except 变量 (F841)
                    err_msg = f"加载失败: {e}"
                    # 失败路径与「未找到」路径收敛到同一兜底: 载入默认模板。
                    # 只解互斥不建模板会让 model 留 None → 编辑页空表单,
                    # 点保存 model.save() 抛未捕获 AttributeError (deep-review 7轮 F2)
                    page.run_thread(lambda: (
                        _use_default_template(),
                        set_status(f"{err_msg} · 已载入默认模板", err=True)))
                    return
                enc_w = any(issubclass(w.category, RuntimeWarning) for w in caught)
                page.run_thread(
                    lambda: load_file(auto, preloaded=m, preloaded_warning=enc_w))
            else:
                page.run_thread(_use_default_template)
        threading.Thread(target=_prep, daemon=True).start()
        _animate_window(*WIN_EDIT, on_done=show_editor)

    # -- 标题栏 --
    # 主页窗口控制: 配置齿轮(最左) + 最小化 + 关闭 (design-system.md #4: 配置入口在标题栏)
    home_win_controls = ft.Row([
        ui.win_btn(ft.Icons.SETTINGS, "配置", on_click=lambda e: enter_editor(e)),
        ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
        ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
    ], spacing=6)
    win_controls = ft.Row([
        ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
        ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
    ], spacing=6)

    # 主页: 版本徽章 + 产品名(左) + 窗口控制(右)
    launcher_head = ft.Row([
        ft.Row([
            ui.version_tag(f"v{VERSION}"),
            # 产品名 (design-system.md #6 字号 18/700)
            ft.Text("汤圆启动器", size=18, weight=ft.FontWeight.W_700, color=COL_TEXT_SECONDARY),
        ], spacing=10),
        home_win_controls,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # -- 编辑页顶栏按钮 (design-system.md #10 BarButton, HTML .btn-bar):
    # 低调灰底细边框 34px; 保存为 primary 变体主色实心 (主操作突出, 2026-08 UI 审查落地)
    def _bar_btn(text, icon, on_click):
        return ft.OutlinedButton(
            text, icon=icon, on_click=on_click, height=34,
            style=ft.ButtonStyle(
                bgcolor={"": COL_BG_GHOST_2, "hovered": COL_BTN_BAR_HOVER},
                color=COL_TEXT_SECONDARY,
                side={"": ft.BorderSide(1, COL_BORDER_SUBTLE),
                      "hovered": ft.BorderSide(1, COL_BORDER_VISIBLE)},
                shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_500),
            ),
        )

    # 编辑页: ← 返回 + 文件按钮(左) + 保存 + 窗口控制(右)
    # 保存按钮移到顶栏左侧主按钮位 (design-system.md #10: BarButton primary 变体)
    save_btn = ft.FilledButton("保存", icon=ft.Icons.SAVE, on_click=on_save, height=34,
        style=ft.ButtonStyle(bgcolor=COL_BRAND, color=ft.Colors.WHITE,
                             shape=ft.RoundedRectangleBorder(radius=0)))  # 矩形 (2026-08 去圆角)
    editor_head = ft.Row([
        ft.Row([
            _bar_btn("返回", ft.Icons.ARROW_BACK, on_back_to_launcher),
            ft.Container(width=1, height=26, bgcolor=COL_BORDER_SUBTLE),
            _bar_btn("打开 cfg 文件夹", ft.Icons.FOLDER_OPEN, on_open_cfg),
            _bar_btn("指定目录", ft.Icons.FOLDER, on_pick_dir),
            _bar_btn("打开文件", ft.Icons.FILE_OPEN, on_open_file),
            ft.Container(width=1, height=26, bgcolor=COL_BORDER_SUBTLE),
            save_btn,
        ], spacing=10),
        win_controls,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    title_bar = ft.Container(
        content=launcher_head,
        # h=56: HTML 事实源 .titlebar 56px (2026-08 UI 审查对齐; padding 8 上下容纳 40px 窗口按钮)
        padding=ft.padding.Padding(left=16, top=8, right=16, bottom=8),
        height=56,
        on_tap_down=start_drag)

    # -- 导航栏 --
    # 不设 height/group_alignment: Flutter NavigationRail 默认 groupAlignment=-1.0
    # (顶部对齐) + 高度=内容高度, 三项紧贴顶部、间距均匀、无上方空白。
    # 教训: 手动 height=624 撑出上下大空白 + group_alignment 使项间距被拉伸不均;
    # expand=True 在 Row 里拉的是横向(rail 变整行空白, 导航项居中浮空) (2026-08 用户反馈)
    nav_rail = ft.NavigationRail(selected_index=0, label_type=ft.NavigationRailLabelType.ALL,
        # w=96: HTML 事实源 .sidebar 96px (2026-08 UI 审查对齐)
        min_width=96, min_extended_width=96,
        destinations=nav_items, on_change=on_nav_change,
        bgcolor=COL_BG, group_alignment=-1.0,   # 显式最顶: 消除剩余顶部 padding (2026-08)
        # 选中态 = 半透明品牌底 (10%) + 图标/文字变品牌柔色 (design-system #11,
        # HTML 激活项 bg 10% + 左 3px 指示条; 指示条 NavigationRail 无法表达, 用
        # 半透明 indicator 圆角 8px 近似——实心 indicator 会盖住图标 (用户反馈 2026-08),
        # 10% 半透明只提亮背景不遮图标)
        indicator_color=COL_BRAND_BG_10,
        indicator_shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
        selected_label_text_style=ft.TextStyle(color=COL_BRAND_SOFT, size=12, weight=ft.FontWeight.W_600),
        unselected_label_text_style=ft.TextStyle(color=COL_TEXT_DIM, size=12))

    # -- 编辑页视图 (导航栏 + 字段区) --
    editor_view = ft.Row([
        nav_rail,
        ft.VerticalDivider(width=1),
        content_area,
    ], expand=True)

    # -- 状态栏 (仅图标 + 编码切换; 常驻文字/时间戳已删 — design-system.md #26)
    # 组件库实现 (rules.md §1: 禁止页面内联伪组件, deep-review 5轮 MEDIUM-5)
    status_bar = ui.status_bar(enc_selector, status_msg, status_icon)

    # -- 视图容器 (AnimatedSwitcher 内容过渡, 方案 B) --
    # 2026-08 重大修复: transition=SCALE + scale=0.9 时内容以 0.9 缩放切入
    # 后停在 0.9 不恢复 1.0 (与窗口 resize 并发时状态机中断), 编辑页内容
    # 永远 0.9 缩放、四周露黑边 (用户截图证实: 内容区仅窗口的 ~85%x72%,
    # 正是 0.9 比例)。改用 FADE: 仅透明度过渡, 无尺寸副作用, 内容恒为 1.0。
    view_switcher = ft.AnimatedSwitcher(
        content=launcher_view,
        duration=280,
        transition=ft.AnimatedSwitcherTransition.FADE,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
        expand=True,
    )
    body = ft.Container(content=view_switcher, expand=True)

    page.add(ft.Container(
        content=ft.Column([
            title_bar,
            body,
            status_bar,
        ], spacing=0, tight=True),
        bgcolor=COL_BG,
        # 无描边: 描边 #2A2730 在透明窗口左/下边缘渲染成橄榄色
        # (用户截图+PrintWindow 双重证实, 2026-08); 移除后边缘干净
        # 矩形边缘 (2026-08 用户决策): 放弃圆角 — Flutter Windows 圆角窗口
        # 四角黑边问题无法可靠解决, 改矩形彻底消除
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        expand=True,
    ))

    # -- 初始加载: 直接进主页 (rev.ini 定位在主页 lazy 完成) --
    refresh_dir()
    if os.environ.get("REVINI_START_VIEW") == "cfg":
        # 调试: 启动直接进编辑页 CFG 配置 (2026-08 验证用, 平时不设)
        enter_editor()
    else:
        show_launcher()

    # 修复: 部分环境下 frameless 窗口以最小化/不可见状态启动, 主动恢复。
    # 实测: left/top 字段推送定位可靠; center()(挪到 124,134)与
    # to_front()(挪到 10,10)都会错误移动窗口, 故弃用, 位置由字段显式指定。
    page.window.minimized = False
    page.window.visible = True
    sc = _screen_center()
    if sc:
        page.window.left = sc[0] - WIN_HOME[0] / 2
        page.window.top = sc[1] - WIN_HOME[1] / 2
    page.update()

    def _settle_position():
        """窗口显示稳定后重设一次位置: 实测字段推送存在竞态
        (窗口创建时序), 偶发停留在默认 (10,10), 延迟重设保证居中。
        窗口字段仅主线程有效, 经 run_thread 走会话通道写入 (deep-review F9/R8:
        原实现裸线程直改 left/top; 延迟 1.2s→2s, 与项目实测
        '启动早期窗口字段写入被丢, 测试钩子需延迟 ~2s' 规则一致)
        同时兜底 FLET_APP_HIDDEN 模式: main() 尾部的 visible=True 在引擎
        就绪前执行会被丢, 此处延迟 2s 后补设一次, 保证窗口最终显示
        (2026-08 用户反馈启动时窗口一闪而过 → HIDDEN 模式修复)"""
        time.sleep(2.0)
        def _do():
            try:
                page.window.visible = True
                # 用户已拖动窗口(位置不再是启动默认角标): 跳过重定位,
                # 不撤销用户摆放 (deep-review 7轮 F5; 原实现无条件回主屏中心)
                l0 = page.window.left if page.window.left is not None else 0
                t0 = page.window.top if page.window.top is not None else 0
                if (l0, t0) not in ((0, 0), (10, 10)):
                    page.update()
                    return
                s2 = _screen_center()
                if s2:
                    # 用当前窗口尺寸计算中心: 启动 2s 内用户可能已进编辑页(980×720),
                    # 硬编码 WIN_HOME 会把宽窗口推偏 (deep-review 4轮 M2)
                    w = page.window.width or WIN_HOME[0]
                    h = page.window.height or WIN_HOME[1]
                    page.window.left = round(s2[0] - w / 2)
                    page.window.top = round(s2[1] - h / 2)
                page.update()
            except Exception:  # noqa: BLE001, S110 - 窗口字段兜底, 失败静默
                pass
        page.run_thread(_do)
    threading.Thread(target=_settle_position, daemon=True).start()


if __name__ == "__main__":
    ft.run(main)
