# -*- coding: utf-8 -*-
"""修复工具:CS:GO 目录内置维护脚本的一键运行入口"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

# 内置资源目录 (Loader 优化版 / 扩展版物品库)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ASSET_LOADER = "Loader_opt23.exe"
ASSET_ITEMS = "items_730.bin"


@dataclass
class RepairTool:
    """一个修复脚本的元数据"""

    name: str                 # 显示名
    file: str                 # 脚本文件名(相对 CSGO 目录); None = python 内置工具
    category: str             # 类别
    desc: str                 # 用途说明
    action: str               # 实际操作说明
    risk: str                 # 风险等级:低/中
    confirm: str              # 运行前确认文案
    handler: Callable[[str, Callable], None] | None = None  # python 实现(异步, 回调 on_done)


# ==================== 内置工具 (python 实现, 不走 bat) ====================

def _backup_file(csgo_dir: str, relpath: str):
    """备份游戏目录下的文件为 <name>.bak_<时间戳>, 返回 (备份路径, None) 或 (None, 错误)"""
    src = os.path.join(csgo_dir, relpath)
    if not os.path.isfile(src):
        return None, f"未找到 {relpath}"
    bak = f"{src}.bak_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(src, bak)
        return bak, None
    except OSError as e:
        return None, f"备份失败: {e}"


def _clean_reg_leftover(csgo_dir: str, on_done: Callable[[bool, str], None] | None = None):
    """清理 RevEMU 注册表残留: SteamClientDll + pid (只删模拟器写的值)

    保留正版 Steam 的 SteamClientDll64 / Universe / ActiveUser。
    残留来源: 旧版 Loader / 部分启动器无条件写注册表, 游戏读到错误
    steamclient 变体 → 连服 STEAM validation rejected。
    """
    import winreg
    key_path = r"Software\Valve\Steam\ActiveProcess"
    removed = []
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                           winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    except OSError:
        if on_done:
            on_done(True, "ActiveProcess 键不存在,无需清理(注册表干净)")
        return
    try:
        for v in ("SteamClientDll", "pid"):
            try:
                winreg.DeleteValue(k, v)
                removed.append(v)
            except OSError:
                pass  # 值不存在 = 本来就干净
        winreg.CloseKey(k)
    except OSError as e:
        if on_done:
            on_done(False, f"清理失败: {e}")
        return
    if removed:
        msg = (f"已清理: {', '.join(removed)}\n"
               "(正版 Steam 的 SteamClientDll64/Universe/ActiveUser 未动)")
    else:
        msg = "无残留(SteamClientDll/pid 不存在),注册表干净"
    if on_done:
        on_done(True, msg)


def _install_loader(csgo_dir: str, on_done: Callable[[bool, str], None] | None = None):
    """安装优化版 Loader_opt23.exe 到游戏目录(同名先备份, 不覆盖原件)"""
    src = os.path.join(ASSETS_DIR, ASSET_LOADER)
    if not os.path.isfile(src):
        if on_done:
            on_done(False, f"缺少内置资源: assets\\{ASSET_LOADER}(请确认项目完整)")
        return
    target = os.path.join(csgo_dir, ASSET_LOADER)
    if os.path.isfile(target) and os.path.getsize(target) == os.path.getsize(src):
        if on_done:
            on_done(True, "Loader_opt23.exe 已安装(无需重复安装)")
        return
    if os.path.isfile(target):
        _, err = _backup_file(csgo_dir, ASSET_LOADER)
        if err:
            if on_done:
                on_done(False, err)
            return
    try:
        shutil.copy2(src, target)
        if on_done:
            on_done(True, "已安装 Loader_opt23.exe\n"
                          "(原件 Loader.exe/revLoader.exe 未动, 三者可并存)")
    except OSError as e:
        if on_done:
            on_done(False, f"安装失败: {e}")


def _update_items(csgo_dir: str, on_done: Callable[[bool, str], None] | None = None):
    """用扩展版 items_730.bin 覆盖旧版(原名备份, 可还原)。

    扩展版含 1695 个物品 ID(旧版 992): 库存/商店皮肤更全,
    含 AK-47 咆哮等绝版皮肤。服务端无需任何修改。
    """
    src = os.path.join(ASSETS_DIR, ASSET_ITEMS)
    if not os.path.isfile(src):
        if on_done:
            on_done(False, f"缺少内置资源: assets\\{ASSET_ITEMS}(请确认项目完整)")
        return
    target_dir = os.path.join(csgo_dir, "platform")
    target = os.path.join(target_dir, ASSET_ITEMS)
    if not os.path.isdir(target_dir):
        if on_done:
            on_done(False, f"未找到 platform 目录: {target_dir}(不是标准 CS:GO 安装?)")
        return
    cur_sz = os.path.getsize(target) if os.path.isfile(target) else 0
    if cur_sz == os.path.getsize(src):
        if on_done:
            on_done(True, "items_730.bin 已是扩展版(无需更新)")
        return
    if cur_sz:
        _, err = _backup_file(csgo_dir, os.path.join("platform", ASSET_ITEMS))
        if err:
            if on_done:
                on_done(False, err)
            return
    try:
        shutil.copy2(src, target)
        if on_done:
            on_done(True, f"已更新 items_730.bin: {cur_sz} → {os.path.getsize(src)} 字节\n"
                          "(库存皮肤增加, 含咆哮系列; 原名已备份, 重进游戏生效)")
    except OSError as e:
        if on_done:
            on_done(False, f"更新失败: {e}")


REPAIR_TOOLS: List[RepairTool] = [
    RepairTool(
        name="清除武器皮肤缓存",
        file="cleancache.bat",
        category="缓存清理",
        desc="删除武器皮肤 Flash 缓存文件(*.iic)。"
             "解决皮肤显示错乱、贴图异常、库存界面加载异常等问题,"
             "运行后游戏会自动重建缓存。",
        action="删除 csgo/resource/flash/econ/weapons/cached/ 目录下的缓存文件",
        risk="低",
        confirm="将删除武器皮肤缓存文件(游戏会自动重建),是否继续?",
    ),
    RepairTool(
        name="修复 Steam 客户端错误",
        file="Fix-SteamError.bat",
        category="注册表修复",
        desc="重置 SteamClientDll 注册表设置。"
             "修复启动时提示 \"Steam Client DLL 加载失败\"、"
             "Steam 设置异常等错误,并清除无效的 SteamClientDll 项。",
        action="删除 SteamClientDll 注册表项,并重置 HKCU\\Software\\Valve\\Steam 的 ActiveProcess 设置",
        risk="中",
        confirm="将修改当前用户注册表中 Valve\\Steam 的设置(HKCU),用于修复 Steam 错误,是否继续?",
    ),
    RepairTool(
        name="清理 RevEMU 注册表残留",
        file=None,
        category="注册表修复",
        desc="删除模拟器写入的 SteamClientDll/pid 残留。"
             "旧版 Loader 残留会污染注册表,导致连服被拒"
             "(STEAM validation rejected)。"
             "正版 Steam 的键(SteamClientDll64/Universe/ActiveUser)不受影响。",
        action="删除 HKCU\\Software\\Valve\\Steam\\ActiveProcess 下的 SteamClientDll 与 pid",
        risk="低",
        confirm="将删除注册表中的模拟器残留值(不影响正版 Steam),是否继续?",
        handler=_clean_reg_leftover,
    ),
    RepairTool(
        name="安装优化 Loader (免残留)",
        file=None,
        category="Loader",
        desc="安装 Loader_opt23.exe: 与原版行为一致,但游戏退出后自动清理"
             "注册表,防止残留污染。原件 Loader.exe/revLoader.exe 不覆盖,"
             "多个 Loader 可并存。",
        action="复制内置 Loader_opt23.exe 到游戏目录(同名文件先备份)",
        risk="低",
        confirm="将复制优化版 Loader 到游戏目录,是否继续?",
        handler=_install_loader,
    ),
    RepairTool(
        name="更新皮肤库 items_730.bin",
        file=None,
        category="物品库",
        desc="用扩展版物品库(1695 个物品,含 AK-47 咆哮等绝版皮肤)"
             "替换旧版,库存/商店皮肤显示更全。原名自动备份。",
        action="备份并覆盖 platform\\items_730.bin",
        risk="低",
        confirm="将覆盖 platform\\items_730.bin(原名已备份),是否继续?",
        handler=_update_items,
    ),
]


def csgo_dir_from_ini(ini_path: str) -> str:
    """从 rev.ini 路径推导 CSGO 根目录"""
    if ini_path:
        return os.path.dirname(ini_path)
    # 兜底:工具自身所在目录的上级
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(here).upper() == "CSGO":
        return here
    return here



def run_tool(csgo_dir: str, tool: RepairTool,
             on_done: Callable[[bool, str], None] | None = None,
             timeout: float = 120.0) -> bool:
    """异步运行修复工具,不阻塞 UI。

    - handler 工具(python 内置): 直接后台线程执行 handler(csgo_dir, on_done)
    - 脚本工具(bat): 要求脚本存在于 csgo_dir, 执行后回调结果
    - 脚本不存在/无法启动: 返回 False(调用方可立即提示)
    - 启动成功: 返回 True,后台线程执行完毕后回调
      on_done(成功与否, 输出摘要)(stdout+stderr, 截断到 4000 字符)
    - 超时(timeout 秒, 默认 120, 由 UI 传入可调): 强制终止进程树后回调失败 —
      subprocess.run 的 timeout 不会杀子进程, 而修复脚本可能修改注册表,
      不能让它在用户不知情下继续执行
    """
    if tool.handler is not None:
        def _run_handler():
            try:
                tool.handler(csgo_dir, on_done)
            except Exception as e:  # noqa: BLE001 - 兜底: handler 异常也要回调
                if on_done is not None:
                    on_done(False, f"工具执行异常: {e}")
        threading.Thread(target=_run_handler, daemon=True).start()
        return True

    script = os.path.join(csgo_dir, tool.file)
    if not os.path.exists(script):
        return False
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    def _run():
        ok = False
        output = ""
        try:
            proc = subprocess.Popen(
                [script], cwd=csgo_dir, creationflags=flags, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            output = f"无法启动脚本: {e}"
        else:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                _kill_process_tree(proc)
                try:
                    # 杀树后二次收尾: 加 timeout 防 taskkill 失败/残留子进程导致永久挂起 (deep-review R8)
                    stdout, stderr = proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    stdout, stderr = b"", b""
                output = (f"脚本执行超时({timeout:g} 秒),已强制终止。\n"
                          + _merge_output(_to_text(stdout), _to_text(stderr)))
            else:
                ok = proc.returncode == 0
                output = _merge_output(_to_text(stdout), _to_text(stderr))
        finally:
            if on_done is not None:
                on_done(ok, output[:4000])

    threading.Thread(target=_run, daemon=True).start()
    return True


def _to_text(b: Optional[bytes]) -> str:
    """字节输出解码: UTF-8 优先, 坏字节替换(与旧行为一致, GBK 输出不崩溃)"""
    return (b or b"").decode("utf-8", errors="replace")


def _kill_process_tree(proc) -> None:
    """强制终止子进程树。Windows 下 .bat 由 cmd 承载, 子命令需整树杀掉,
    因此用 taskkill /T; 失败时退化为 proc.kill() 兜底 (deep-review R8:
    原实现忽略 taskkill 非 0 返回直接 return, 残留子进程会让二次 communicate 挂起)"""
    if sys.platform == "win32":
        try:
            r = subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, timeout=10)
            if r.returncode == 0:
                return
            # taskkill 失败 (进程已退出/权限不足): 继续走 proc.kill() 兜底
        except (OSError, subprocess.TimeoutExpired):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def _merge_output(stdout: str, stderr: str) -> str:
    """合并 stdout/stderr 为可读文本: 逐行去空去重, 保留出现顺序
    (整块去重会漏掉跨流的重复行, 如 stdout 与 stderr 打印相同内容)"""
    out = []
    seen = set()
    for chunk in (stdout, stderr):
        for line in (chunk or "").splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
    return "\n".join(out)
