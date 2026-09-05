"""Rev.Ini 编辑器 — Flet 版 (汤圆启动器)

暗黑二次元启动器大改: 主页=居中竖卡片启动台, 配置编辑收进二级页。
设计定稿见 skill: flet-desktop-apps → references/revini-editor-launcher-redesign.md
实施计划见: plan.md
"""
import asyncio
import base64
import io
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
from PIL import Image as PILImage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import APP_VERSION
from app import avatar as avatar_mod
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
from app.settings import (
    SETTINGS_DIR,
    load_settings,
    save_settings,
    set_user_csgo_dir,
)
from app.tools import _install_loader
from flet_app import theme
from flet_app.components import ui

# 颜色/阴影一律 theme.COL_X 属性动态访问 (v2.3.0 深浅换装: from-import 会冻结
# 启动时的深色值, set_scheme 换装后不可见)。此处仅保留与主题无关的静态令牌。
from flet_app.theme import (
    FONT_36,
    FONT_CN,
    H_INPUT,
    S_PREVIEW_AVATAR,
    W_AVATAR_SIDE,
)


def find_avatar_path(csgo_dir):
    """CSGO 目录头像: platform/avatar.dat 优先, avatar1.dat 备选; 均失败返回 None"""
    if not csgo_dir:
        return None
    for name in ("avatar.dat", "avatar1.dat"):
        p = os.path.join(csgo_dir, "platform", name)
        if os.path.isfile(p):
            return p
    return None


def find_preview_path() -> str:
    """启动器展示用清晰头像 (用户数据目录, 256×256 PNG); 缺失返回 None。

    两套逻辑 (2026-08-23): 游戏头像 64×64 固定, 主页展示读清晰版不糊。
    """
    p = os.path.join(SETTINGS_DIR, "avatar_preview.png")
    return p if os.path.isfile(p) else None


# 主页卡片尺寸
CARD_W = 360

# 窗口尺寸随布局切换: 主页 360×510 竖卡(窗口即卡) / 编辑 784×600 横屏, 向心步进缓动
WIN_HOME = (360, 510)
WIN_EDIT = (784, 600)
WIN_MIN = (360, 510)

# ServerPanel 悬停面板锚点 (主页内容区坐标; design-system.md #34 锚定胶囊下方,
# HTML 事实源 .server-panel top:292px 窗口坐标 - 标题栏 56)
SERVER_PANEL_TOP = 236


def _dwm_round_corners(title: str = "Tangyuan", timeout: float = 6.0) -> bool:
    """Win11 原生 DWM 圆角 (tokens.md §3 radius-window): frameless 窗口调
    DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE=33, DWMWCP_ROUND=2)。
    系统级渲染无黑边 (当年黑边是 Flutter 自绘圆角路线缺陷, DESIGN.md 坑位)。
    窗口属 flet 前端进程 (非本 python 进程), 按标题定位: update_title 置脏后
    标题变 "* Tangyuan", FindWindowW 全等匹配会脱靶 → 启动 6s 窗口内用户改配置
    就圆角失败回退矩形 (2026-08-30 审查)。改用 EnumWindows 子串匹配,
    精确名/置脏名优先; 超时/调用失败返回 False → 调用方回退矩形并在状态栏留档。"""
    if sys.platform != "win32":
        return False
    import ctypes
    try:
        user32 = ctypes.windll.user32
        dwm = ctypes.windll.dwmapi
        wnd_enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        matches: list[tuple[int, str]] = []

        def _collect(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                n = user32.GetWindowTextLengthW(hwnd)
                if n > 0:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    user32.GetWindowTextW(hwnd, buf, n + 1)
                    if title in buf.value:
                        matches.append((hwnd, buf.value))
            return True

        deadline = time.time() + timeout
        hwnd = 0
        while time.time() < deadline and not hwnd:
            matches.clear()
            user32.EnumWindows(wnd_enum_proc(_collect), 0)
            # 精确名优先, 其次置脏名, 最后任意包含 (z-order 首个)
            for want in (title, f"* {title}"):
                for h, t in matches:
                    if t == want:
                        hwnd = h
                        break
                if hwnd:
                    break
            if not hwnd and matches:
                hwnd = matches[0][0]
            if not hwnd:
                time.sleep(0.3)
        if not hwnd:
            return False
        pref = ctypes.c_int(2)   # DWMWCP_ROUND
        return dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), 4) == 0
    except Exception:  # noqa: BLE001 - ctypes 调用兜底: 回退矩形
        return False


def _strip_connect_arg(val: bytes, token: bytes = b"+connect") -> bytes:
    """从启动参数中剥离已有的 <token> <地址> 参数(含其前导空白), 返回清理后字节。
    无该 token 时原样返回。用于自动进服更新时替换旧地址 (deep-review F2);
    v2.3.0 参数化 token 以同样机制支持 +map (练枪一键进入)。
    词边界: token 后必须紧跟空白或串尾, 防误剥 +connectivity 等参数 (deep-review 4轮 LOW5)。
    循环剥离全部 (deep-review 8轮 F1): 原实现只剥第一个,
    多个同类 token 时第二个残留, 空值剥离模式清理不彻底。"""
    low_tok = token.lower()
    while True:
        low = val.lower()
        i = low.find(low_tok)
        while i >= 0:
            j = i + len(low_tok)
            if j == len(low) or low[j:j + 1] in (b" ", b"\t"):
                break
            i = low.find(low_tok, j)
        if i < 0:
            return val
        j = i + len(low_tok)
        while j < len(val) and val[j:j + 1] in (b" ", b"\t"):
            j += 1                       # 跳过 token 与地址之间的空白
        while j < len(val) and val[j:j + 1] not in (b" ", b"\t"):
            j += 1                       # 跳过地址 token (到下一个空白或串尾)
        k = i
        while k > 0 and val[k - 1:k] in (b" ", b"\t"):
            k -= 1                       # 向前吃掉 token 前的空白
        val = (val[:k] + val[j:]).strip()


def _is_hovered(e) -> bool:
    """on_hover 事件 data 兼容 (flet 0.86.5 真布尔 / 旧版字符串, 与 ui.py 同款)。"""
    return e.data is True or e.data == "true"


def _procname_patch(ini_path, new_value, token="+connect"):
    """临时把 [Loader] ProcName 行替换为 原值 + ' <token> <value>'
    (Loader.exe 读取该文件构建 csgo.exe 命令行: +connect 自动进服;
    v2.3.0 参数化 token, 练枪模式以 '+map aim_botz' 同机制追加)。
    纯字节级行内替换: 不经过 model/编码往返, 保证无关字节零改动。
    返回 (原始行字节, patch 后新行字节) (供启动后恢复; 恢复前比对当前行,
    被用户保存覆盖时跳过恢复); 失败/无需改动返回 None。
    大小写不敏感 (通过 lowercase 副本定位, 切片仍取原字节)。"""
    nv = str(new_value or "").strip()
    tok = token.encode("ascii", errors="replace")
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
    # 已有同类 token (手动或上次残留): 剥离旧地址再追加新值, 保证新值生效 (deep-review F2)
    old_val = _strip_connect_arg(old_val, tok)
    if nv:
        new_line = line[:eq + 1] + ws + old_val + b" " + tok + b" " + nv.encode("ascii", errors="replace")
    elif old_val != val_raw.strip():
        # 该 token 已禁用 (nv 为空): 剥离上次残留后写回。
        # 残留来源: 启动后 10s 窗口内退出应用, poll 线程的 _procname_restore
        # 未执行 → 旧参数永久留在 rev.ini (deep-review 7轮 task-1 HIGH)。
        # 返回 None: 剥离是清理不是临时 patch, 不进 restore 链。
        new_line = line[:eq + 1] + ws + old_val
    else:
        return None   # 无残留, 无需改动
    if line.endswith(b"\r"):   # CRLF 文件: 保留行尾 \r, 避免中间态混行尾
        new_line += b"\r"
    try:
        tmp = ini_path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(raw[:ls] + new_line + raw[le:])
        os.replace(tmp, ini_path)
    except OSError:
        # 原子写纪律 (与 ini_model.save 一致): 失败清 tmp, 目标文件保持原样
        try:
            if os.path.exists(ini_path + ".tmp"):
                os.remove(ini_path + ".tmp")
        except OSError:
            pass
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
    tmp = ini_path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(raw[:ls] + orig_line + raw[le:])
        os.replace(tmp, ini_path)
    except OSError:
        # 原子写纪律 (与 ini_model.save 一致): 失败清 tmp, 目标文件保持原样
        try:
            if os.path.exists(ini_path + ".tmp"):
                os.remove(ini_path + ".tmp")
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


def _map_asset_path() -> str | None:
    """内置练枪图 (assets/maps/aim_botz.bsp): 开发 = 仓库 assets;
    打包后 = 安装目录 assets (installer.iss 随包, 同 _preset_src_dir 模式)。缺失返回 None。"""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for c in (os.path.join(here, "assets", "maps", "aim_botz.bsp"),
              os.path.join(os.path.dirname(sys.executable), "assets", "maps", "aim_botz.bsp")):
        if os.path.isfile(c):
            return c
    return None


def _ensure_aim_map(csgo_dir: str) -> str | None:
    """练枪图就位: 把内置 aim_botz.bsp 拷入 csgo/maps (启动器自带, 非游戏原件)。
    已存在同名文件 → 不覆盖 (AGENTS.md 铁律), 直接用现有的 (含用户自装版本)。
    返回 None=就绪; 字符串=错误信息。"""
    src = _map_asset_path()
    if not src:
        return "内置练枪图缺失 (assets/maps/aim_botz.bsp)"
    maps_dir = os.path.join(csgo_dir, "csgo", "maps")
    if os.path.isfile(os.path.join(maps_dir, "aim_botz.bsp")):
        return None
    try:
        os.makedirs(maps_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(maps_dir, "aim_botz.bsp"))
    except OSError as e:
        return f"练枪图安装失败: {e}"
    return None


def _target_scheme(cfg: dict) -> str:
    """主题三态 → 当前应处方案: dark / light / scheduled。
    scheduled: dark_start-dark_end 区间内深色, 跨午夜区间 (19:00-07:00) 正确处理;
    start==end 视为全天深色; 时间串解析失败回退 19:00/07:00 默认。"""
    mode = str(cfg.get("theme_mode") or "scheduled")
    if mode in ("dark", "light"):
        return mode

    def _hm(v, fb):
        try:
            h, m = str(v).strip().split(":")
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            return fb

    start = _hm(cfg.get("theme_dark_start"), 19 * 60)
    end = _hm(cfg.get("theme_dark_end"), 7 * 60)
    now = time.localtime()
    cur = now.tm_hour * 60 + now.tm_min
    if start == end:
        return "dark"
    if start < end:
        return "dark" if start <= cur < end else "light"
    return "dark" if cur >= start or cur < end else "light"


