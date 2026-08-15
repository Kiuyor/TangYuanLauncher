# 精确测量打包版启动器 RevIniEditor.exe 的启动耗时
# 方法学: 只认"启动后新出现"的 flet.exe 进程的窗口 (排除已运行实例/残留进程)
# 计时口径: t0=进程创建调用 / 新 flet.exe 引擎进程出现 / 引擎窗口可见(IsWindowVisible 翻转 = UI 就绪)
# 干扰: 首次运行或位于新目录时, 杀软(卡巴斯基/360/火绒等)会逐文件扫描 exe+引擎组件
#       (约 150MB, 见 packaging/README_分发版.md), 单次结果波动大 — 应重复多次取 min/中位数。
# 用法: python measure_startup.py [exe路径] [工作目录]   (默认值见下)
import subprocess, time, ctypes, sys
import ctypes.wintypes

EXE = r"D:\re-la\revini-editor\build\nuitka\main.dist\RevIniEditor.exe"
CWD = r"D:\re-la\revini-editor\build\nuitka\main.dist"
if len(sys.argv) >= 2:
    EXE = sys.argv[1]
if len(sys.argv) >= 3:
    CWD = sys.argv[2]

user32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

# 64 位 Windows: 句柄是 64 位指针, ctypes 默认 restype=c_int 会截断 → 所有 API 静默失败/误关句柄
# (deep-review 双 agent 审查 M1)。显式声明 restype/argtypes。
k32.OpenProcess.restype = ctypes.wintypes.HANDLE
k32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
k32.CloseHandle.restype = ctypes.wintypes.BOOL
k32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
k32.TerminateProcess.restype = ctypes.wintypes.BOOL
k32.TerminateProcess.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.UINT]
k32.QueryFullProcessImageNameW.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
                                            ctypes.c_wchar_p, ctypes.POINTER(ctypes.wintypes.DWORD)]
user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]


def proc_list():
    """枚举全部 PID。失败时打印错误并返回空列表 (审查 L3), 避免静默跑满 30s 报\"未见\"。"""
    arr = (ctypes.wintypes.DWORD * 8192)()
    needed = ctypes.wintypes.DWORD()
    if not psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(needed)):
        print("[!] EnumProcesses 失败, 进程列表不可靠")
        return []
    return list(arr[:needed.value // 4])


def proc_name(pid):
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(512)
        sz = ctypes.wintypes.DWORD(512)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz)):
            return buf.value
        return ""
    finally:
        k32.CloseHandle(h)


def all_flet_pids():
    return {pid for pid in proc_list() if proc_name(pid).lower().endswith("flet.exe")}


def cleanup_new_pids(before):
    """强杀本次测量新增的 flet.exe, 防孤儿进程残留。
    无论主进程是否提前退出/崩溃都调用 (审查 L2: 原实现只在窗口出现路径清理)。"""
    for pid in (all_flet_pids() - before):
        h = k32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
        if h:
            k32.TerminateProcess(h, 1)
            k32.CloseHandle(h)


before = all_flet_pids()
print(f"启动前 flet 进程: {before or '无'}")

t0 = time.perf_counter()
p = subprocess.Popen([EXE], cwd=CWD)
t_proc = time.perf_counter()

new_flet_seen = None
t_vis = None
title = ""
t_end = time.perf_counter() + 30
while time.perf_counter() < t_end:
    p.poll()
    if p.returncode is not None and not new_flet_seen:
        print(f"[!] 主进程退出 code={p.returncode} @ {time.perf_counter()-t0:.2f}s")
        break
    now = all_flet_pids()
    newf = now - before
    if newf and new_flet_seen is None:
        new_flet_seen = time.perf_counter() - t0

    # 窗口归属校验 (审查 L4): 用闭包 + 可变容器替代模块级 global (审查 L1);
    # 标题含产品名才认定为目标窗口, 空标题/其它 flet 应用的窗口跳过。
    found = [None]

    def cb(h, _):
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in newf and user32.IsWindowVisible(h):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, buf, 256)
            t = buf.value
            if t and ("Rev.Ini" in t or "汤圆" in t or "CS:GO" in t):
                found[0] = (h, t)
                return False  # 命中目标, 停止枚举
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if found[0]:
        t_vis = time.perf_counter() - t0
        _, title = found[0]
        break
    time.sleep(0.05)

print(f"主进程创建: {t_proc-t0:.2f}s")
print(f"新 flet.exe 引擎出现: {new_flet_seen if new_flet_seen is not None else '未见'}s")
print(f"引擎窗口可见: {t_vis if t_vis is not None else '未见'}s  title={title!r}")

if p.poll() is None:
    try:
        p.terminate()
    except Exception:
        pass
    time.sleep(0.5)
cleanup_new_pids(before)
print("已清理测试进程")
