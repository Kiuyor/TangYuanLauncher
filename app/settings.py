# -*- coding: utf-8 -*-
"""用户设置持久化:记录用户手动指定的 CS:GO 路径等"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

# 设置文件放在用户配置目录,而非源码目录。
# 原因: Nuitka --onefile 打包后 __file__ 指向临时解压目录,
# 程序退出即被清理,设置会丢失。使用 %APPDATA% 等用户级目录可持久保存。
def _settings_dir() -> str:
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, "RevIniEditor")
    return os.path.join(os.path.expanduser("~"), ".config", "revini-editor")


SETTINGS_DIR = _settings_dir()
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULTS = {
    "user_csgo_dir": "",   # 用户手动指定的 CS:GO 目录
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(DEFAULTS)
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save_settings(data: dict) -> bool:
    """保存设置;成功返回 True,写入失败返回 False(不抛异常)"""
    cur = load_settings()
    # 显式传入空字符串视为清空该键
    for k, v in data.items():
        if v == "" and k in cur:
            cur.pop(k)
        else:
            cur[k] = v
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def get_user_csgo_dir() -> Optional[str]:
    d = load_settings().get("user_csgo_dir", "")
    return d if d and os.path.isdir(d) else None


def set_user_csgo_dir(path: str) -> bool:
    return save_settings({"user_csgo_dir": path})
