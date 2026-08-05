"""Rev.Ini 编辑器 — Flet 版 (汤圆启动器)

暗黑二次元启动器大改: 主页=居中竖卡片启动台, 配置编辑收进二级页。
设计定稿见 skill: flet-desktop-apps → references/revini-editor-launcher-redesign.md
实施计划见: plan.md
"""
import flet as ft
import sys, os, threading, subprocess, asyncio, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import VERSION
from app.ini_model import RevIni, default_ini_text
from app.fields import (FIELD_GROUPS, RANK_DISPLAY, rank_level_to_name,
                        rank_name_to_level)
from app.locator import locate_rev_ini, find_csgo_dir, find_cfg_dir
from app.settings import set_user_csgo_dir

# ==================== 汤圆启动器主题色板 ====================
COL_BG = "#111216"            # 窗口背景(纯色)
COL_CARD = "#16181B"          # 主页卡片底
COL_CARD_BORDER = "#87CEEB"   # 卡片描边(天蓝 SkyBlue, 2026-08 用户指定)
COL_BRAND = "#87CEEB"         # 品牌天蓝 (2026-08 由克莱因蓝 #002FA7 更换)
COL_BRAND_DARK = "#4FA3D4"    # 渐变深端
COL_BRAND_LIGHT = "#B3E0F5"   # 胶囊底(更浅天蓝)
ON_BRAND = "#0A2E52"          # 天蓝底上的文字/图标 (深蓝, 对比 7.9:1; 白字仅 1.7:1 不可用)
ON_BRAND_OK = "#0B4F2E"       # 天蓝底上的成功态 (深绿, 已启动 ✓)
COL_GLOW = "#DCE8FF"          # 冷白辉光 (2026-08 由淡金 #E8D5A3 换, 用户嫌土豪金; 拷问 Q1/Q3 定稿)
COL_TEXT = "#EDEAF0"          # 主文字
COL_TEXT_DIM = "#A6A0B0"      # 次要文字(原 #9A93A3 对比度偏低)
CHIP_ADDED_BG = "#87CEEB"     # 推荐参数 chip 已添加态: 天蓝底 (2026-08 由淡金换, 拷问 Q2 定稿)
INPUT_BORDER = "#4A4550"      # 输入控件边框 (提亮于 #3A3740: 空值输入区可识别性差, 视觉审计 2026-08)
INPUT_FILL = "#101114"        # 输入控件深色填充块 (与卡片底区分, 明确可编辑区域)


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
AVATAR_D = 96
BTN_W = 288   # 卡片宽 80%
BTN_H = 52

# 窗口尺寸随布局切换: 主页 360×510 竖卡(窗口即卡) / 编辑 980×720 横屏, 向心步进缓动
WIN_HOME = (360, 510)
WIN_EDIT = (980, 720)
WIN_MIN = (360, 510)


def _procname_patch(ini_path, new_value):
    """临时把 [Loader] ProcName 行替换为 原值 + ' +connect <server>'
    (Loader.exe 读取该文件构建 csgo.exe 命令行, 自动进服用)。
    纯字节级行内替换: 不经过 model/编码往返, 保证无关字节零改动。
    返回被替换行的原始字节 (供启动后恢复); 失败/无需改动返回 None。
    大小写不敏感 (通过 lowercase 副本定位, 切片仍取原字节)。"""
    nv = str(new_value or "").strip()
    if not nv:
        return None
    try:
        raw = open(ini_path, "rb").read()
    except OSError:
        return None
    low = raw.lower()
    li = low.find(b"[loader]")
    if li < 0:
        return None
    sec_end = low.find(b"[", li + 8)
    if sec_end < 0:
        sec_end = len(raw)
    pi = low.find(b"procname", li, sec_end)
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
    if b"+connect" in old_val.lower():
        return None                       # 已含 +connect (手动或上次残留), 不重复追加
    new_line = line[:eq + 1] + ws + old_val + b" +connect " + nv.encode("ascii", errors="replace")
    if line.endswith(b"\r"):   # CRLF 文件: 保留行尾 \r, 避免中间态混行尾
        new_line += b"\r"
    try:
        open(ini_path, "wb").write(raw[:ls] + new_line + raw[le:])
    except OSError:
        return None
    return line


def _procname_restore(ini_path, orig_line):
    """启动完成后把 [Loader] ProcName 行恢复为原始字节 (csgo 命令行已固化,
    文件恢复不影响已启动进程)。失败静默: 残留 +connect 无害, 下次启动去重检查
    会跳过重复追加。"""
    if not orig_line:
        return
    try:
        raw = open(ini_path, "rb").read()
    except OSError:
        return
    low = raw.lower()
    li = low.find(b"[loader]")
    if li < 0:
        return
    sec_end = low.find(b"[", li + 8)
    if sec_end < 0:
        sec_end = len(raw)
    pi = low.find(b"procname", li, sec_end)
    if pi < 0:
        return
    ls = raw.rfind(b"\n", 0, pi) + 1
    le = raw.find(b"\n", pi)
    if le < 0:
        le = len(raw)
    try:
        open(ini_path, "wb").write(raw[:ls] + orig_line + raw[le:])
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
    except Exception:
        return None


