#!/usr/bin/env python3
"""内置工具回归验证 (ad-hoc, 非测试套件)

用法: .venv311/Scripts/python.exe scripts/verify_tools.py
覆盖: newloader.exe 安装(不覆盖原件/幂等) / 工具元数据 / 启动优先逻辑 / ruff 基线
"""
import os
import shutil
import subprocess
import sys
import tempfile

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

fails = []


def check(name, cond, detail=""):
    print(f'[{"PASS" if cond else "FAIL"}] {name}' + (f" | {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def main():
    from app.tools import REPAIR_TOOLS, _install_loader, _speedup_startgame

    asset = os.path.join(PROJ, "assets", "Loader_opt23.exe")
    asset_sz = os.path.getsize(asset)

    # --- 模拟游戏目录: 原件 Loader/revLoader 必须保持不动 ---
    tmp = tempfile.mkdtemp()
    orig = b"Y" * 34816
    for fn in ("Loader.exe", "revLoader.exe"):
        with open(os.path.join(tmp, fn), "wb") as f:
            f.write(orig)

    res = []
    _install_loader(tmp, lambda ok, m: res.append((ok, m)))
    check("install ok", res and res[-1][0], str(res[-1] if res else None))
    check("newloader.exe created w/ optimized size",
          os.path.getsize(os.path.join(tmp, "newloader.exe")) == asset_sz)
    with open(os.path.join(tmp, "Loader.exe"), "rb") as f:
        loader_orig = f.read()
    check("Loader.exe untouched", loader_orig == orig)
    with open(os.path.join(tmp, "revLoader.exe"), "rb") as f:
        rev_orig = f.read()
    check("revLoader.exe untouched", rev_orig == orig)
    check("no backup files", not [f for f in os.listdir(tmp) if "bak" in f])

    res.clear()
    _install_loader(tmp, lambda ok, m: res.append((ok, m)))
    check("idempotent", res and res[-1][0] and "无需重复安装" in res[-1][1])
    check("still 3 files", len(os.listdir(tmp)) == 3, str(os.listdir(tmp)))

    # --- 同大小不同内容 → 应覆盖 (旧版大小比较会误判跳过, MD5 修复) ---
    fake = b"Z" * asset_sz
    with open(os.path.join(tmp, "newloader.exe"), "wb") as f:
        f.write(fake)
    res.clear()
    _install_loader(tmp, lambda ok, m: res.append((ok, m)))
    check("same-size diff-content -> replaced",
          res and res[-1][0] and "已安装 newloader.exe" in res[-1][1])
    with open(os.path.join(tmp, "newloader.exe"), "rb") as f:
        cur = f.read()
    with open(asset, "rb") as f:
        want = f.read()
    check("content now optimized", cur == want)

    # --- 启动提速: timeout 10 → 2, CRLF 保留, 备份, 幂等 ---
    bat = os.path.join(tmp, "startgame.bat")
    crlf_content = b"@ECHO OFF\r\ntimeout /t 10 /nobreak\r\nstart Loader.exe\r\n"
    with open(bat, "wb") as f:
        f.write(crlf_content)
    res.clear()
    _speedup_startgame(tmp, lambda ok, m: res.append((ok, m)))
    check("speedup ok (10s -> 2s)", res and res[-1][0] and "2s" in res[-1][1])
    with open(bat, "rb") as f:
        new_bat = f.read()
    check("timeout now 2", b"timeout /t 2" in new_bat)
    check("CRLF preserved", new_bat.count(b"\r\n") == 3 and b"\r\ntimeout" in new_bat)
    check("other lines intact", b"start Loader.exe" in new_bat)
    baks = [f for f in os.listdir(tmp) if "startgame.bat.bak" in f]
    check("bat backup created", len(baks) == 1, str(baks))
    res.clear()
    _speedup_startgame(tmp, lambda ok, m: res.append((ok, m)))
    check("speedup idempotent", res and res[-1][0] and "已是快速启动" in res[-1][1])
    with open(bat, "wb") as f:
        f.write(b"@ECHO OFF\r\nstart Loader.exe\r\n")
    res.clear()
    _speedup_startgame(tmp, lambda ok, m: res.append((ok, m)))
    check("no timeout -> already fast", res and res[-1][0] and "无 timeout" in res[-1][1])
    shutil.rmtree(tmp)

    # --- 工具元数据 ---
    t = next((t for t in REPAIR_TOOLS if t.name.startswith("安装优化")), None)
    check("loader tool found", t is not None)
    check("risk=低", t is not None and t.risk == "低")
    check("desc mentions newloader.exe", "newloader.exe" in t.desc)

    # --- 启动优先逻辑 (闭包不易单测, 静态确认 + 导入) ---
    with open(os.path.join(PROJ, "flet_app", "main.py"), encoding="utf-8") as f:
        src = f.read()
    check("launch prefers newloader.exe",
          'os.path.isfile(os.path.join(d, "newloader.exe"))' in src)
    check("Popen uses loader_exe", "subprocess.Popen([loader_exe]" in src)

    import flet_app.main  # noqa: F401 - 模块级导入即冒烟
    check("flet_app.main imports", True)

    # --- ruff: 全库 0 错误 (质量门, 2026-08 审计清零后由"基线 31"收紧) ---
    r = subprocess.run([sys.executable, "-m", "ruff", "check",
                        "app", "flet_app", "main.py", "scripts"],
                       capture_output=True, text=True, cwd=PROJ, check=False)
    out = r.stdout + r.stderr
    check("ruff 全库 0 错误", r.returncode == 0 and "All checks passed" in out,
          out.strip().splitlines()[-1] if out.strip() else "EMPTY")

    print()
    print("FAILED:" if fails else "ALL PASSED",
          fails if fails else "(ad-hoc verification, not a suite)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
