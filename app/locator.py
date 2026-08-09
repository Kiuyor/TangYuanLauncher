"""CS:GO 安装目录自动定位

实际优先级 (与实现一致, deep-review F4 修正):
1. 启动器 exe 同级 game\\ 子目录 (v2.0.0 内嵌游戏版, 命中立即返回)
2. 注册表卸载信息 (Nosteam CSGO 的 InstallLocation / DisplayIcon 推导)
3. 当前工作目录 / 脚本所在目录
4. 常见安装路径
"""
from __future__ import annotations

import os
import sys

try:
    import winreg
except ImportError:  # 非 Windows 兜底
    winreg = None


def _looks_like_csgo_dir(path: str) -> bool:
    """目录是否像 CS:GO 根目录:必须含 csgo.exe(严格,避免父目录误判)"""
    if not path or not os.path.isdir(path):
        return False
    if os.path.exists(os.path.join(path, "csgo.exe")):
        return True
    # 兼容:含 csgo 子目录 + rev.ini 的安装形态
    return (os.path.isdir(os.path.join(path, "csgo"))
            and os.path.exists(os.path.join(path, "rev.ini")))


def _scan_uninstall(hive, root: str) -> list:
    """扫描卸载注册表,返回 (name, location, icon) 列表"""
    out = []
    if winreg is None:
        return out
    try:
        key = winreg.OpenKey(hive, root)
    except OSError:
        return out
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(key, i)
        except OSError:
            break
        try:
            sk = winreg.OpenKey(hive, f"{root}\\{sub}")
        except OSError:
            i += 1
            continue
        name = loc = icon = ""
        for value_name in ("DisplayName", "InstallLocation", "DisplayIcon"):
            try:
                v, _ = winreg.QueryValueEx(sk, value_name)
                if value_name == "DisplayName":
                    name = str(v)
                elif value_name == "InstallLocation":
                    loc = str(v)
                else:
                    icon = str(v)
            except OSError:
                pass
        out.append((name, loc, icon))
        i += 1
    return out


def _clean_reg_path(path_value: str) -> str:
    """清洗注册表路径值。

    两种常见形态:
    - 带引号: "D:\\cs\\CSGO\\icon.ico",0  → D:\\cs\\CSGO\\icon.ico
    - 不带引号: D:\\cs\\CSGO\\icon.ico,0    → D:\\cs\\CSGO\\icon.ico
    统一剥离外层引号与逗号后的图标索引, 避免残留引号导致目录无效。
    """
    v = path_value.strip()
    if v.startswith('"'):
        end = v.find('"', 1)
        if end > 0:
            v = v[1:end]
    elif "," in v:
        v = v.split(",", 1)[0]
    return v.strip('"').strip()


def _common_dirs() -> list:
    """常见安装路径(不检测 Steam 目录:本工具面向 no-steam 旧版)"""
    return [p for drive in ("C:", "D:", "E:")
            for p in (f"{drive}\\CSGO", f"{drive}\\csgo",
                      f"{drive}\\Games\\CSGO")]


