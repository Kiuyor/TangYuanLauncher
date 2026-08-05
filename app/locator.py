# -*- coding: utf-8 -*-
"""CS:GO 安装目录自动定位

优先级:
1. 注册表卸载信息 (Nosteam CSGO 的 InstallLocation)
2. 注册表 DisplayIcon 推导
3. 当前工作目录 / 脚本所在目录
4. 常见安装路径
"""
from __future__ import annotations

import os
from typing import Optional

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
    out = []
    for drive in ("C:", "D:", "E:"):
        for p in (f"{drive}\\CSGO", f"{drive}\\csgo",
                  f"{drive}\\Games\\CSGO"):
            out.append(p)
    return out


def find_csgo_dir() -> Optional[str]:
    """自动定位 CS:GO 安装目录,找不到返回 None。
    注册表访问在权限受限/重定向环境下可能抛异常,整体兜底保证永不崩溃。"""
    try:
        return _find_csgo_dir_impl()
    except OSError:
        # 注册表/文件系统权限问题: 静默降级, 交由常见路径/手动指定
        return None


def _find_csgo_dir_impl() -> Optional[str]:
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

    # 2. 当前工作目录 / 脚本位置
    candidates.append(os.getcwd())
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # revini-editor/
    candidates.append(here)
    candidates.append(os.path.dirname(here))

    # 3. 常见安装路径(不含 Steam 目录)
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


def locate_rev_ini(csgo_dir: Optional[str] = None) -> Optional[str]:
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


def find_cfg_dir(csgo_dir: Optional[str]) -> Optional[str]:
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
