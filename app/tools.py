# -*- coding: utf-8 -*-
"""修复工具:CS:GO 目录内置维护脚本的一键运行入口"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class RepairTool:
    """一个修复脚本的元数据"""

    name: str                 # 显示名
    file: str                 # 脚本文件名(相对 CSGO 目录)
    category: str             # 类别
    desc: str                 # 用途说明
    action: str               # 实际操作说明
    risk: str                 # 风险等级:低/中
    confirm: str              # 运行前确认文案


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
             on_done: Optional[Callable[[bool, str], None]] = None,
             timeout: float = 120.0) -> bool:
    """异步运行修复脚本,不阻塞 UI。

    - 脚本不存在/无法启动: 返回 False(调用方可立即提示)
    - 启动成功: 返回 True,后台线程执行完毕后回调
      on_done(成功与否, 脚本输出摘要)(stdout+stderr, 截断到 4000 字符)
    - 超时(timeout 秒, 默认 120, 由 UI 传入可调): 强制终止进程树后回调失败 —
      subprocess.run 的 timeout 不会杀子进程, 而修复脚本可能修改注册表,
      不能让它在用户不知情下继续执行
    """
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