def _exe_sibling_game_dirs() -> list:
    """启动器 exe 同级 game\\ 子目录候选 (v2.0.0 内嵌游戏版)。

    Nuitka 目录版: 安装器把游戏装为 exe 旁的 game\\, 两者平级;
    开发版: __file__ 位于 revini-editor/app/, 向上两级即仓库根, game\\ 若存在同样生效。
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [os.path.join(base, "game")]


def _is_game_subdir(path: str) -> bool:
    """内嵌 game\\ 目录判定: 含 rev.ini / csgo.exe / Loader.exe 任一即视为游戏根目录"""
    if not path or not os.path.isdir(path):
        return False
    return any(os.path.exists(os.path.join(path, name))
               for name in ("rev.ini", "csgo.exe", "Loader.exe"))


def find_csgo_dir() -> str | None:
    """自动定位 CS:GO 安装目录,找不到返回 None。
    注册表访问在权限受限/重定向环境下可能抛异常,整体兜底保证永不崩溃。"""
    try:
        return _find_csgo_dir_impl()
    except OSError:
        # 注册表/文件系统权限问题: 静默降级, 交由常见路径/手动指定
        return None


def _find_csgo_dir_impl() -> str | None:
    candidates = []

    # 1. 注册表卸载信息
    if winreg is not None:
        roots = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for root in roots:
                for name, loc, icon in _scan_uninstall(hive, root):
                    lower = name.lower()
                    if "csgo" not in lower and "nosteam" not in lower:
                        continue
                    if loc:
                        candidates.append(_clean_reg_path(loc))
                    if icon:
                        # DisplayIcon 形如 "D:\cs\CSGO\icon.ico",0 (含图标索引)
                        ico_dir = os.path.dirname(_clean_reg_path(icon))
                        if ico_dir:
                            candidates.append(ico_dir)

    # 2. 启动器 exe 同级 game\\ 子目录 (v2.0.0 内嵌游戏版)
    for g in _exe_sibling_game_dirs():
        if not _is_game_subdir(g):
            continue
        # 强命中 (含 rev.ini 或 csgo.exe): 内嵌游戏版装完即用, 立即返回
        if os.path.exists(os.path.join(g, "rev.ini")) or \
                os.path.exists(os.path.join(g, "csgo.exe")):
            return g
        # 弱命中 (仅 Loader.exe, 部分解压/残留): 不遮蔽注册表里的完整安装
        # (deep-review 7轮 工具链 F5: 原实现任一文件即 return, 弱目录抢走
        # 注册表候选; 弱目录加入候选列表, 由统一验证 _looks_like_csgo_dir
        # 决定是否可用 — 它要求 csgo.exe, 仅 Loader 的目录自然落选)
        candidates.append(g)

    # 3. 当前工作目录 / 脚本位置
    candidates.append(os.getcwd())
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # revini-editor/
    candidates.append(here)
    candidates.append(os.path.dirname(here))

    # 4. 常见安装路径(不含 Steam 目录)
    candidates.extend(_common_dirs())

    # 去重并验证
    seen = set()
    for c in candidates:
        c = c.strip()
        if not c or c in seen:
            continue
        seen.add(c)
        if _looks_like_csgo_dir(c):
            return c
    return None


def locate_rev_ini(csgo_dir: str | None = None) -> str | None:
    """定位 rev.ini,优先级:
    1. 显式传入目录
    2. 用户手动指定的路径(settings.json 持久化)
    3. 自动探测(注册表/常见路径)
    4. 当前目录"""
    # 1. 显式传入
    if csgo_dir and os.path.isfile(os.path.join(csgo_dir, "rev.ini")):
        return os.path.join(csgo_dir, "rev.ini")

    # 2. 用户指定路径(持久化)
    try:
        from .settings import get_user_csgo_dir
        ud = get_user_csgo_dir()
        if ud and os.path.isfile(os.path.join(ud, "rev.ini")):
            return os.path.join(ud, "rev.ini")
    except (ImportError, OSError):
        pass

    # 3. 自动探测
    d = find_csgo_dir()
    if d and os.path.isfile(os.path.join(d, "rev.ini")):
        return os.path.join(d, "rev.ini")

    # 4. 当前目录
    if os.path.isfile(os.path.join(os.getcwd(), "rev.ini")):
        return os.path.join(os.getcwd(), "rev.ini")
    return None


def find_cfg_dir(csgo_dir: str | None) -> str | None:
    """从 CS:GO 根目录推导 cfg 文件夹 ([根目录]\\csgo\\cfg)
    兼容两种形态:
    - 根目录: D:\\CSGO\\csgo\\cfg
    - 已选到 csgo 子目录: D:\\CSGO\\csgo\\cfg (直接拼 cfg)
    返回存在/可推导的 cfg 路径,否则 None"""
    if not csgo_dir:
        return None
    candidates = [
        os.path.join(csgo_dir, "csgo", "cfg"),
        os.path.join(csgo_dir, "cfg"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    # 目录不存在返回 None, 由调用方提示 (deep-review F8:
    # 原实现返回"最可能路径"导致 os.startfile 对不存在路径抛未捕获 OSError)
    return None