def _server_presets(cfg: dict | None = None) -> list[dict]:
    """规范化服务器预设列表 (settings.server_presets): 仅保留含 addr 的条目。"""
    ps = (cfg or load_settings()).get("server_presets")
    if not isinstance(ps, list):
        return []
    out = []
    for p in ps:
        if isinstance(p, dict) and str(p.get("addr") or "").strip():
            item = {"name": str(p.get("name") or str(p["addr"]).strip()),
                    "addr": str(p["addr"]).strip()}
            if p.get("sid"):
                item["sid"] = str(p["sid"])   # 状态 API 的服务器 id (在线状态映射)
            out.append(item)
    return out


def main(page: ft.Page):
    page.title = "Tangyuan"
    page.theme_mode = ft.ThemeMode.DARK
    # 6px 细滚动条 (批次④试做项, HTML .content::-webkit-scrollbar 6px;
    # 卡顿/难看即降级删除 scrollbar_theme — 降级处见批次④留档)
    page.theme = ft.Theme(
        color_scheme_seed=theme.COL_BRAND, font_family=FONT_CN,
        scrollbar_theme=ft.ScrollbarTheme(
            thickness=6, radius=3,
            thumb_color=theme.COL_BORDER_VISIBLE,
            track_visibility=False,
            cross_axis_margin=3, min_thumb_length=36, interactive=True))
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

    # -- 主题 (v2.3.0): 启动即按 settings 三态 (dark/light/scheduled) 应用深浅,
    # 之后构建的全部控件取到的就是当前方案色值 --
    # theme_mode 必须随方案: 无显式颜色的 Text 按 theme_mode 取默认色
    # (卡在 DARK → 浅色下一族文字白字不可读, 2026-08-30 视觉评审)
    _cfg0 = load_settings()
    theme.set_scheme(_target_scheme(_cfg0))
    page.theme_mode = (ft.ThemeMode.LIGHT if theme.get_scheme() == "light"
                       else ft.ThemeMode.DARK)

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
          "loaded_name": "NO FILE LOADED", "dirty": False,
          "view": "home",                 # 当前视图: home/editor/avatar (主题重建判定)
          "theme_epoch": 0,               # 主题换装次数 (编辑页惰性重建判定)
          "editor_epoch": 0,              # 编辑页表面构建时的 theme_epoch
          "connect_server": "",           # 主服地址 (rev.ini Loader.ConnectServer, 胶囊/启动跟随)
          "servers_api": None}            # 状态 API 原始数据 (None=拉取失败; ServerPanel 数据源)
    model = None
    field_rows = []  # [(field, value_ref, control)]
    nav_index = 0
    # 主页控件句柄: 由 _rebuild_home() 统一创建 (主题换装后整组重建, v2.3.0);
    # title_bar/view_switcher/_root 由后续代码赋值, _rebuild_home 首次调用时跳过引用
    avatar = nick_label = unlocated_hint = home_err = hint_box = None
    server_monitor = server_panel = launch_btn = None
    home_win_controls = launcher_head = launcher_view = None
    # 头像页表面句柄 (仅由 _rebuild_avatar_surfaces 赋值; 预置 None 提供 nonlocal 绑定)
    avatar_preview = crop_canvas = avatar_head = avatar_view = avatar_win_controls = None
    view_switcher = title_bar = _root = None

    # -- UI 引用 --
    # 状态栏 (design-system.md #26): 常态仅绿勾图标, 无文字 (v1.16 定稿);
    # status_msg 仅错误时显示 (set_status err 分支), status_icon 错误时切红 ERROR 图标
    status_msg = ft.Text("", size=12, color=theme.COL_ERR)
    status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=theme.COL_OK)
    # 编码选择: ui.enc_group 自绘分段 (design-system #27)。原 SegmentedButton
    # 亮蓝实心被用户反馈"难看"且选中/未选中无法分离样式 (0.86.5 style 整体应用),
    # 改为 ghost 底容器 + 20% 主色浅底选中段 (2026-08 UI 审查)
    enc_selector = ui.enc_group([("gbk", "ANSI"), ("utf-8", "UTF-8")], "gbk",
                                on_change=lambda v: _on_enc_change(v))
    save_btn = None   # 实际定义在标题栏构建处 (editor_head, 2026-08 新设计: 保存移顶栏)
    content_area = ft.Container(expand=True, bgcolor=theme.COL_BG_MAIN)

    # -- 工具函数 --
    def set_status(text, ok=False, err=False):
        # 仅图标定稿 (v1.16): 成功/普通状态不显示文字, 只留绿勾;
        # 错误时显示中文错误文字 + 红色 ERROR 图标 (临时显示, 可被下次状态覆盖)
        if ok:
            status_msg.value = ""
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = theme.COL_OK
        elif err:
            status_msg.value = text
            status_msg.color = theme.COL_ERR
            status_icon.name = ft.Icons.ERROR_OUTLINE
            status_icon.color = theme.COL_ERR
        else:
            status_msg.value = ""
            status_icon.name = ft.Icons.CHECK_CIRCLE
            status_icon.color = theme.COL_OK
        page.update()

    # 临时提示 (2026-08 保存反馈): v1.16 常态仅图标, 但保存等关键操作无任何
    # 文字反馈会显得"没反应"(用户反馈 CFG 保存状态栏不提示) — 显示 3 秒后自动清除
    _flash_seq = {"n": 0}

    def _flash_status(text, err=False):
        _flash_seq["n"] += 1
        seq = _flash_seq["n"]
        status_msg.value = text
        status_msg.color = theme.COL_ERR if err else theme.COL_OK
        status_icon.name = ft.Icons.ERROR_OUTLINE if err else ft.Icons.CHECK_CIRCLE
        status_icon.color = theme.COL_ERR if err else theme.COL_OK
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
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
                ft.FilledButton("丢弃并继续", on_click=lambda e: (_close(), on_confirm()),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CARD),   # Win11 卡片档 (v2.3.1)
        )
        page.show_dialog(dlg)

    def guard_dirty(action):
        """dirty 时弹确认, 否则直接执行"""
        if st["dirty"]:
            confirm_discard(action)
        else:
            action()

    def update_title():
        base = "Tangyuan"
        page.title = ("* " if st["dirty"] else "") + base
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
                    page.update()
                    ini = os.path.join(p, "rev.ini")
                    if os.path.isfile(ini):
                        load_file(ini)
                    return
                page.update()
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
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
                        ft.FilledButton("仍然使用", on_click=lambda e: (_close(), guard_dirty(_apply)),
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                    shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CARD),
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
                # ui.SelectDark (v2.3.1 自绘下拉) 鸭子类型兼容 ft.Dropdown:
                # .value 可写 / .options 元素含 .key / .error_text 可写
                if isinstance(ctrl, (ft.Dropdown, ui.SelectDark)):
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
        page.update()
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
        label = field["label"]
        desc, ftype, default = field.get("desc", ""), field["type"], field.get("default", "")
        vr = {"v": str(default) if default is not None else ""}

        if ftype == "bool":
            val = bool(default)
            vr["v"] = val
            ctrl = ft.Switch(value=val,
                active_color=ft.Colors.WHITE, active_track_color=theme.COL_BRAND,   # 开启: 主色轨道+白滑块
                inactive_thumb_color=theme.COL_SWITCH_INACTIVE_THUMB,
                inactive_track_color=theme.COL_SWITCH_INACTIVE_TRACK,
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))
        elif ftype == "rank":
            # 伪装段位: 选项为 RANK_DISPLAY 段位名, 存储值 = 1-18 数字(保存时转换)
            opts = [ft.dropdown.Option(key=name, text=name) for name in RANK_DISPLAY]
            dflt_name = rank_level_to_name(default) if isinstance(default, int) else str(default)
            # 合法选择必须清除 bad, 否则非法原值字段永久无法通过 UI 修改 (deep-review R2)
            ctrl = ui.select_dark(
                opts, selected=dflt_name, width=236, height=H_INPUT,
                on_select=lambda e: (vr.__setitem__("v", e.control.value),
                                     vr.__setitem__("bad", False),
                                     setattr(e.control, "error_text", None), mark_dirty()))
        elif ftype in ("combo",):
            items = field.get("items", [])
            dm = field.get("display_map") or {}   # M4: 未提供 display_map 时不能 .get() None
            opts = [ft.dropdown.Option(key=i, text=dm.get(i, i)) for i in items]
            ctrl = ui.select_dark(
                opts, selected=str(default) if default else (items[0] if items else ""),
                width=236, height=H_INPUT,
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
                width=236, height=H_INPUT, font_size=15,
                # 48px 框 + 15px 字 (v2.3.1 定稿: 64 框小字头重脚轻, 40px 曾被否决)
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
            # 超长昵称可保存并在主页撑爆固定 360×510 布局); input_dark 内手动截断
            # (flet 0.86.5 无 counter_text, 引擎 maxLength 自带计数器不可隐藏)
            ctrl = ui.input_dark(
                value=str(default) if default else "",
                width=236, height=H_INPUT,   # 48px 定稿: 与下拉/int 档统一, 双列卡等高
                max_length=field.get("maxlen") or None,
                placeholder=field.get("placeholder") or None,   # 占位符接线 (视觉审计 2026-08)
                on_change=lambda e: (vr.__setitem__("v", e.control.value), mark_dirty()))

        if ftype == "textarea":
            # 多行字段卡片 (design-system.md #20 LaunchSplit): 加载器启动命令卡,
            # 通栏不参与双列网格; 内部 ctrl 已是 左textarea:右RecPanel 3:2 分栏
            # (v2.3.1 三轮: 键名 kicker 已删 — rules.md §4.3 隐藏技术细节)
            row = ft.Container(
                content=ft.Column([
                    ft.Text(label, size=14, weight=ft.FontWeight.W_700),
                    ft.Text(desc, size=12, color=theme.COL_TEXT_DIM, opacity=0.85) if desc else ft.Text(""),
                    ft.Container(height=6),
                    ctrl,
                ], tight=True, spacing=2),
                bgcolor=theme.COL_CARD,
                border_radius=theme.RADIUS_CARD,   # Win11 卡片档 (v2.3.1)
                shadow=theme.SHADOW_CARD,
                border=ft.Border(top=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                                 right=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                                 bottom=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                                 left=ft.BorderSide(1, theme.COL_BORDER_SUBTLE)),
                padding=ft.padding.Padding(left=16, top=16, right=16, bottom=16),
                margin=ft.margin.Margin(top=4, bottom=4, left=0, right=0))
            # hover 微交互 (LaunchSplit 内联卡无组件自带 hover, 手动加):
            # 卡片提亮一档 + 品牌边框 (右移 4px 试做后降级 — offset 位移破坏
            # ListView 内卡片渲染, 批次④留档)
            row.on_hover = lambda e, r=row: (
                setattr(r, "bgcolor", theme.COL_BG_GHOST_2 if _is_hovered(e) else theme.COL_CARD),
                setattr(r, "border", ft.Border(
                    top=ft.BorderSide(1, theme.COL_BORDER_BRAND if _is_hovered(e) else theme.COL_BORDER_SUBTLE),
                    right=ft.BorderSide(1, theme.COL_BORDER_BRAND if _is_hovered(e) else theme.COL_BORDER_SUBTLE),
                    bottom=ft.BorderSide(1, theme.COL_BORDER_BRAND if _is_hovered(e) else theme.COL_BORDER_SUBTLE),
                    left=ft.BorderSide(1, theme.COL_BORDER_BRAND if _is_hovered(e) else theme.COL_BORDER_SUBTLE))),
                r.update())
        else:
            # 单字段卡片 (design-system.md #14 ConfigCard): 纵向 — 标题在上, 控件在下
            # desc 固定 2 行高 (HTML field-grid 对齐: 双列卡 desc 行数不同会撑高卡片,
            # 用户反馈 2026-08 界面语言/自动进入服务器大小不一致)
            # 组件库实现 (rules.md §1, deep-review 5轮 MEDIUM-5): ui.config_card 支持
            # desc_lines(固定行高容器, 双列等高); hover 由组件自带
            # (双列内 hover 不右移 — design-system.md #14)
            row = ui.config_card(
                title=label, desc=desc,
                control=ft.Container(content=ctrl, alignment=ft.alignment.Alignment(0, 0)),
                desc_lines=2,
            )
            row.margin = ft.margin.Margin(top=4, bottom=4, left=0, right=0)
        field_rows.append((field, vr, ctrl))
        return row

    def build_page(group):
        # 页头 (design-system.md #12 PageHead): 组件库实现 (v2.3.1 去 kicker)
        items = [ui.page_head(group["title"], group.get("desc", ""))]
        # 字段双列网格 (design-system.md #13 FieldGrid): 组件库实现。
        # STRETCH 在 ListView 无界高度下塌陷 (两次实测 2026-08) → 用固定卡片高度:
        # 内容已统一 (desc 固定 2 行 36px + 控件统一 48px), 卡片高度恒定 = 等高
        return ui.field_grid(group.get("fields", []), build_field_row, header=items[0])

    def build_tools_page(group):
        from app.tools import REPAIR_TOOLS, run_tool
        items = [ui.page_head(group["title"], group.get("desc", ""))]

        # 执行超时设置 (2026-08): 脚本运行超过该秒数会被强制终止进程树
        # 默认 120s; 存字符串便于直接显示, 读取时解析+钳位。
        # 值持久在 st: 换装重建本页时不丢用户自设值 (2026-09-05 审查)
        timeout_field = ft.TextField(
            value=str(st.get("tool_timeout") or "120"), width=110, text_align=ft.TextAlign.CENTER,   # 数字居中 (用户指定 2026-08)
            label="执行超时(秒)", label_style=ft.TextStyle(size=11),
            on_change=lambda e: st.__setitem__("tool_timeout", e.control.value),
            border_color=theme.INPUT_BORDER, focused_border_color=theme.COL_BRAND, fill_color=theme.INPUT_FILL,
            border_radius=theme.RADIUS_CTRL,   # Win11 控件档 (v2.3.1)
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
                    status_txt.color = theme.COL_WARN
                    page.update()

                    def on_done(ok, output):
                        # run_tool 的回调在工作线程触发, UI 变更统一回主线程 (H1)
                        page.run_thread(
                            lambda: _apply_tool_result(ok, output))

                    def _apply_tool_result(ok, output):
                        try:
                            run_btn.set_busy(False)
                            if ok:
                                status_txt.value = "完成"
                                status_txt.color = theme.COL_OK
                                set_status(f"完成: {tool.name}", ok=True)
                            else:
                                status_txt.value = "失败"
                                status_txt.color = theme.COL_ERR
                                set_status(f"失败: {tool.name}: {output[:120]}", err=True)
                            page.update()
                        except Exception:  # noqa: BLE001, S110 - 工具运行期间换装重建,
                            pass  # 旧卡片的 run_btn/status_txt 已废弃: 静默 (状态栏由新控件接管)

                    if not run_tool(d, tool, on_done=on_done, timeout=timeout):
                        # 脚本缺失/无法启动 (启动瞬间文件被删/占用): on_done 不会被回调,
                        # 必须在这里恢复按钮状态, 否则永久卡"运行中…" (2026-08 用户反馈)
                        page.run_thread(lambda: (
                            run_btn.set_busy(False),
                            setattr(status_txt, "value", "无法启动"),
                            setattr(status_txt, "color", theme.COL_ERR),
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
                        size=12, color=theme.COL_TEXT_DIM, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=theme.COL_CARD,
            border_radius=theme.RADIUS_CARD,   # Win11 卡片档 (v2.3.1)
            shadow=theme.SHADOW_CARD,
            border=ft.Border(top=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                             right=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                             bottom=ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                             left=ft.BorderSide(1, theme.COL_BORDER_SUBTLE)),
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
        # 行间竖距 = space-10 (tokens.md §4 .tool-grid gap): 原 ListView 漏传
        # spacing 且行间无垫片, 两行卡片竖向贴死 (2026-09-05 用户反馈增加间距);
        # 不用 ListView spacing — 那会把页头/超时卡/风险告知的接缝一并撑大
        for i in range(0, len(tool_cards), 2):
            pair = tool_cards[i:i + 2]
            if i > 0:
                items.append(ft.Container(height=10))
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
            # 容错变体: 双空格/引号包裹 (+exec "auto.cfg") 不误报缺失 (2026-09-05 审查)
            return bool(m and re.search(r'(?i)\+exec\s+"?auto\.cfg"?', m.group(0)))
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
            tmp = ini + ".tmp"
            try:
                with open(tmp, "wb") as f:
                    f.write(bytes([10]).join(lines))
                os.replace(tmp, ini)
            except OSError:
                # 原子写纪律 (与 ini_model.save 一致): 失败清 tmp 再交外层报错
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass
                raise
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

    def build_cfg_page(reload: bool = True):
        """构建 CFG 配置页: 顶部说明 + 提示条(ProcName/缺失) + 4 组表单卡片。
        reload=False 跳过重读磁盘、沿用 cfg_vrs 现值 — 换装重建 (_rebuild_editor_
        surfaces) 时保护未保存的 CFG 修改: _cfg_load 会清空重读, st["cfg_dirty"]
        的编辑被静默丢弃 (2026-08-30 二轮审查)。丢弃路径 (切页/返回) 都先清
        cfg_dirty 再重建, 语义不受影响。"""
        if reload or not cfg_vrs:
            _cfg_load()
        items: list[ft.Control] = []
        # 顶部说明 (2026-08-23 用户指定: 从页底移到最上面, 进入即见适用范围)
        items.append(ft.Container(
            content=ft.Text("修改会写入 s0up 预设 (auto.cfg / crosshair.cfg), 保存前自动备份。",
                            size=12, opacity=0.85),
            padding=ft.padding.Padding(left=0, top=2, right=0, bottom=8)))
        # 提示条 1: 启动参数缺 +exec auto.cfg (预设被 config.cfg 覆盖, 2026-08 拷问 F2)
        warn_banner = False
        if not _cfg_procname_has_exec():
            warn_banner = True
            items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=theme.COL_WARN),
                    ft.Text("启动参数缺少 +exec auto.cfg, 预设可能被游戏配置覆盖", size=12,
                            color=theme.COL_TEXT_PRIMARY, expand=True),
                    ft.OutlinedButton(
                        "一键添加", on_click=_cfg_add_exec, height=28,
                        style=ft.ButtonStyle(
                            bgcolor=theme.COL_BRAND, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=theme.COL_WARN_BG, border=ft.Border.all(1, theme.COL_WARN),
                border_radius=theme.RADIUS_CTRL,   # Win11 控件档 (v2.3.1)
                padding=ft.padding.Padding(left=12, top=8, right=8, bottom=8)))
        # 提示条 2: 预设文件缺失 (两条同现时垫 space-10 — 与卡片贴死同族漏间距, 2026-09-05)
        if cfg_missing:
            if warn_banner:
                items.append(ft.Container(height=10))
            items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=theme.COL_ERR),
                    ft.Text(f"预设文件缺失: {'、'.join(cfg_missing)}, 可重新植入", size=12,
                            color=theme.COL_TEXT_PRIMARY, expand=True),
                    ft.OutlinedButton(
                        "重新植入", on_click=_cfg_restore_preset, height=28,
                        style=ft.ButtonStyle(
                            bgcolor=theme.COL_BRAND, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=theme.COL_ERR_BG, border=ft.Border.all(1, theme.COL_ERR),
                border_radius=theme.RADIUS_CTRL,
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
                        opts, selected=vr["v"], width=236, height=H_INPUT,
                        on_select=lambda e, vr=vr, f=f: _on_cfg_change(e, vr, f))
                else:
                    # 数字字段等宽 13px + 显式 48px 高 (v2.3.1: 字段卡 48/字15/mono13/下拉14)
                    ctrl = ui.input_dark(
                        vr["v"], width=236, height=H_INPUT, mono=True, font_size=13,
                        placeholder=str(f.default) if f.default is not None else "",
                        on_change=lambda e, vr=vr, f=f: _on_cfg_change(e, vr, f))
                # desc_lines=1 强制说明行等高, 双列卡片高度对齐
                cards.append(ui.config_card(f.label, f.unit, ctrl, desc_lines=1))
            # 组标题 (15px/700 与卡片标题 14px 拉开层级, 2026-08-23 显示优化)
            items.append(ft.Container(
                content=ft.Text(gn, size=15, weight=ft.FontWeight.W_700,
                                color=theme.COL_TEXT_SECONDARY),
                padding=ft.padding.Padding(left=0, top=18, bottom=6)))
            # 双列 (2 张一行, 同字段页 field-grid); 奇数行最后一张单卡也包 Row
            # 约束内容宽度 — 直接 append 会撑满整行 648px (准星透明度卡巨宽, 用户反馈 2026-08-23)
            # 行间竖距 = space-10 (tokens.md §4 field-grid/tool-grid gap; 拷问定稿
            # 2026-09-05): 原 ListView 漏传 spacing, 组内两行卡片贴死 — 同工具页
            # 垫片法, 不用 ListView spacing (会把组标题 top18/顶部说明接缝一并撑大)
            for i in range(0, len(cards), 2):
                pair = cards[i:i + 2]
                if i > 0:
                    items.append(ft.Container(height=10))
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
            icon=ft.Icon(icon, color=theme.COL_TEXT_DIM),
            selected_icon=ft.Icon(icon, color=theme.COL_BRAND_SOFT),
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
            # 取消分支已把 rail 高亮拨回旧页: 确认切换后须重新指到目标页
            # (非 dirty 路径 rail 已自行高亮 target, 此处赋同值无副作用)
            nav_rail.selected_index = target
            content_area.content = nav_content[nav_index]
            # 顶栏保存按钮语义随页切换: CFG 页保存 CFG, 其他页保存 rev.ini
            save_btn.on_click = _save_cfg if nav_index == CFG_NAV_INDEX else on_save
        if nav_index == CFG_NAV_INDEX and st["cfg_dirty"]:
            # 已有对话框开着时先弹掉 (连点导航/主题菜单未关等), 防确认框栈式叠加
            # (与 on_close_window 同模式, deep-review R8)
            try:
                page.pop_dialog()
            except Exception:  # noqa: BLE001, S110 - 无对话框可弹: 静默
                pass
            # NavigationRail 在 on_change 触发前已自行高亮目标项; 取消丢弃时必须
            # 拨回当前页, 否则高亮与内容错位, 且再点高亮项因索引未变不再触发
            # on_change, 用户看起来"卡在旧页" (2026-08-30 审查)
            e.control.selected_index = nav_index
            page.update()
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

    # -- 窗口焦点跟踪 (2026-08-30 审查): 切视图仅在窗口确实失焦时拉焦点。
    # 原实现 show_launcher/show_editor 无条件 focused=True, 每次视图切换都会
    # 抢走用户正在其它窗口的输入焦点; 但 2026-08 实测过 frameless 未聚焦窗口
    # "首次点击被窗口管理器吞掉" — 保留兜底语义: on_event 从未收到事件
    # (跟踪不可用) 时退化为总是聚焦。
    _win_focus = {"seen": False, "blurred": False}

    def _on_window_event(e):
        try:
            _win_focus["seen"] = True
            # e.type 正常是 WindowEventType 枚举; 取 .value 兼容裸字符串载荷
            t = getattr(e.type, "value", e.type)
            if t == "blur":
                _win_focus["blurred"] = True
            elif t == "focus":
                _win_focus["blurred"] = False
        except Exception:  # noqa: BLE001, S110 - 事件载荷异常只影响跟踪, 不碰 UI
            pass

    def _focus_if_unfocused():
        if not _win_focus["seen"] or _win_focus["blurred"]:
            page.window.focused = True

    page.window.on_event = _on_window_event

    # ==================== 主页启动台 ====================
    def _apply_avatar(nick):
        """头像: 清晰版(用户数据目录 256px) → avatar.dat → avatar1.dat →
        主界面底色圆 + 昵称首字母。

        两套逻辑 (2026-08-23): 游戏头像 64×64 固定, 主页展示优先读 256px
        清晰版不糊; 缺失回退 64 版兼容旧数据/首次运行。
        用裸 base64 而非文件路径: flet Image 对同一文件路径有渲染缓存,
        保存头像后主页仍显示旧图 (实测 2026-08-23); base64 内容变化即强制重绘。
        """
        src = find_preview_path() or find_avatar_path(st["csgo_dir"] or find_csgo_dir())
        if src:
            try:
                with open(src, "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
            except OSError:
                b64 = ""
            if b64:
                # 必须固定 width/height: Image 不设尺寸会按原始分辨率渲染
                # (实测 avatar.dat 235×315 撑破布局, 盖住昵称/头衔/胶囊)
                avatar.content = ft.Image(src=b64, width=theme.S_AVATAR, height=theme.S_AVATAR,
                                          fit=ft.BoxFit.COVER,
                                          filter_quality=ft.FilterQuality.HIGH,  # 低清 avatar.dat 缩放平滑 (2026-08 UI 审查)
                                          border_radius=theme.S_AVATAR // 2)
                return
        avatar.content = ft.Text((nick or "汤")[:1], size=FONT_36,
                                 color=theme.COL_BRAND_LIGHT, weight=ft.FontWeight.W_700)

    # 主页控件实例 (avatar/nick_label/hint_box 等) 已移入 _rebuild_home() 统一创建
    # (v2.3.0 主题换装重建); 此处仅保留主页逻辑函数, 全部经闭包按名解析最新控件。

    def _sync_launch_btn_async():
        """启动按钮状态回填: tasklist 进程探测 (~100-300ms) 挪到后台线程,
        不阻塞回主页/换装重建的 UI 路径 (2026-08-30 审查); 结果经 run_thread
        回 UI (H1)。探测期间用户点启动无碍 — on_launch_click 自带 csgo_running
        进程级幂等检查。控件已随换装重建时 apply 静默 (set_state 由新控件接管)。"""
        if st.get("launching"):
            return

        def _probe():
            running = csgo_running()

            def _apply():
                try:
                    if not st.get("launching"):
                        if running:
                            launch_btn.set_state("running", "游戏运行中")
                        else:
                            launch_btn.set_state("idle")
                except Exception:  # noqa: BLE001, S110 - 控件已随换装重建: 静默
                    pass

            page.run_thread(_apply)

        threading.Thread(target=_probe, daemon=True).start()

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
                # 主服 = 常用设置 ConnectServer 目标 (状态胶囊/启动跟随, design-system #7)
                st["connect_server"] = str(m.get("Loader", "ConnectServer", "") or "").strip()
                nick_label.value = nick
                hint_box.controls = []
                home_err.value = ""
                _apply_avatar(nick)
                # 切回主页同步启动按钮状态: 游戏运行中保持"已启动 ✓" (R6)
                # (tasklist 探测已挪后台 — 原同步调用阻塞每次回主页 100-300ms)
                _sync_launch_btn_async()
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


    def on_launch_click(_=None, practice: bool = False, connect: str | None = None):
        """轻检查 + 启动 Loader + 轮询 csgo.exe 反馈
        (2026-08 deep-review R1/R3/R4:
        - R1: Loader.exe 带 requireAdministrator 清单, 普通 Popen 抛 WinError 740 →
          用 ShellExecuteW runas 提权启动 (方案复用自 D:\\Launcher)
        - R4: 仅 csgo.exe 判定"已启动"; Loader 存活只拒绝二次 Popen, 不显示假成功
        v2.3.0: practice=True 时追加 +map aim_botz 练枪启动 (与服务器直连互斥,
        不使用 practice.cfg — 直接加载地图)
        v2.3.1: connect=ServerPanel「进入」的一次性目标 — 仅本次启动追加
        +connect, 不改常用设置 ConnectServer (design-system #34)"""
        if st.get("launching"):
            return
        # 进程级幂等: 仅以 csgo.exe 判定游戏在运行 (Loader 生命周期不可靠, R4)
        if csgo_running():
            launch_btn.set_state("running", "游戏运行中")
            page.update()
            return
        d = st["csgo_dir"] or find_csgo_dir() or ""
        # newloader 自动就位 (2026-09-05 拷问定稿): 目录缺失才从 assets 静默安装
        # (md5 幂等, 不覆盖原版 Loader.exe); 失败静默 → 走下面的原版回退。
        # 修复工具页同名工具已删, 就位不再依赖用户手动跑工具。
        if d:
            _install_loader(d, None)
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
        # 练枪模式 (v2.3.0): 先把内置 aim_botz.bsp 就位 (幂等, 不覆盖已有同名地图)
        if practice:
            map_err = _ensure_aim_map(d)
            if map_err:
                show_home_error(map_err)
                return
        # 启动参数注入 (v2.3.0): 练枪 = 剥残留 +connect 后临时追加 +map aim_botz;
        # 普通启动 = 剥残留 +map 后, 主页选中服务器优先, 否则跟随常用设置 ConnectServer。
        # 均临时追加到启动目标 rev.ini 的 ProcName 行 (Loader.exe 读此文件构建 csgo.exe
        # 命令行, deep-review R7 同源规则), csgo.exe 出现后由 poll 恢复原样。失败静默。
        proc_orig = proc_new = None
        try:
            if practice:
                _procname_patch(ini, "")   # 清残留 +connect (练枪进本地地图, 不连服)
                _patched = _procname_patch(ini, "aim_botz", token="+map")
                if _patched:
                    proc_orig, proc_new = _patched
            else:
                # 剥离上次练枪启动残留的 +map (10s 窗口内退出应用时 poll 未恢复)
                _procname_patch(ini, "", token="+map")
                _m = RevIni.load(ini)
                auto_join = str(_m.get("Loader", "ConnectServer", "") or "").strip()
                # ServerPanel「进入」的一次性目标优先 (v2.3.1: 不改 ConnectServer 配置);
                # 否则跟随常用设置 ConnectServer 字段
                one_shot = str(connect or "").strip()
                if one_shot:
                    auto_join = one_shot
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
        def _begin_launch(tooltip):
            st["launching"] = True      # 防连点 (UAC 等待期同样拦截)
            launch_btn.set_state("launching", tooltip)
            page.update()

        def _start_poll():
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

        try:
            subprocess.Popen([loader_exe], cwd=d)
        except OSError as e:
            if getattr(e, "winerror", None) == 740:
                # Loader 需要管理员权限 (requireAdministrator manifest, 原版/优化版都有):
                # ShellExecuteW runas 提权启动, 弹出 UAC 确认 (R1)。
                # 挪后台线程 + 提前提示 (2026-09-05 拷问定稿): ShellExecuteW 阻塞至
                # 用户处置 UAC, 主线程保持可刷, 避免"点了没反应, 突然弹窗";
                # 批准 → 统一轮询, 取消 → 按钮复位 + 红字
                _begin_launch("等待管理员确认…")
                show_home_error("系统将弹出管理员确认 (UAC), 请点「是」以启动游戏")

                def _elevate():
                    import ctypes
                    try:
                        res = ctypes.windll.shell32.ShellExecuteW(
                            None, "runas", loader_exe, "", d, 1)
                    except Exception:  # noqa: BLE001 - ShellExecuteW 调用兜底, 失败归入取消路径
                        res = 0

                    def _apply():
                        try:
                            if res <= 32:
                                st["launching"] = False
                                _procname_restore(ini, proc_orig, proc_new)
                                launch_btn.set_state("idle")
                                show_home_error("管理员确认未通过 (UAC 被取消), 未启动游戏")
                            else:
                                _start_poll()
                            page.update()
                        except Exception:  # noqa: BLE001, S110 - 会话已关/控件已重建: 静默
                            pass

                    try:
                        page.run_thread(_apply)
                    except Exception:  # noqa: BLE001, S110 - 会话已关: 静默
                        pass

                threading.Thread(target=_elevate, daemon=True).start()
                return
            else:
                _procname_restore(ini, proc_orig, proc_new)
                show_home_error(f"启动失败: {e}")
                return

        _begin_launch("启动中…")
        _start_poll()

    # 启动按钮/服务器状态胶囊句柄由 _rebuild_home() 创建 (v2.3.0 主题换装重建)
    # 数据源: https://cs.suchitems.top/api/status (未烬官网状态 API)
    SERVER_STATUS_API = "https://cs.suchitems.top/api/status"

    def _refresh_server():
        """拉取状态 API → 按主页当前选中服务器显示在线状态。
        API 实际返回 {"servers":[{id,status,players,maxplayers,…}]} (2026-08-30 实测);
        旧实现解析顶层 online/lastBeat 字段 — 该字段已不存在, 监控恒显示离线, 本次一并修正。
        线程安全: 工作线程调用, 控件变更经 page.run_thread 回主线程 (项目规则 H1)。
        红线 (rules.md §4.2): online 才显示人数; 网络失败显示「离线」不编造。"""
        def _do():
            servers = None   # None=拉取失败 (区别于空列表)
            try:
                req = urllib.request.Request(SERVER_STATUS_API, headers={
                    "User-Agent": "RevIni-Editor/1.0", "Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    d = json.loads(resp.read().decode("utf-8", "replace"))
                servers = {str(s.get("id")): s for s in d.get("servers", [])
                           if isinstance(s, dict) and s.get("id")}
            except Exception:  # noqa: BLE001 - 网络/JSON/类型兜底全部归离线
                servers = None
            page.run_thread(lambda: _apply_server_status(servers))

        threading.Thread(target=_do, daemon=True).start()

    def _apply_server_status(servers):
        """主线程: 刷新 ServerPanel 分服行 + 状态胶囊。
        胶囊 = 主服 (常用设置 ConnectServer 目标, design-system #7): 命中预设带 sid
        → 显示该服状态; 未命中 → 聚合 (任一在线=在线, 人数求和)。
        面板行 = 逐预设真实状态; API 拉取失败/无 sid → 「获取失败」灰点,
        禁止编造 (rules.md §4.2)。"""
        st["servers_api"] = servers
        presets = _server_presets()
        rows = []
        for p in presets:
            ent = servers.get(p["sid"]) if servers and p.get("sid") else None
            if servers is None or not p.get("sid"):
                rows.append({"name": p["name"], "addr": p["addr"], "status": "error"})
            elif ent is None:
                rows.append({"name": p["name"], "addr": p["addr"], "status": "offline"})
            else:
                rows.append({"name": p["name"], "addr": p["addr"],
                             "status": "online" if str(ent.get("status")) == "online" else "offline",
                             "players": ent.get("players"),
                             "maxplayers": ent.get("maxplayers")})
        server_panel.set_servers(rows)

        status, label, count = "offline", "离线", ""
        if servers:
            target = str(st.get("connect_server") or "").strip()
            preset = next((p for p in presets if p["addr"] == target), None)
            ent = servers.get(preset["sid"]) if preset and preset.get("sid") else None
            if ent is not None:
                label = preset["name"]
                if str(ent.get("status")) == "online":
                    status = "online"
                    pl, mx = ent.get("players"), ent.get("maxplayers")
                    if pl is not None:
                        count = f"{pl} / {mx if mx is not None else '?'} 人"
            else:
                online = [s for s in servers.values() if str(s.get("status")) == "online"]
                if online:
                    status, label = "online", "在线"
                    count = f"{sum(s.get('players') or 0 for s in online)} 人"
        server_monitor.set_status(status, label, count)
        page.update()

    def gap(h):
        return ft.Container(height=h)

    # ==================== 服务器悬停面板 (v2.3.1: 直连下拉已删) ====================
    _sp_timer = None   # 悬停收起延迟 Timer (150ms 防误关, design-system #34)

    def _sp_show(_e=None):
        """悬停胶囊/面板 → 展开面板 (panel-in 150ms)"""
        nonlocal _sp_timer
        if _sp_timer is not None:
            _sp_timer.cancel()
            _sp_timer = None
        if not server_panel.visible:
            # panel-in 150ms 已降级为即时显示 (offset 动画实机破坏布局, 批次③留档)
            server_panel.visible = True
            page.update()

    def _sp_hide(_e=None):
        """移出胶囊/面板 → 150ms 后收起 (防误关); 期间移回即取消"""
        nonlocal _sp_timer
        if _sp_timer is not None:
            _sp_timer.cancel()

        def _do():
            nonlocal _sp_timer
            _sp_timer = None
            if server_panel.visible:
                server_panel.visible = False
                try:
                    page.update()
                except Exception:  # noqa: BLE001, S110 - 已重建: 静默
                    pass
        _sp_timer = threading.Timer(0.15, lambda: page.run_thread(_do))
        _sp_timer.daemon = True
        _sp_timer.start()

    def _enter_server(addr: str):
        """ServerPanel「进入」: 一次性 +connect 该服启动, 不改常用设置 (design-system #34)"""
        _sp_hide()
        on_launch_click(None, connect=addr)

    # ==================== 主题切换 (v2.3.0): 深 / 浅 / 定时 ====================
    def _theme_btn():
        # 图标指示当前方案: 深色=月亮, 浅色=太阳; 点击弹菜单
        icon = ft.Icons.DARK_MODE if theme.get_scheme() == "dark" else ft.Icons.LIGHT_MODE
        return ui.win_btn(icon, "主题", on_click=_open_theme_menu)

    def _redress_nonhome():
        """非主页视图的就地即时换装 (拷问定稿 2026-09-05): 编辑/头像页停留时切
        主题, 经 show_editor/show_avatar 开头的 epoch 检查触发表面重建并装回树 —
        未保存修改 (CFG reload=False / rev.ini model 回填)、当前导航页、裁剪
        状态、窗口尺寸全部保留。原惰性策略 ("返回主页后应用") 的惰性重建只在
        show_* 进入时检查, 人已站在页面上就等不到 — 即配置页改深浅色不刷新的
        病灶。头像页无主题按钮, 手动切换只发生在编辑页; 头像页分支仅定时轮询
        可达。avatar 页把 st["view"] 置 "editor" (按非主页处理), 故以树上表面
        的身份判断区分两者。"""
        if view_switcher.content is avatar_view:
            show_avatar()
        else:
            show_editor()

    def _apply_theme_mode(mode: str):
        """手动三态切换: 持久化 → 换装 → 当前视图即时重建 (主页整组 / 编辑·头像就地)。"""
        save_settings({"theme_mode": mode})
        theme.set_scheme(_target_scheme(load_settings()))
        _apply_page_theme()
        st["theme_epoch"] += 1
        if st.get("view", "home") == "home":
            _rebuild_home()
        else:
            _redress_nonhome()
            set_status("主题已切换")
        page.update()

    def _apply_page_theme():
        """页面级主题重建 (换装时调用): theme_mode 随方案切换 —
        无显式颜色的 Text 按 theme_mode 取默认色, 卡在 DARK 会让浅色下
        一族标题/说明渲染成近不可读的白字 (2026-08-30 视觉评审发现);
        6px 细滚动条 thumb 色随深浅重建 (批次④试做项)。"""
        page.theme_mode = (ft.ThemeMode.LIGHT if theme.get_scheme() == "light"
                           else ft.ThemeMode.DARK)
        page.theme = ft.Theme(
            color_scheme_seed=theme.COL_BRAND, font_family=FONT_CN,
            scrollbar_theme=ft.ScrollbarTheme(
                thickness=6, radius=3,
                thumb_color=theme.COL_BORDER_VISIBLE,
                track_visibility=False,
                cross_axis_margin=3, min_thumb_length=36, interactive=True))
        page.update()

    def _open_period_dialog(_=None):
        s_f = ui.input_dark(load_settings().get("theme_dark_start", "19:00"),
                            width=110, mono=True, placeholder="HH:MM")
        e_f = ui.input_dark(load_settings().get("theme_dark_end", "07:00"),
                            width=110, mono=True, placeholder="HH:MM")

        def _save_period(_=None):
            save_settings({"theme_dark_start": (s_f.value or "19:00").strip() or "19:00",
                           "theme_dark_end": (e_f.value or "07:00").strip() or "07:00"})
            page.pop_dialog()
            if str(load_settings().get("theme_mode")) == "scheduled":
                # 定时模式下改时段立即按新区间重算 (非定时模式仅保存, 切到定时后生效)
                theme.set_scheme(_target_scheme(load_settings()))
                # theme_mode 必须随换装 (与 _apply_theme_mode/_apply_scheme_change 同规):
                # 时段修改导致方案翻转时, 卡在旧 theme_mode 会让浅色下一族默认色 Text 白字
                # (2026-08-30 三轮审查)
                _apply_page_theme()
                st["theme_epoch"] += 1
                # 主页即时重建; 编辑/头像页停留时也就地换装 (拷问定稿 2026-09-05,
                # 原"返回主页后应用"惰性策略即配置页改深浅色不刷新的病灶) —
                # _redress_nonhome 只重建当前视图自身, 不会把主页换上屏 (2.3.0
                # 担心的"窗口停在编辑尺寸却换出主页"脱节不存在)
                if st.get("view", "home") == "home":
                    _rebuild_home()
                else:
                    _redress_nonhome()
                    set_status("深色时段已保存, 新配色已应用")

        page.show_dialog(ft.AlertDialog(
            modal=False, bgcolor=theme.COL_BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CARD),
            title=ft.Text("深色时段 (24 小时制)", size=15, weight=ft.FontWeight.W_700,
                          color=theme.COL_TEXT_PRIMARY),
            content=ft.Column([
                ft.Row([ft.Text("深色开始", size=13, color=theme.COL_TEXT_SECONDARY), s_f],
                       spacing=10),
                ft.Row([ft.Text("深色结束", size=13, color=theme.COL_TEXT_SECONDARY), e_f],
                       spacing=10),
                ft.Text("区间内深色、其余浅色; 支持跨午夜 (如 19:00-07:00)",
                        size=11, color=theme.COL_TEXT_DIM),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("取消", on_click=lambda _e: page.pop_dialog()),
                ft.FilledButton("保存", on_click=_save_period,
                                style=ft.ButtonStyle(bgcolor=theme.COL_BRAND,
                                                     color=ft.Colors.WHITE,
                                                     shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL))),
            ], actions_alignment=ft.MainAxisAlignment.END))

    def _open_theme_menu(_=None):
        cur = str(load_settings().get("theme_mode") or "scheduled")

        def _opt(label, mode, icon):
            checked = (cur == mode)
            return ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK if checked else icon, size=15,
                            color=theme.COL_BRAND if checked else theme.COL_TEXT_MUTED),
                    ft.Text(label, size=13,
                            color=theme.COL_TEXT_PRIMARY if checked else theme.COL_TEXT_SECONDARY,
                            weight=ft.FontWeight.W_700 if checked else ft.FontWeight.W_400),
                ], spacing=8, tight=True),
                on_click=lambda _e, m=mode: (page.pop_dialog(), _apply_theme_mode(m)))

        page.show_dialog(ft.AlertDialog(
            modal=False, bgcolor=theme.COL_BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CARD),
            title=ft.Text("主题", size=15, weight=ft.FontWeight.W_700,
                          color=theme.COL_TEXT_PRIMARY),
            content=ft.Column([
                _opt("深色", "dark", ft.Icons.DARK_MODE),
                _opt("浅色", "light", ft.Icons.LIGHT_MODE),
                _opt("定时切换", "scheduled", ft.Icons.SCHEDULE),
                ft.Divider(height=1, color=theme.COL_BORDER_SUBTLE),
                ft.TextButton(
                    content=ft.Row([ft.Icon(ft.Icons.EDIT, size=15, color=theme.COL_TEXT_MUTED),
                                    ft.Text("深色时段设置…", size=13,
                                            color=theme.COL_TEXT_SECONDARY)],
                                   spacing=8, tight=True),
                    on_click=lambda _e: (page.pop_dialog(), _open_period_dialog())),
            ], spacing=2, tight=True)))

    def _apply_scheme_change(scheme: str):
        """定时轮询触发的换装: 不改写 theme_mode (保持 scheduled), 只切当前方案。"""
        theme.set_scheme(scheme)
        _apply_page_theme()
        st["theme_epoch"] += 1
        if st.get("view", "home") == "home":
            _rebuild_home()
        else:
            # 编辑/头像页停留时也就地换装 (拷问定稿 2026-09-05, 与主页行为一致;
            # 原惰性文案"重新进入编辑页时应用"同样是不刷新病灶的一部分)
            _redress_nonhome()
            set_status("主题已按定时切换, 新配色已应用")
        page.update()

    def _theme_poll_loop():
        while True:
            time.sleep(60)
            try:
                tgt = _target_scheme(load_settings())
            except Exception:  # noqa: BLE001, S112 - 设置读取兜底, 下轮重试
                continue
            if tgt != theme.get_scheme():
                page.run_thread(lambda t=tgt: _apply_scheme_change(t))

    # ==================== 动效挂接助手 (tokens.md §7, rules §4.6) ====================
    # ==================== 动效 (tokens.md §7, rules §4.6) ====================
    # 降级留档 (v2.3.1 批次③): view-in/group-in/panel-in/换装淡入的 opacity+offset
    # 两段动画在 flet 0.86.5 实机反复破坏布局 (内容区空白/控件叠错位), 按
    # rules §4.6 "实机异常就地降级为即时切换" 全部退化为即时切换; 保留动效 =
    # 在线点呼吸 (纯 opacity) / 火箭抖动 (纯 rotate, 有限 2 次) / chip 勾选弹跳
    # (纯 scale, 有限 1 次) / 下拉引擎弹出过渡。offset 位移动画待 flet 升级再试
    # (按钮 hover 上移/卡片 hover 右移批次④同批降级)。

    # ==================== 主页控件统一构建 (v2.3.0 换装重建入口) ====================
    def _rebuild_home():
        """创建/重建全部主页可见控件。所有取色在构建时读 theme.* — 重建即新装。
        主页回归四件套 (v2.3.1 二轮): 头像/昵称 24/状态胶囊/启动钮 110 —
        直连下拉与练枪按钮已移出卡片 (练枪入标题栏, 直连改 ServerPanel 悬停面板)。
        状态回填: refresh_launcher() (昵称/头像/按钮态) + _refresh_server() (在线状态)。"""
        nonlocal avatar, nick_label, unlocated_hint, home_err, hint_box
        nonlocal server_monitor, server_panel, launch_btn
        nonlocal home_win_controls, launcher_head, launcher_view
        avatar = ui.avatar("汤")
        avatar.on_click = lambda e: enter_avatar()   # enter_avatar 定义在下方, 延迟绑定
        avatar.tooltip = "修改头像"
        nick_label = ui.nickname("未定位", size=24)
        unlocated_hint = ft.Text("⚠ rev.ini 未定位, 点配置指定目录", size=12,
                                 color=theme.COL_TEXT_DIM)
        home_err = ft.Text("", size=12, color=theme.COL_ERR)
        # 提示行动态容器: controls 增删占位 (visible=False 仍占布局, Flet 0.86.5 实测)
        hint_box = ft.Column([], spacing=0, tight=True)
        server_monitor = ui.ServerMonitor(
            label="离线", count="", status="offline",
            on_hover_change=lambda h: _sp_show() if h else _sp_hide())
        server_panel = ui.ServerPanel(on_enter=_enter_server)
        server_panel.on_hover = lambda e: (_sp_show() if _is_hovered(e) else _sp_hide())
        launch_btn = ui.LaunchButton(on_click=on_launch_click, tooltip="启动游戏")
        # 内容区底 = bg-main + home-wash 品牌氛围垫层 (radial 椭圆极淡品牌蓝,
        # 非发光 — Flutter gradient 绘制在 bgcolor 之上, 同容器叠加即 HTML
        # `radial-gradient(...), var(--bg-main)` 语义, tokens.md §1.7)
        home_body = ft.Container(
            content=ft.Column([
                avatar,
                gap(24),
                nick_label,
                gap(14),
                server_monitor,
                gap(24),
                launch_btn,
                # 错误/引导提示 (仅出错时占位, 常驻就绪提示已删 — design-system.md)
                hint_box,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            bgcolor=theme.COL_BG_MAIN,
            gradient=ft.RadialGradient(
                colors=[theme.COL_HOME_WASH, ft.Colors.TRANSPARENT],
                stops=[0.0, 0.7],
                center=ft.Alignment(0, -0.28),   # HTML: ellipse at 50% 36%
                radius=0.75,
            ),
            padding=ft.padding.Padding(top=24, left=36, right=36, bottom=48),
        )
        launcher_view = ft.Stack([
            home_body,
            # ServerPanel 悬停面板: 覆盖层锚定状态胶囊下方 (不占布局),
            # w264 水平居中 (design-system.md #34)
            ft.Container(content=server_panel,
                         left=(CARD_W - 264) / 2, top=SERVER_PANEL_TOP),
        ], expand=True, fit=ft.StackFit.EXPAND)   # 非定位子控件铺满 (home_body)
        home_win_controls = ft.Row([
            # 练枪入标题栏 (v2.3.1 二轮): 准星钮 = on_launch_click(practice=True)
            # (lucide 无枪图标, crosshair 语义; flet 无 CROSSHAIR, GPS_FIXED 最近似)
            ui.win_btn(ft.Icons.GPS_FIXED, "练枪启动",
                       on_click=lambda e: on_launch_click(e, practice=True)),
            _theme_btn(),
            ui.win_btn(ft.Icons.SETTINGS, "配置", on_click=lambda e: enter_editor(e)),
            ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
            ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
        ], spacing=6)
        launcher_head = ft.Row([
            ft.Row([
                ui.version_tag(f"v{APP_VERSION}"),
                # 产品名 15px + nowrap: 5 钮布局防换行 (DESIGN.md 坑位记录)
                ft.Text("汤圆启动器", size=15, weight=ft.FontWeight.W_700,
                        color=theme.COL_TEXT_SECONDARY, no_wrap=True),
            ], spacing=10),
            home_win_controls,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        if title_bar is not None:
            title_bar.content = launcher_head
        if view_switcher is not None:
            view_switcher.content = launcher_view
        if _root is not None:
            _root.bgcolor = theme.COL_BG
        st["home_epoch"] = st["theme_epoch"]   # 主页已同步到当前主题
        if view_switcher is not None:
            # 主题切换重建: 控件已挂 page, 正常回填状态。
            # 首次构建 (view_switcher 未建) 跳过 — set_state/set_status 内部
            # self.update() 会抛 "Control must be added to the page first";
            # 初始状态由启动末尾 show_launcher → refresh_launcher 正常回填。
            refresh_launcher()      # 回填昵称/头像/按钮态 (内部 page.update)
            _refresh_server()

    _rebuild_home()   # 首次构建 (title_bar/view_switcher 尚未创建, 仅装控件)

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
        # 编辑/头像期间发生过主题换装: 回主页先整组重建 (epoch 不一致即换装过)
        if st.get("home_epoch", 0) != st.get("theme_epoch", 0):
            _rebuild_home()
        st["view"] = "home"
        title_bar.content = launcher_head
        view_switcher.content = launcher_view
        refresh_launcher()
        status_bar.visible = False   # 主页 360×510 窗口即卡, 状态栏放不下且无功能价值
        _focus_if_unfocused()   # 仅失焦时拉焦点: frameless 未聚焦窗口首次点击会被窗口管理器吞掉 (2026-08)
        # 启动/恢复服务器状态轮询: 立即刷一次 + 后台 30s 周期 (仅主页期间)
        server_epoch["n"] += 1
        _refresh_server()
        if not getattr(_server_poll_loop, "_started", False):
            _server_poll_loop._started = True
            threading.Thread(target=_server_poll_loop, daemon=True).start()
        page.update()

    def _rebuild_editor_surfaces():
        """主题 epoch 变化后重建编辑页表面 (导航/字段页/工具页/CFG 页/顶栏/状态栏)
        并回填数据。页面构建函数均为工厂 (build_page/build_tools_page/build_cfg_page),
        populate_all() 用 model 回填字段值 — 与首次构建同一条代码路径。"""
        nonlocal nav_content, nav_items, nav_rail, editor_view, editor_head
        nonlocal save_btn, enc_selector, status_msg, status_icon, status_bar, win_controls
        field_rows.clear()   # 旧页控件引用作废, 由 build_field_row 重新登记
        nav_content = []
        nav_items = []
        for i, g in enumerate(FIELD_GROUPS):
            icon = icon_map.get(g.get("icon_key", "wrench"), ft.Icons.BUILD)
            nav_items.append(ft.NavigationRailDestination(
                icon=ft.Icon(icon, color=theme.COL_TEXT_DIM),
                selected_icon=ft.Icon(icon, color=theme.COL_BRAND_SOFT),
                label=ft.Text(g["title"], size=12)))
            if g.get("type") == "cfg":
                # CFG 页带未保存修改时保留现值重建 (reload=False) — 见 build_cfg_page
                nav_content.append(build_cfg_page(reload=not st["cfg_dirty"]))
            elif g.get("type") == "tools":
                nav_content.append(build_tools_page(g))
            else:
                nav_content.append(build_page(g))
        if model is not None:
            populate_all()
        content_area.content = nav_content[nav_index]
        # 换装重建须同步壳层底色: content_area/_root 构造时捕获的是当时的方案色,
        # 不刷新则编辑页在浅色下残留深色背板, 直到回主页才被 _rebuild_home 修正
        # (2026-08-30 审查)
        content_area.bgcolor = theme.COL_BG_MAIN
        if _root is not None:
            _root.bgcolor = theme.COL_BG
        nav_rail = ft.NavigationRail(selected_index=nav_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=96, min_extended_width=96,
            destinations=nav_items, on_change=on_nav_change,
            bgcolor=theme.COL_BG, group_alignment=-1.0,
            indicator_color=theme.COL_BRAND_BG_10,
            indicator_shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL),   # nav-item 4px (Win11 档)
            selected_label_text_style=ft.TextStyle(color=theme.COL_BRAND_SOFT, size=12,
                                                   weight=ft.FontWeight.W_600),
            unselected_label_text_style=ft.TextStyle(color=theme.COL_TEXT_DIM, size=12))
        editor_view = ft.Row([nav_rail, ft.VerticalDivider(width=1), content_area],
                             expand=True)
        enc_selector = ui.enc_group([("gbk", "ANSI"), ("utf-8", "UTF-8")],
                                    st.get("enc", "gbk"),
                                    on_change=lambda v: _on_enc_change(v))
        status_msg = ft.Text("", size=12, color=theme.COL_ERR)
        status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=theme.COL_OK)
        save_btn = ft.FilledButton("保存", icon=ft.Icons.SAVE, on_click=on_save, height=34,
            style=ft.ButtonStyle(bgcolor=theme.COL_BRAND, color=ft.Colors.WHITE,
                                 shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL)))
        # 保存语义随当前页切换 (与 on_nav_change._switch 同规则): 换装重建时
        # nav_index 可能停在 CFG 页 — 恒接 on_save 会把 CFG 修改静默丢掉、
        # 反而保存一份 rev.ini (2026-08-30 审查)
        save_btn.on_click = _save_cfg if nav_index == CFG_NAV_INDEX else on_save
        # 窗口控制随换装重建 (主题按钮图标 月亮/太阳 随当前方案, design-system #4/#36)
        win_controls = ft.Row([
            _theme_btn(),
            ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
            ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
        ], spacing=6)
        editor_head = ft.Row([
            ft.Row([
                _bar_btn("返回", ft.Icons.ARROW_BACK, on_back_to_launcher),
                ft.Container(width=1, height=26, bgcolor=theme.COL_BORDER_SUBTLE),
                _bar_btn("打开 cfg 文件夹", ft.Icons.FOLDER_OPEN, on_open_cfg),
                _bar_btn("指定目录", ft.Icons.FOLDER, on_pick_dir),
                _bar_btn("打开文件", ft.Icons.FILE_OPEN, on_open_file),
                ft.Container(width=1, height=26, bgcolor=theme.COL_BORDER_SUBTLE),
                save_btn,
            ], spacing=10),
            win_controls,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        status_bar = ui.status_bar(enc_selector, status_msg, status_icon)
        # 必须经 holder.content 换入 _root: 仅重绑 status_bar 变量不会替换
        # Column 已捕获的旧对象, 编辑页会整体丢失状态栏/编码切换/状态反馈
        # (2026-09-05 审查 P1)
        status_bar_holder.content = status_bar
        st["editor_epoch"] = st["theme_epoch"]

    def show_editor():
        # 主题换装发生在编辑页之外 (主页菜单/定时): epoch 不一致时先重建编辑页表面
        if st.get("editor_epoch", 0) != st.get("theme_epoch", 0):
            _rebuild_editor_surfaces()
        st["view"] = "editor"
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
        _focus_if_unfocused()   # 仅失焦时拉焦点: 否则返回/保存等按钮首次点击被焦点吞掉 (2026-08)
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

    # -- 窗口切换 (2026-08 方案 B 基础上 v2.3.1 改造): 窗口一次到位,
    # 内容即时切换 (v2.3.1: 入场动画按 rules §4.6 降级, 见动效降级留档) --
    # 逐帧窗口 resize 每帧一次 Python→Flutter 往返, 无论怎么优化都有限;
    # 窗口一次 update 到位 + body 内容入场动效。
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
    # 主页窗口控制 (练枪/主题/配置/─/×) 与 launcher_head 已移入 _rebuild_home()
    # 统一创建 (v2.3.0 主题换装重建); 编辑页 win_controls 加主题按钮
    # (v2.3.1: design-system #9/#36 — 主页+编辑页放, 修改头像页不放, 裁剪中换装丢进度)。
    win_controls = ft.Row([
        _theme_btn(),
        ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
        ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
    ], spacing=6)
    # 修改头像页窗口控制 (无主题按钮 — design-system #9 何时不用)
    # 已移入 _rebuild_avatar_surfaces() 统一创建 (三轮: 换装后进头像页配色跟随)

    # -- 编辑页顶栏按钮 (design-system.md #10 BarButton, HTML .btn-bar):
    # 低调灰底细边框 34px; 保存为 primary 变体主色实心 (主操作突出, 2026-08 UI 审查落地)
    def _bar_btn(text, icon, on_click):
        return ft.OutlinedButton(
            text, icon=icon, on_click=on_click, height=34,
            style=ft.ButtonStyle(
                bgcolor={"": theme.COL_BG_GHOST_2, "hovered": theme.COL_BTN_BAR_HOVER},
                color=theme.COL_TEXT_SECONDARY,
                side={"": ft.BorderSide(1, theme.COL_BORDER_SUBTLE),
                      "hovered": ft.BorderSide(1, theme.COL_BORDER_VISIBLE)},
                shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL),  # Win11 控件档
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_500),
            ),
        )

    # 编辑页: ← 返回 + 文件按钮(左) + 保存 + 窗口控制(右)
    # 保存按钮移到顶栏左侧主按钮位 (design-system.md #10: BarButton primary 变体)
    save_btn = ft.FilledButton("保存", icon=ft.Icons.SAVE, on_click=on_save, height=34,
        style=ft.ButtonStyle(bgcolor=theme.COL_BRAND, color=ft.Colors.WHITE,
                             shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL)))
    editor_head = ft.Row([
        ft.Row([
            _bar_btn("返回", ft.Icons.ARROW_BACK, on_back_to_launcher),
            ft.Container(width=1, height=26, bgcolor=theme.COL_BORDER_SUBTLE),
            _bar_btn("打开 cfg 文件夹", ft.Icons.FOLDER_OPEN, on_open_cfg),
            _bar_btn("指定目录", ft.Icons.FOLDER, on_pick_dir),
            _bar_btn("打开文件", ft.Icons.FILE_OPEN, on_open_file),
            ft.Container(width=1, height=26, bgcolor=theme.COL_BORDER_SUBTLE),
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
        bgcolor=theme.COL_BG, group_alignment=-1.0,   # 显式最顶: 消除剩余顶部 padding (2026-08)
        # 选中态 = 半透明品牌底 (10%) + 图标/文字变品牌柔色 (design-system #11,
        # HTML 激活项 bg 10% + 左 3px 指示条; 指示条 NavigationRail 无法表达, 用
        # 半透明 indicator 圆角 4px 近似——实心 indicator 会盖住图标 (用户反馈 2026-08),
        # 10% 半透明只提亮背景不遮图标)
        indicator_color=theme.COL_BRAND_BG_10,
        indicator_shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CTRL),   # nav-item 4px (Win11 档)
        selected_label_text_style=ft.TextStyle(color=theme.COL_BRAND_SOFT, size=12, weight=ft.FontWeight.W_600),
        unselected_label_text_style=ft.TextStyle(color=theme.COL_TEXT_DIM, size=12))

    # -- 编辑页视图 (导航栏 + 字段区) --
    editor_view = ft.Row([
        nav_rail,
        ft.VerticalDivider(width=1),
        content_area,
    ], expand=True)

    # -- 状态栏 (仅图标 + 编码切换; 常驻文字/时间戳已删 — design-system.md #26)
    # 组件库实现 (rules.md §1: 禁止页面内联伪组件, deep-review 5轮 MEDIUM-5)
    status_bar = ui.status_bar(enc_selector, status_msg, status_icon)
    # holder 是状态栏进 _root 的固定入口: 换装重建 (_rebuild_editor_surfaces)
    # 只换 holder.content, 与 title_bar.content 换装同模式 (2026-09-05 审查 P1)
    status_bar_holder = ft.Container(content=status_bar)

    # -- 视图容器 (原 AnimatedSwitcher 改普通容器; 旧 SCALE 0.9 残留坑见 DESIGN.md) --
    view_switcher = ft.Container(content=launcher_view, expand=True)
    body = ft.Container(content=view_switcher, expand=True)

    # ==================== 修改头像 (2026-08-23 新增) ====================
    # 选图状态: 当前原图 bytes (保存时 PIL 裁剪用); 未选图时 None
    avatar_picked = {"bytes": None}

    # 预览节流状态 (2026-08-23 用户实测: 拖动裁剪框非常卡 — 根因是每帧
    # 重新解码整张原图 + PNG 编码 + 整页 update; 优化: 原图只解码一次 +
    # 150ms 节流 + 停顿后防抖补最后一帧)
    preview_state = {"last": 0.0, "img": None, "pending": None, "timer": None}

    def _render_preview(box):
        """box → 96×96 圆形预览 (解码缓存复用, 拖动帧只 crop+resize)"""
        data = avatar_picked["bytes"]
        if data is None:
            return
        try:
            img = preview_state["img"]
            if img is None:
                img = PILImage.open(io.BytesIO(data))
                img.load()
                preview_state["img"] = img
            img = img.crop(box)
            img = img.resize((S_PREVIEW_AVATAR, S_PREVIEW_AVATAR), PILImage.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            avatar_preview.content = ft.Image(
                src=b64,   # 裸 base64 (flet Image.src 支持; data URI 前缀实测不可靠)
                width=S_PREVIEW_AVATAR, height=S_PREVIEW_AVATAR,
                fit=ft.BoxFit.COVER, border_radius=S_PREVIEW_AVATAR // 2)
            avatar_preview.update()
        except Exception:  # noqa: BLE001, S110 - 预览裁剪失败静默, 不影响主流程
            pass

    def _flush_preview():
        """防抖到点: 补渲染被节流跳过的最后一帧 (拖动/滚轮停顿后)。"""
        preview_state["timer"] = None
        b = preview_state["pending"]
        preview_state["pending"] = None
        if b is not None:
            preview_state["last"] = time.monotonic()
            _render_preview(b)

    def _preview_from_box(box):
        """裁剪框 box → 预览 (150ms 节流; 拖动中只挪裁剪框不重算预览)"""
        if avatar_picked["bytes"] is None:
            return
        now = time.monotonic()
        if now - preview_state["last"] < 0.15:
            preview_state["pending"] = box
            return
        preview_state["last"] = now
        _render_preview(box)
        if preview_state["timer"]:
            preview_state["timer"].cancel()
        preview_state["timer"] = threading.Timer(
            0.2, lambda: page.run_thread(_flush_preview))
        preview_state["timer"].daemon = True
        preview_state["timer"].start()

    def _read_file_bytes(path: str) -> bytes:
        """同步读文件 (async 回调里经 asyncio.to_thread 调用, 不阻塞事件循环)"""
        with open(path, "rb") as f:
            return f.read()

    def _pick_avatar_image(_=None):
        """选图: ctypes 调 Windows 原生 GetOpenFileNameW (模态对话框)。

        flet 0.86.5 桌面引擎不支持 FilePicker 控件 (实测报 'Unknown control:
        FilePicker'); tkinter 对话框在后台线程创建 Tk 会挂起 (Windows Tk 主循环
        绑定主线程, 实测 askopenfilename 不返回) — 原生 API 最可靠。
        模态对话框期间 flet 事件循环阻塞属预期 (用户只在对话框内操作)。
        """
        import ctypes
        from ctypes import wintypes

        class _OFN(ctypes.Structure):
            _fields_ = [
                ("lStructSize", wintypes.DWORD),
                ("hwndOwner", wintypes.HWND),
                ("hInstance", wintypes.HINSTANCE),
                ("lpstrFilter", wintypes.LPCWSTR),
                ("lpstrCustomFilter", wintypes.LPWSTR),
                ("nMaxCustFilter", wintypes.DWORD),
                ("nFilterIndex", wintypes.DWORD),
                ("lpstrFile", wintypes.LPWSTR),
                ("nMaxFile", wintypes.DWORD),
                ("lpstrFileTitle", wintypes.LPWSTR),
                ("nMaxFileTitle", wintypes.DWORD),
                ("lpstrInitialDir", wintypes.LPCWSTR),
                ("lpstrTitle", wintypes.LPCWSTR),
                ("Flags", wintypes.DWORD),
                ("nFileOffset", wintypes.WORD),
                ("nFileExtension", wintypes.WORD),
                ("lpstrDefExt", wintypes.LPCWSTR),
                ("lCustData", wintypes.LPARAM),
                ("lpfnHook", wintypes.LPVOID),
                ("lpTemplateName", wintypes.LPCWSTR),
                ("pvReserved", wintypes.LPVOID),
                ("dwReserved", wintypes.DWORD),
                ("FlagsEx", wintypes.DWORD),
            ]

        def _win_open_file(title: str, filter_str: str) -> str | None:
            buf = ctypes.create_unicode_buffer(2048)
            ofn = _OFN()
            ofn.lStructSize = ctypes.sizeof(_OFN)
            ofn.lpstrFilter = filter_str
            # ctypes 结构体 c_wchar_p 字段不能直接赋 unicode buffer (实测抛
            # "incompatible types, c_wchar_Array_2048 instance instead of
            # c_wchar_p instance" 导致 flet 错误卡片), 必须 cast 成指针
            ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
            ofn.nMaxFile = 2048
            ofn.lpstrTitle = title
            ofn.Flags = 0x00001000   # OFN_FILEMUSTEXIST
            if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
                return buf.value
            return None

        try:
            path = _win_open_file(
                "选择头像图片",
                "图片文件\0*.jpg;*.jpeg;*.png;*.webp;*.bmp\0所有文件\0*.*\0\0")
            if not path:
                return
            try:
                data = _read_file_bytes(path)
            except OSError as ex:
                msg = f"读取图片失败: {ex}"
                _flash_status(msg, err=True)
                return
            err = avatar_mod.validate_image(data)
            if err:
                _flash_status(err, err=True)
                return
            try:
                img = PILImage.open(io.BytesIO(data))
                w, h = img.size
            except Exception:  # noqa: BLE001
                _flash_status("无法识别的图片格式", err=True)
                return

            avatar_picked["bytes"] = data
            # 换图重置预览缓存 (原图解码缓存失效 + 预览立即刷新)
            preview_state["img"] = None
            preview_state["last"] = 0.0
            # flet Image.src 支持裸 base64 字符串 (空串会渲染 "A valid src value
            # must be specified" 错误块且不消失 — 已用 1×1 透明 PNG 占位修复)
            crop_canvas.set_image(base64.b64encode(data).decode(), w, h)
            page.update()
        except Exception as ex:  # noqa: BLE001 - 兜底提示, 避免 flet 错误卡片
            msg = f"选择图片失败: {ex}"
            _flash_status(msg, err=True)

    def enter_avatar(_=None):
        """主页头像点击: 窗口扩到 784×600 + 切修改头像视图"""
        _animate_window(*WIN_EDIT, on_done=show_avatar)

    def show_avatar():
        server_epoch["n"] = 0   # 停服务器状态轮询 (修改头像期间不刷主页 UI)
        st["view"] = "editor"   # 按非主页处理: 定时换装只打 epoch 标记, 不重建底下的主页
        # 头像页表面构建于旧主题 epoch: 先重建再上屏 (裁剪中复用画布保进度)
        if st.get("avatar_epoch", 0) != st.get("theme_epoch", 0):
            _rebuild_avatar_surfaces()
        title_bar.content = avatar_head
        view_switcher.content = avatar_view
        status_bar.visible = False
        _focus_if_unfocused()   # 仅失焦时拉焦点 (与 show_launcher/show_editor 同规则)
        page.update()

    def on_back_avatar(_=None):
        show_launcher()
        _animate_window(*WIN_HOME)

    def on_avatar_save(_=None):
        d = st["csgo_dir"] or find_csgo_dir() or ""
        if not d:
            _flash_status("未定位游戏目录, 请先在配置页指定", err=True)
            return
        if avatar_picked["bytes"] is None:
            _flash_status("请先选择一张图片", err=True)
            return
        box = crop_canvas.current_box()
        if box is None:
            _flash_status("裁剪区域无效", err=True)
            return
        ok, err = avatar_mod.save_avatar(
            d, avatar_picked["bytes"], box,
            preview_path=os.path.join(SETTINGS_DIR, "avatar_preview.png"))
        if not ok:
            _flash_status(err, err=True)
            return
        _flash_status("头像已保存, 重启游戏生效")
        show_launcher()
        _animate_window(*WIN_HOME)

    def on_avatar_reset(_=None):
        d = st["csgo_dir"] or find_csgo_dir() or ""
        if not d:
            _flash_status("未定位游戏目录, 请先在配置页指定", err=True)
            return
        ok, err = avatar_mod.restore_default_avatar(d)
        if not ok:
            _flash_status(err, err=True)
            return
        # 同步清掉清晰预览版 → 主页回退显示原厂 64×64 (两套逻辑联动)
        try:
            os.remove(os.path.join(SETTINGS_DIR, "avatar_preview.png"))
        except OSError:
            pass
        _flash_status("已恢复默认头像")
        show_launcher()
        _animate_window(*WIN_HOME)

    def _rebuild_avatar_surfaces():
        """创建/重建修改头像页表面 (三轮: 换装后进入头像页配色跟随当前方案)。
        头像页原只在启动时构建一次, theme 换装后进入显示旧配色。
        裁剪状态保护: avatar_picked 有图 (裁剪中) 时复用 crop_canvas/avatar_preview
        实例 — 只重建容器与标题栏, 裁剪框位置与已选图不丢; 无图时画布一并重建。"""
        nonlocal avatar_preview, crop_canvas, avatar_head, avatar_view
        nonlocal avatar_win_controls
        if avatar_picked["bytes"] is None:
            crop_canvas = ui.CropCanvas(on_change=_preview_from_box)
            avatar_preview = ui.preview_avatar()
        avatar_win_controls = ft.Row([
            ui.win_btn(ft.Icons.MINIMIZE, "最小化", on_click=on_minimize),
            ui.win_btn(ft.Icons.CLOSE, "关闭", on_click=on_close_window, variant="close"),
        ], spacing=6)
        # 修改头像页标题栏: 返回 + 标题 (design-system.md 修改头像视图, 无主题按钮)
        avatar_head = ft.Row([
            ft.Row([
                ui.win_btn(ft.Icons.ARROW_BACK, "返回", on_click=on_back_avatar),
                ft.Text("修改头像", size=16, weight=ft.FontWeight.W_700),
            ], spacing=10),
            avatar_win_controls,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 修改头像页主体: 左=裁剪区, 右=预览+操作 (design-system.md 修改头像视图)
        avatar_view = ft.Row([
            ft.Container(
                content=crop_canvas,
                expand=True,
                alignment=ft.alignment.Alignment(0, 0),
                padding=ft.padding.Padding(left=24, top=24, right=24, bottom=24),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("预览", size=11, weight=ft.FontWeight.W_600, color=theme.COL_TEXT_DIM),
                    avatar_preview,
                    ft.Text("拖动裁剪框调整范围\n拖动四角缩放大小", size=11,
                            color=theme.COL_TEXT_DIM, text_align=ft.TextAlign.CENTER),
                    ft.Container(expand=True),
                    ui.btn_av("选择图片", icon=ft.Icons.IMAGE,
                              on_click=_pick_avatar_image),
                    ui.btn_av("恢复默认", icon=ft.Icons.RESTORE,
                              on_click=on_avatar_reset, variant="ghost"),
                    ui.btn_av("取消", on_click=on_back_avatar),
                    ui.btn_av("保存", icon=ft.Icons.SAVE,
                              on_click=on_avatar_save, variant="primary"),
                ], spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=W_AVATAR_SIDE,
                bgcolor=theme.COL_BG,
                border=ft.Border(left=ft.BorderSide(1, theme.COL_BORDER_SUBTLE)),
                padding=ft.padding.Padding(left=16, top=24, right=16, bottom=24),
            ),
        ], expand=True)
        st["avatar_epoch"] = st["theme_epoch"]

    _rebuild_avatar_surfaces()   # 首次构建 (深色启动色)

    _root = ft.Container(
        content=ft.Column([
            title_bar,
            body,
            status_bar_holder,
        ], spacing=0, tight=True),
        bgcolor=theme.COL_BG,
        # 无描边: 描边 #2A2730 在透明窗口左/下边缘渲染成橄榄色
        # (用户截图+PrintWindow 双重证实, 2026-08); 移除后边缘干净。
        # 窗口圆角 (v2.3.1 定稿): 走系统级 DWM (DwmSetWindowAttribute),
        # 本容器保持矩形铺满 — 禁止 Flutter 自绘圆角 (黑边, AGENTS.md 铁律)
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        expand=True,
    )
    page.add(_root)

    # -- 主题定时轮询 (v2.3.0): 每 60s 复核 scheduled 时段, 方案变化即换装 --
    threading.Thread(target=_theme_poll_loop, daemon=True).start()

    # -- Win11 DWM 原生圆角 (tokens.md §3 radius-window, v2.3.1 定稿):
    # frameless 窗口系统级圆角, 无 Flutter 自绘黑边问题 (AGENTS.md 铁律);
    # 失败自动回退矩形并在状态栏留档 --
    def _apply_dwm():
        if not _dwm_round_corners("Tangyuan"):
            page.run_thread(
                lambda: set_status("窗口 DWM 圆角不可用, 已保持矩形边缘", err=True))
    threading.Thread(target=_apply_dwm, daemon=True).start()

    # -- 初始加载: 直接进主页 (rev.ini 定位在主页 lazy 完成) --
    page.update()
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