def main(page: ft.Page):
    page.title = "Rev.Ini 编辑器 · CS:GO 配置工具"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=COL_BRAND, font_family="Microsoft YaHei")
    page.padding = 0
    page.bgcolor = ft.Colors.TRANSPARENT
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
    auto_dir = find_csgo_dir() or ""
    st = {"ini_path": "", "csgo_dir": auto_dir,
          "dir_source": "自动定位" if auto_dir else "未定位",
          "loaded_name": "NO FILE LOADED", "dirty": False}
    model = None
    field_rows = []  # [(field, value_ref, control)]
    nav_index = 0

    # -- UI 引用 --
    status_msg = ft.Text("就绪", size=12, opacity=0.8)
    dir_label = ft.Text("— 未定位 —", size=12, opacity=0.8)
    path_chip = ft.Text("未加载文件", size=12, opacity=0.85)
    # 编码选择: 用 SegmentedButton 替代 Dropdown — 底部状态栏里 Dropdown 弹出菜单
    # 会被 frameless 圆角窗口边缘裁切(用户报告"被窗口强行裁接")
    enc_selector = ft.SegmentedButton(
        segments=[
            ft.Segment(value="gbk", label="ANSI"),
            ft.Segment(value="utf-8", label="UTF-8"),
        ],
        selected=["gbk"],
        style=ft.ButtonStyle(bgcolor=COL_BRAND, color=ON_BRAND),   # 选中分段天蓝深蓝字 (2026-08)
        on_change=lambda e: _on_enc_change(e),
    )
    save_btn = ft.FilledTonalButton("保存", icon=ft.Icons.SAVE,
        style=ft.ButtonStyle(bgcolor=COL_BRAND, color=ON_BRAND))   # 天蓝实心深蓝字 (2026-08)
    content_area = ft.Container(expand=True)

    # -- 工具函数 --
    def set_status(text, ok=False, err=False):
        status_msg.value = text
        status_msg.color = ft.Colors.GREEN if ok else (ft.Colors.RED if err else None)
        status_msg.opacity = 1.0 if (ok or err) else 0.7
        page.update()

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
                ft.OutlinedButton("取消", on_click=lambda e: _close()),
                ft.FilledButton("丢弃并继续", on_click=lambda e: (_close(), on_confirm())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
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
        path_chip.value = f"* {st['loaded_name']}" if st["dirty"] else st["loaded_name"]
        page.update()

    def refresh_dir():
        if st["csgo_dir"]:
            dir_label.value = st["csgo_dir"]
            dir_label.tooltip = f"CS:GO 目录: {st['csgo_dir']}\n来源: {st['dir_source']}"
        else:
            dir_label.value = "— 未定位 —"
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
                creationflags=subprocess.CREATE_NO_WINDOW)   # GUI 子系统下不闪控制台 (2026-08)
            out = r.stdout.strip()
            return out if out else ""
        except subprocess.TimeoutExpired:
            # 对话框被超时终止: 明确提示, 不再静默吞掉用户选择
            set_status("DIALOG TIMEOUT // 对话框超时(5 分钟),请重试", err=True)
            return ""
        except Exception:
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
                set_user_csgo_dir(p)
                refresh_dir()
                ini = os.path.join(p, "rev.ini")
                if os.path.isfile(ini):
                    load_file(ini)
                set_status(f"DIR SET // {p}", ok=True)

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
                        ft.OutlinedButton("取消", on_click=lambda e: _close()),
                        ft.FilledButton("仍然使用", on_click=lambda e: (_close(), guard_dirty(_apply))),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
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
                if isinstance(ctrl, ft.Dropdown) and vr["v"] in [o.key for o in ctrl.options]:
                    ctrl.value = vr["v"]
            elif ftype == "textarea":
                vr["v"] = str(raw)
                if isinstance(ctrl, ft.Column):
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
                set_status(f"LOAD ERROR // {e}", err=True)
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
        path_chip.value = st["loaded_name"]
        path_chip.tooltip = path
        if enc_selector:
            if model.source_encoding in ("gbk", "utf-8"):
                enc_selector.selected = [model.source_encoding]
                st["enc"] = model.source_encoding
        populate_all()
        refresh_dir()
        update_title()
        if enc_warning:
            set_status(f"LOADED // {st['loaded_name']} · ⚠ 编码损坏,已用替换字符加载,保存前请确认备份", err=True)
        else:
            set_status(f"LOADED // {st['loaded_name']}", ok=True)
        return True

    def on_save(e=None):
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
            set_status(f"SAVE ERROR // {e}", err=True)
            return
        st["dirty"] = False
        update_title()
        stamp = datetime.now().strftime("%H:%M:%S")
        enc_label = "ANSI" if enc == "gbk" else "UTF-8"
        set_status(f"SAVED // {st['loaded_name']} [{enc_label}] @ {stamp}" +
                   ("  ·  BACKUP" if bak else ""), ok=True)
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

    def _on_enc_change(e):
        """编码分段按钮切换: 事件数据是选中值列表(单选模式取第一个)。
        0.86.5 Dart 侧发 List; 兼容其它形态(裸字符串/JSON 字符串), 防御性解析 (L1)"""
        data = e.data
        if isinstance(data, str):
            import json as _json
            try:
                parsed = _json.loads(data)
                data = parsed if isinstance(parsed, (list, tuple)) else [parsed]
            except ValueError:
                data = [data]
        sel = data if isinstance(data, (list, tuple)) else [str(data or "")]
        if sel:
            # 白名单校验: 只认 gbk/utf-8, 未知值保持原编码,
            # 避免污染 st['enc'] 导致保存时抛 ValueError (L1)
            v = str(sel[0])
            if v in ("gbk", "utf-8"):
                st["enc"] = v

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
            set_status("CFG DIR // 未定位", err=True)
            return
        try:
            os.startfile(cfg)
        except OSError as e:
            # 目录被删/权限受限时给出反馈, 而不是按钮静默无反应 (deep-review F8)
            set_status(f"CFG DIR // 打开失败: {e}", err=True)
            return
        set_status(f"CFG DIR // {cfg}", ok=True)

    save_btn.on_click = on_save

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
                active_color=ON_BRAND, active_track_color=COL_BRAND,   # 开启: 天蓝轨道+深蓝滑块 (2026-08)
                inactive_thumb_color="#8A8494", inactive_track_color="#2A2730",
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))
        elif ftype == "rank":
            # 伪装段位: 选项为 RANK_DISPLAY 段位名, 存储值 = 1-18 数字(保存时转换)
            opts = [ft.dropdown.Option(key=name, text=name) for name in RANK_DISPLAY]
            dflt_name = rank_level_to_name(default) if isinstance(default, int) else str(default)
            # 合法选择必须清除 bad, 否则非法原值字段永久无法通过 UI 修改 (deep-review R2)
            ctrl = ft.Dropdown(options=opts, width=236, value=dflt_name,
                filled=True,   # 0.86.5: Dropdown 必须 filled=True 才绘制 fill_color (视觉审计 2026-08)
                border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
                on_select=lambda e: (vr.__setitem__("v", e.control.value),
                                     vr.__setitem__("bad", False), mark_dirty()))
        elif ftype in ("combo",):
            items = field.get("items", [])
            dm = field.get("display_map") or {}   # M4: 未提供 display_map 时不能 .get() None
            opts = [ft.dropdown.Option(key=i, text=dm.get(i, i)) for i in items]
            ctrl = ft.Dropdown(options=opts, width=236,
                filled=True,   # 0.86.5: 同上, 否则透明底融进卡片
                value=str(default) if default else (items[0] if items else ""),
                border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
                on_select=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))
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
                if lo or hi:
                    if not (lo <= iv <= hi):
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
            ctrl = ft.TextField(width=236, text_align=ft.TextAlign.RIGHT,
                value=str(default) if default else "0",
                border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
                on_change=_on_int_change)
        elif ftype == "textarea":
            ta = ft.TextField(multiline=True, min_lines=3, max_lines=6,
                value=str(default) if default else "",
                hint_text=field.get("placeholder") or None,   # 占位符接线 (视觉审计 2026-08: 原未传入)
                border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty(), _sync_chips()))
            # 推荐参数 chips: 点击 toggle 添加/移除; 已添加的 chip 变淡金底+对勾
            # (避免重复添加, 视觉审计 2026-08)
            chip_refs = []
            def _sync_chips():
                cur = ta.value or ""
                for cdef, chip in chip_refs:
                    added = cdef.get("args", "").strip() in cur
                    chip.bgcolor = CHIP_ADDED_BG if added else None
                    chip.label = ft.Text(("✓ " if added else "") + cdef["label"],
                                         size=12, color=ON_BRAND if added else None)
                    chip.icon = ft.Icons.CHECK if added else None
                page.update()
            vr["sync"] = _sync_chips   # populate_all 加载后同步一次 chip 状态
            def make_cc(c):
                def on_chip(_=None):
                    args = c.get("args", "").strip()
                    cur = ta.value.strip()
                    if args in cur:
                        # 移除
                        ta.value = cur.replace(args, "").replace("  ", " ").strip()
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
                chip = ft.Chip(label=ft.Text(c["label"], size=12), on_click=make_cc(c))
                chip_refs.append((c, chip))
                chips.append(chip)
            ctrl = ft.Column([ta, ft.Row(chips, wrap=True, spacing=4)], spacing=8)
        else:
            # max_length 应用字段定义的限制 (deep-review F10: 原实现忽略 maxlen,
            # 超长昵称可保存并在主页撑爆固定 360×510 布局)
            ctrl = ft.TextField(width=236,
                value=str(default) if default else "",
                max_length=field.get("maxlen") or None,
                hint_text=field.get("placeholder") or None,   # 占位符接线 (视觉审计 2026-08)
                border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))

        if ftype == "textarea":
            # 多行字段卡片: 纵向布局 — 标题/说明在上, 输入框通栏, chips 在下
            # (视觉审计 2026-08: 原左右分栏把多行输入框压窄, 长参数频繁换行)
            # 宽度=卡片内宽 (编辑窗口固定 980, 导航88+分隔1+ListView padding 40+卡片 padding 36)
            # 勿用 fit_parent_size: ListView 无界高度下 TextField 通栏渲染空白 (实测 2026-08)
            ta.width = 815
            row = ft.Container(
                content=ft.Column([
                    ft.Text(code_text, size=13, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.75),
                    ft.Text(label, size=17, weight=ft.FontWeight.W_500),
                    ft.Text(desc, size=14, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.85) if desc else ft.Text(""),
                    ft.Container(height=6),
                    ctrl,
                ], tight=True, spacing=2),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=12,
                padding=ft.padding.Padding(left=18, top=16, right=18, bottom=16),
                margin=ft.margin.Margin(top=4, bottom=4, left=0, right=0))
        else:
            row = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(code_text, size=13, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.75),
                        ft.Text(label, size=17, weight=ft.FontWeight.W_500),
                        ft.Text(desc, size=14, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.85) if desc else ft.Text(""),
                    ], tight=True, spacing=2, expand=True),
                    ft.Container(content=ctrl, alignment=ft.alignment.Alignment(1, 0)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=12,
                padding=ft.padding.Padding(left=18, top=16, right=18, bottom=16),
                margin=ft.margin.Margin(top=4, bottom=4, left=0, right=0))
        # hover 微交互: 卡片提亮一档, 提升长列表可扫描性 (视觉增强 R4)
        row.on_hover = lambda e, r=row: (
            setattr(r, "bgcolor",
                    ft.Colors.SURFACE_CONTAINER_HIGH if e.data == "true"
                    else ft.Colors.SURFACE_CONTAINER_HIGHEST), r.update())
        field_rows.append((field, vr, ctrl))
        return row

    def build_page(group):
        items = []
        code_sec = group["fields"][0]["section"] if group.get("fields") else "GENERAL"
        items.append(ft.Container(
            content=ft.Column([
                ft.Text(f"// CFG.{code_sec.upper()}", size=11, color=ft.Colors.AMBER_ACCENT, opacity=0.8),
                ft.Text(group["title"], size=22, weight=ft.FontWeight.W_600),
                ft.Text(group.get("desc", ""), size=13, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.7),
            ], spacing=4),
            padding=ft.padding.Padding(left=18, top=10, right=18, bottom=14)))
        for f in group.get("fields", []):
            items.append(build_field_row(f))
        return ft.ListView(controls=items, padding=ft.padding.Padding(left=20, top=20, right=20, bottom=40), expand=True)

    def build_tools_page(group):
        from app.tools import REPAIR_TOOLS, run_tool
        items = [ft.Container(
            content=ft.Column([
                ft.Text("// CFG.TOOLS", size=11, color=ft.Colors.AMBER_ACCENT, opacity=0.8),
                ft.Text(group["title"], size=22, weight=ft.FontWeight.W_600),
                ft.Text(group.get("desc", ""), size=13, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.7),
            ], spacing=4),
            padding=ft.padding.Padding(left=18, top=10, right=18, bottom=14))]

        # 执行超时设置 (2026-08): 脚本运行超过该秒数会被强制终止进程树
        # 默认 120s; 存字符串便于直接显示, 读取时解析+钳位
        timeout_field = ft.TextField(
            value="120", width=110, text_align=ft.TextAlign.CENTER,   # 数字居中 (用户指定 2026-08)
            label="执行超时(秒)", label_style=ft.TextStyle(size=11),
            border_color=INPUT_BORDER, focused_border_color=COL_BRAND, fill_color=INPUT_FILL,
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
                if not d or not os.path.isfile(os.path.join(d, tool.file)):
                    set_status(f"TOOL // 未定位 {tool.file}", err=True)
                    return
                timeout = _parse_timeout()
                def _run():
                    run_btn.disabled = True
                    run_btn.content = "运行中…"   # 0.86.5 Button 无 text 属性, 用 content (2026-08)
                    status_txt.value = "运行中…"
                    status_txt.color = ft.Colors.AMBER
                    page.update()

                    def on_done(ok, output):
                        # run_tool 的回调在工作线程触发, UI 变更统一回主线程 (H1)
                        page.run_thread(
                            lambda: _apply_tool_result(ok, output))

                    def _apply_tool_result(ok, output):
                        run_btn.disabled = False
                        run_btn.content = "运行"
                        if ok:
                            status_txt.value = "完成"
                            status_txt.color = ft.Colors.GREEN
                            set_status(f"TOOL DONE // {tool.name}", ok=True)
                        else:
                            status_txt.value = "失败"
                            status_txt.color = ft.Colors.RED
                            set_status(f"TOOL FAIL // {tool.name}: {output[:120]}", err=True)
                        page.update()

                    if not run_tool(d, tool, on_done=on_done, timeout=timeout):
                        # 脚本缺失/无法启动 (启动瞬间文件被删/占用): on_done 不会被回调,
                        # 必须在这里恢复按钮状态, 否则永久卡"运行中…" (2026-08 用户反馈)
                        page.run_thread(lambda: (
                            setattr(run_btn, "disabled", False),
                            setattr(run_btn, "content", "运行"),
                            setattr(status_txt, "value", "无法启动"),
                            setattr(status_txt, "color", ft.Colors.RED),
                            set_status(f"TOOL START FAIL // {tool.file}", err=True),
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
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=12,
            padding=ft.padding.Padding(left=16, top=12, right=16, bottom=12),
            margin=ft.margin.Margin(left=0, top=4, right=0, bottom=4)))

        for tool in REPAIR_TOOLS:
            run_btn = ft.Button("运行", icon=ft.Icons.PLAY_ARROW,
                style=ft.ButtonStyle(bgcolor=COL_BRAND, color=ON_BRAND))   # 品牌色实心 (视觉审计 2026-08)
            status_txt = ft.Text("待运行", size=11, opacity=0.85)
            run_btn.on_click = make_runner(tool, run_btn, status_txt)
            # 风险分级色: 低=绿/中=琥珀/高=红 (原统一 ERROR 红无法区分等级, 视觉审计 2026-08)
            RISK_COLORS = {"低": ft.Colors.GREEN, "中": ft.Colors.AMBER, "高": ft.Colors.RED}
            risk_color = RISK_COLORS.get(tool.risk, ft.Colors.ERROR)
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Row([
                            # 类别标签: 天蓝底深蓝字 (白字仅 1.7:1 不可读, 2026-08)
                            ft.Container(content=ft.Text(tool.category, size=11, color=ON_BRAND),
                                bgcolor=COL_BRAND,
                                padding=ft.padding.Padding(left=8, top=2, right=8, bottom=2), border_radius=4),
                            ft.Text(f"风险:{tool.risk}", size=12, color=risk_color, weight=ft.FontWeight.W_500),
                        ], spacing=8),
                        ft.Text(tool.name, size=16, weight=ft.FontWeight.W_600),
                        ft.Text(tool.desc, size=13, opacity=0.85),
                        ft.Text(f"执行: {tool.action}", size=12, opacity=0.7),
                    ], expand=True, spacing=4),
                    ft.Column([
                        run_btn,
                        status_txt,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ]), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=12,
                padding=ft.padding.Padding(left=16, top=16, right=16, bottom=16),
                margin=ft.margin.Margin(left=0, top=4, right=0, bottom=4)))
        items.append(ft.Container(
            content=ft.Text("工具直接调用 CS:GO 目录下的官方维护脚本,运行结果以脚本输出为准。\n"
                "修复 Steam 错误会修改当前用户的注册表(HKCU),请按需使用。", size=12, opacity=0.85),
            padding=ft.padding.Padding(left=0, top=8, right=0, bottom=0)))
        return ft.ListView(controls=items, padding=ft.padding.Padding(left=20, top=20, right=20, bottom=40), expand=True)

    # -- 导航 --
    nav_content = []
    icon_map = {"tune": ft.Icons.TUNE, "play": ft.Icons.PLAY_ARROW, "wrench": ft.Icons.BUILD}
    nav_items = []
    for i, g in enumerate(FIELD_GROUPS):
        icon = icon_map.get(g.get("icon_key", "wrench"), ft.Icons.BUILD)
        nav_items.append(ft.NavigationRailDestination(
            icon=ft.Icon(icon, color=COL_TEXT_DIM),
            selected_icon=ft.Icon(icon, color=ON_BRAND),
            label=ft.Text(g["title"], size=12)))
        nav_content.append(build_tools_page(g) if g.get("type") == "tools" else build_page(g))
    content_area.content = nav_content[0]

    def on_nav_change(e):
        nonlocal nav_index
        nav_index = e.control.selected_index
        content_area.content = nav_content[nav_index]
        page.update()

    def start_drag(_=None):
        asyncio.create_task(page.window.start_dragging())

    def on_close_window(_=None):
        """关闭窗口: 有未保存修改时先确认 (与返回按钮行为一致, 2026-08 deep-review F1),
        确认后清掉可能残留的对话框, 再真正关闭
        (deep-review R8: 先弹掉已有 modal=False 对话框, 防止确认框栈式叠加)"""
        # 先清掉可能开着的其它对话框 (F6 目录确认等), 避免确认框叠加上层挡死下层
        try:
            page.pop_dialog()
        except Exception:
            pass
        page.update()

        def _do_close():
            try:
                page.pop_dialog()
            except Exception:
                pass
            page.update()
            asyncio.create_task(page.window.destroy())

        if st["dirty"]:
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
                                      border_radius=AVATAR_D // 2)
        else:
            avatar.content = ft.Text((nick or "汤")[:1], size=40,
                                     color=COL_GLOW, weight=ft.FontWeight.W_700)

    # 头像(底色与主界面一致 + 金色圆环 + 淡金光晕)
    avatar = ft.Container(
        width=AVATAR_D, height=AVATAR_D,
        border_radius=AVATAR_D // 2,
        bgcolor=COL_CARD,
        border=ft.Border(top=ft.BorderSide(2, COL_GLOW),
                         right=ft.BorderSide(2, COL_GLOW),
                         bottom=ft.BorderSide(2, COL_GLOW),
                         left=ft.BorderSide(2, COL_GLOW)),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text("汤", size=40, color=COL_GLOW, weight=ft.FontWeight.W_700),
    )
    # 主页昵称: 单行 + 省略号, 防超长昵称撑爆固定 360×510 布局 (deep-review F10)
    nick_label = ft.Text("未定位", size=24, weight=ft.FontWeight.W_700, color=COL_TEXT,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    unlocated_hint = ft.Text("⚠ rev.ini 未定位, 点配置指定目录", size=12, color=COL_TEXT_DIM)
    home_err = ft.Text("", size=12, color=ft.Colors.ERROR)
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
                        launch_btn_text.value = "已启动 ✓"
                        launch_btn_text.color = ON_BRAND_OK
                        launch_icon.color = ON_BRAND_OK
                        launch_btn.gradient = GRAD_LAUNCH
                    else:
                        launch_btn_text.value = "启动游戏"
                        launch_btn_text.color = ON_BRAND
                        launch_icon.color = ON_BRAND
                        launch_btn.gradient = GRAD_LAUNCH
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
            launch_btn_text.value = "启动游戏"
            launch_btn_text.color = ON_BRAND
            launch_icon.color = ON_BRAND
            launch_btn.gradient = GRAD_LAUNCH
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
                               creationflags=subprocess.CREATE_NO_WINDOW)
            return name.lower() in r.stdout.decode("gbk", errors="replace").lower()
        except Exception:
            return False

    def csgo_running():
        try:
            # PYTHONUTF8=1 时 fsencoding=utf-8, tasklist 输出 GBK → text=True 解码崩溃
            # (stdout=None + 永久返回 False + 刷 _readerthread 错误噪音, 2026-08 实测)。
            # 用 bytes + 显式 gbk+replace: 环境无关, csgo.exe 为 ASCII 不受影响。
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq csgo.exe"],
                               capture_output=True, timeout=5,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            return "csgo.exe" in r.stdout.decode("gbk", errors="replace").lower()
        except Exception:
            return False

    launch_icon = ft.Icon(ft.Icons.ROCKET_LAUNCH, size=18, color=ON_BRAND)
    launch_btn_text = ft.Text("启动游戏", size=16, weight=ft.FontWeight.W_600, color=ON_BRAND)

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
            launch_btn_text.value = "已启动 ✓"
            launch_btn_text.color = ON_BRAND_OK
            launch_icon.color = ON_BRAND_OK
            launch_btn.gradient = GRAD_LAUNCH
            page.update()
            return
        d = st["csgo_dir"] or find_csgo_dir() or ""
        if not d or not os.path.isfile(os.path.join(d, "Loader.exe")):
            show_home_error("未定位 Loader.exe, 请先在配置页指定目录")
            return
        # Loader 已在运行 (启动窗口期/挂起残留): 拒绝二次 Popen, 显示等待提示而非假\"已启动 ✓\" (R4)
        if _proc_exists("Loader.exe"):
            show_home_error("Loader.exe 已在运行, 请稍候游戏启动")
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
        proc_orig = None
        try:
            _m = RevIni.load(ini)
            auto_join = str(_m.get("Loader", "ConnectServer", "") or "").strip()
            _proc = str(_m.get("Loader", "ProcName", "") or "").strip()
            if auto_join and "+connect" not in _proc:
                proc_orig = _procname_patch(ini, auto_join)   # 助手内部拼 " +connect <server>"
        except OSError:
            pass
        try:
            subprocess.Popen([os.path.join(d, "Loader.exe")], cwd=d)
        except OSError as e:
            if getattr(e, "winerror", None) == 740:
                # Loader.exe 需要管理员权限 (requireAdministrator manifest):
                # ShellExecuteW runas verb 提权启动, 弹出 UAC 确认 (R1)
                try:
                    import ctypes
                    res = ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", os.path.join(d, "Loader.exe"), "", d, 1)
                except Exception:
                    res = 0
                if res <= 32:
                    _procname_restore(ini, proc_orig)
                    show_home_error("Loader.exe 需要管理员权限, 请在 UAC 弹窗中确认")
                    return
                # 提权拉起成功, fall through 到统一轮询
            else:
                _procname_restore(ini, proc_orig)
                show_home_error(f"启动失败: {e}")
                return

        st["launching"] = True      # 防连点
        launch_btn.gradient = GRAD_LAUNCHING   # 渐变变暗 = 忙碌态
        launch_btn_text.value = "启动中…"
        launch_btn_text.color = COL_TEXT
        page.update()

        def poll():
            ok = False
            for _ in range(20):          # 10s 超时, 每 0.5s 检查 (慢机器 >5s 启动常见, 2026-08 deep-review F2)
                if csgo_running():
                    ok = True
                    break
                time.sleep(0.5)
            _procname_restore(ini, proc_orig)   # 自动进服: 恢复 ProcName (无论成败, csgo 命令行已固化)
            # 轮询线程只做检测, UI 变更统一回主线程 (H1)
            page.run_thread(lambda: _apply_poll_result(ok))

        def _apply_poll_result(ok):
            launch_btn.gradient = GRAD_LAUNCH
            if ok:
                launch_btn_text.value = "已启动 ✓"
                launch_btn_text.color = ON_BRAND_OK
                launch_icon.color = ON_BRAND_OK
            else:
                launch_btn_text.value = "启动游戏"
                launch_btn_text.color = ON_BRAND
                launch_icon.color = ON_BRAND
                # 超时反馈必须走主页可见通道 (status_bar 在主页隐藏, R3)
                show_home_error("启动超时: 未检测到 csgo.exe, 游戏可能仍在启动, 请稍候")
            st["launching"] = False
            page.update()
        threading.Thread(target=poll, daemon=True).start()

    # 辉光已删除 (2026-08 用户决定): 启动按钮/头像不再有呼吸光晕
    hover_state = {"on": False}   # 启动按钮 hover 状态 (渐变提亮)

    # 启动按钮渐变 (2026-08): 正常/启动中(变暗忙碌态) 两档
    GRAD_LAUNCH = ft.LinearGradient(begin=ft.alignment.Alignment(0, -1),
                                    end=ft.alignment.Alignment(0, 1),
                                    colors=[COL_BRAND, COL_BRAND_DARK])
    GRAD_LAUNCHING = ft.LinearGradient(begin=ft.alignment.Alignment(0, -1),
                                       end=ft.alignment.Alignment(0, 1),
                                       colors=[COL_BRAND_DARK, "#2A6B96"])   # 忙碌态变暗 (白字可读)

    launch_btn = ft.Container(
        width=BTN_W, height=BTN_H,
        gradient=GRAD_LAUNCH,
        border_radius=BTN_H // 2,
        alignment=ft.alignment.Alignment(0, 0),
        animate=ft.Animation(1300, ft.AnimationCurve.EASE_IN_OUT),
        on_click=on_launch_click,
        on_hover=lambda e: on_launch_hover(e),   # 晚绑定: 函数在其后定义
        content=ft.Row([launch_icon, launch_btn_text], spacing=8,
                       alignment=ft.MainAxisAlignment.CENTER),
    )

    def on_launch_hover(e):
        """hover 微交互: 渐变整体提亮一档 (光晕已删除 2026-08)"""
        hover_state["on"] = e.data == "true"
        if st.get("launching"):
            # 启动中忙碌态: 保持变暗, 不响应 hover 提亮
            launch_btn.gradient = GRAD_LAUNCHING
            launch_btn.update()
            return
        if hover_state["on"]:
            launch_btn.gradient = ft.LinearGradient(
                begin=ft.alignment.Alignment(0, -1), end=ft.alignment.Alignment(0, 1),
                colors=["#B5E2F7", "#7CC4EC"])   # hover 整体提亮一档 (idle: #87CEEB→#4FA3D4)
        else:
            launch_btn.gradient = GRAD_LAUNCH
        launch_btn.update()
    config_btn = ft.OutlinedButton("配置", icon=ft.Icons.TUNE, width=BTN_W, height=44,
                                   style=ft.ButtonStyle(side=ft.BorderSide(1, COL_BRAND)),
                                   on_click=lambda e: enter_editor(e))

    def gap(h):
        return ft.Container(height=h)

    card = ft.Container(
        width=CARD_W,
        bgcolor=COL_CARD,
        border_radius=24,
        # 阴影改纯黑: 原天蓝 #87CEEB33 向上扩散到标题栏下方渲染成橄榄色线
        # (用户报告\"标题栏下方一条线\", 2026-08); 黑色阴影融入深底无色相
        shadow=ft.BoxShadow(blur_radius=30, spread_radius=0, color="#00000059",
                            offset=ft.Offset(0, 8)),
        padding=ft.padding.Padding(top=28, left=36, right=36, bottom=30),
        content=ft.Column([
            avatar,
            gap(24),
            nick_label,
            gap(8),
            hint_box,
            gap(20),
            launch_btn,
            gap(14),
            config_btn,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
    )

    launcher_view = ft.Container(
        expand=True,
        alignment=ft.alignment.Alignment(0, 0),
        content=card,
    )

    # -- 布局切换 (主页 ↔ 编辑页) --
    def show_launcher():
        refresh_launcher()
        title_bar.content = launcher_head
        view_switcher.content = launcher_view
        status_bar.visible = False   # 主页 360×510 窗口即卡, 状态栏放不下且无功能价值
        page.window.focused = True   # 主动聚焦: frameless 窗口未聚焦时首次点击被窗口管理器吞掉 (2026-08)
        page.update()

    def show_editor():
        nonlocal model
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
                    set_status("返回 // 文件已被删除, 内存配置保留, 保存将重建文件", err=True)
            else:
                # 无文件(默认模板场景): 重置为干净的默认模板
                model = RevIni.from_text(default_ini_text())
                populate_all()
                st["dirty"] = False
            show_launcher()               # 先切回主页卡(宽屏中居中显示)
            _animate_window(*WIN_HOME)    # 再收拢窗口包住卡片
        if st["dirty"]:
            confirm_discard(_go, title="返回启动台",
                            message="配置尚未保存, 返回将丢弃这些修改。")
        else:
            _go()

    # -- 窗口切换 (方案 B 2026-08: 一次到位 + AnimatedSwitcher 内容过渡) --
    # 逐帧窗口 resize 每帧一次 Python→Flutter 往返, 无论怎么优化都有限;
    # 改为: 窗口一次 update 到位 + body 内容用 AnimatedSwitcher(SCALE) 原生过渡。
    resize_state = {"busy": False}

    def _animate_window(tw, th, on_done=None):
        """窗口一次到位到目标尺寸(屏幕居中); on_done 同步执行(主线程)。
        内部 run_thread: 工作线程(Timer/轮询)调用也可靠, 窗口字段仅主线程有效 (2026-08)。"""
        if resize_state["busy"]:
            return
        resize_state["busy"] = True
        page.run_thread(lambda: _do_resize(tw, th, on_done))

    def _do_resize(tw, th, on_done):
        try:
            sc = _screen_center()
            if sc:
                cx, cy = sc
            else:
                w0 = page.window.width or WIN_HOME[0]
                h0 = page.window.height or WIN_HOME[1]
                l0 = page.window.left if page.window.left is not None else 0
                t0 = page.window.top if page.window.top is not None else 0
                cx, cy = l0 + w0 / 2, t0 + h0 / 2
            page.window.min_width, page.window.min_height = WIN_MIN
            page.window.width = tw
            page.window.height = th
            page.window.left = round(cx - tw / 2)
            page.window.top = round(cy - th / 2)
            page.update()
        finally:
            resize_state["busy"] = False
            if on_done:
                on_done()

    def enter_editor(_=None):
        """配置按钮: 预构建编辑页内容(与窗口展开动画并行), 动画完成只做轻量切换。
        原实现: on_done=show_editor 在动画完成瞬间首次构建几百字段控件+全量推送,
        造成切换时明显卡顿 (2026-08 用户反馈)。
        M2/H1: _prep 线程只做磁盘 IO+解析(纯数据), UI 应用统一经 run_thread 回主线程,
        load_state 互斥防双加载。"""
        # 主线程先置互斥再起线程: 保证 _prep 未跑到置位语句时 show_editor
        # 也能看到 loading=True, 杜绝"双加载"竞态窗口 (M2)
        load_state["loading"] = True
        def _prep():
            """工作线程: 只做 locate + RevIni.load(纯数据), 不碰任何 UI 控件 (H1/M2)"""
            nonlocal model
            if model is not None:
                return   # 已加载过: 防重复加载 (loading 标志是给 show_editor 看的)
            auto = locate_rev_ini()
            if auto:
                import warnings
                try:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        m = RevIni.load(auto)
                except OSError as e:
                    # 先取出消息再进 lambda: 避免闭包延迟绑定 except 变量 (F841)
                    err_msg = f"LOAD ERROR // {e}"
                    page.run_thread(lambda: (
                        set_status(err_msg, err=True),
                        load_state.__setitem__("loading", False)))   # M2: 失败也要解除互斥
                    return
                enc_w = any(issubclass(w.category, RuntimeWarning) for w in caught)
                page.run_thread(
                    lambda: load_file(auto, preloaded=m, preloaded_warning=enc_w))
            else:
                page.run_thread(_use_default_template)
        threading.Thread(target=_prep, daemon=True).start()
        _animate_window(*WIN_EDIT, on_done=show_editor)

    # -- 标题栏 --
    win_controls = ft.Row([
        ft.IconButton(icon=ft.Icons.MINIMIZE, on_click=on_minimize, tooltip="最小化",
                      icon_color=COL_TEXT_DIM),
        ft.IconButton(icon=ft.Icons.CLOSE, on_click=on_close_window, tooltip="关闭",
                      icon_color=COL_TEXT_DIM),
    ], spacing=6)

    # 主页: 版本胶囊 + 副标题(左) + 窗口控制(右)
    launcher_head = ft.Row([
        ft.Row([
            ft.Container(
                content=ft.Text(f"v{VERSION}", size=10, weight=ft.FontWeight.W_500, color=ON_BRAND),
                bgcolor=COL_BRAND_LIGHT,
                border_radius=10,
                padding=ft.padding.Padding(left=10, top=4, right=10, bottom=4),
            ),
            # 原卡片副标题移至版本号旁 (2026-08 用户指定); 字号 16 (用户指定 2026-08)
            ft.Text("汤圆启动器", size=16, color="#C3BDD0"),
        ], spacing=8),
        win_controls,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # 编辑页: ← 返回 + 文件按钮(左) + 目录/文件信息 + 窗口控制(右)
    editor_head = ft.Row([
        ft.Row([
            ft.OutlinedButton("返回", icon=ft.Icons.ARROW_BACK, on_click=on_back_to_launcher,
                              style=ft.ButtonStyle(side=ft.BorderSide(1, COL_BRAND))),
            ft.Container(width=1, height=26, bgcolor=ft.Colors.OUTLINE_VARIANT),
            ft.OutlinedButton("打开 cfg 文件夹", icon=ft.Icons.FOLDER_OPEN, on_click=on_open_cfg,
                              style=ft.ButtonStyle(side=ft.BorderSide(1, COL_BRAND))),
            ft.OutlinedButton("指定目录", icon=ft.Icons.FOLDER, on_click=on_pick_dir,
                              style=ft.ButtonStyle(side=ft.BorderSide(1, COL_BRAND))),
            ft.OutlinedButton("打开文件", icon=ft.Icons.FILE_OPEN, on_click=on_open_file,
                              style=ft.ButtonStyle(side=ft.BorderSide(1, COL_BRAND))),
        ], spacing=10),
        ft.Row([
            ft.Column([ft.Text("CS:GO 目录", size=11, opacity=0.8), dir_label], tight=True, spacing=1),
            path_chip,
            win_controls,
        ], spacing=10),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    title_bar = ft.Container(
        content=launcher_head,
        padding=ft.padding.Padding(left=16, top=9, right=16, bottom=9),
        height=64,
        on_tap_down=start_drag)

    # -- 导航栏 --
    # 不设 height/group_alignment: Flutter NavigationRail 默认 groupAlignment=-1.0
    # (顶部对齐) + 高度=内容高度, 三项紧贴顶部、间距均匀、无上方空白。
    # 教训: 手动 height=624 撑出上下大空白 + group_alignment 使项间距被拉伸不均;
    # expand=True 在 Row 里拉的是横向(rail 变整行空白, 导航项居中浮空) (2026-08 用户反馈)
    nav_rail = ft.NavigationRail(selected_index=0, label_type=ft.NavigationRailLabelType.ALL,
        min_width=88, min_extended_width=88,
        destinations=nav_items, on_change=on_nav_change,
        bgcolor=COL_BG, group_alignment=-1.0,   # 显式最顶: 消除剩余顶部 padding (2026-08)
        indicator_color="#4FA3D4",   # 选中胶囊(天蓝中档, 深底上醒目)
        selected_label_text_style=ft.TextStyle(color=COL_TEXT, size=12, weight=ft.FontWeight.W_600),
        unselected_label_text_style=ft.TextStyle(color=COL_TEXT_DIM, size=12))

    # -- 编辑页视图 (导航栏 + 字段区) --
    editor_view = ft.Row([
        nav_rail,
        ft.VerticalDivider(width=1),
        content_area,
    ], expand=True)

    # -- 状态栏 (无时钟) --
    status_bar = ft.Container(
        content=ft.Row([
            status_msg,
            ft.Row([ft.Text("编码", size=12, opacity=0.75), enc_selector, save_btn], spacing=8),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        padding=ft.padding.Padding(left=16, top=8, right=16, bottom=8))

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
        border_radius=ft.border_radius.BorderRadius(top_left=12, top_right=12, bottom_left=12, bottom_right=12),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        expand=True,
    ))

    # -- 初始加载: 直接进主页 (rev.ini 定位在主页 lazy 完成) --
    refresh_dir()
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
                s2 = _screen_center()
                if s2:
                    page.window.left = s2[0] - WIN_HOME[0] / 2
                    page.window.top = s2[1] - WIN_HOME[1] / 2
                page.update()
            except Exception:
                pass
        page.run_thread(_do)
    threading.Thread(target=_settle_position, daemon=True).start()


if __name__ == "__main__":
    ft.run(main)
