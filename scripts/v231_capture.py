"""v2.3.1 实机验收截图助手 (v2): 窗口挪到 ZCode 未遮挡的屏幕右侧,
全部点击坐标相对窗口矩形计算, 抓图前置顶。
用法: python v231_capture.py <outdir> <theme>
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys
import time

import PIL.ImageGrab

user32 = ctypes.windll.user32


def find_window():
    buf = ctypes.create_unicode_buffer(64)
    found = []
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(h, l):
        n = user32.GetWindowTextW(h, buf, 64)
        if n and buf.value == "Tangyuan":
            found.append(h)
        return True

    user32.EnumWindows(CB(cb), 0)
    return found[0] if found else None


def rect():
    r = wt.RECT()
    user32.GetWindowRect(find_window(), ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def topmost():
    user32.SetWindowPos(find_window(), -1, 0, 0, 0, 0, 0x0001 | 0x0002)


def move_window(x, y):
    user32.SetWindowPos(find_window(), 0, x, y, 0, 0, 0x0001 | 0x0002)
    time.sleep(0.3)


def grab(name, outdir):
    topmost()
    time.sleep(0.7)   # 等置顶重绘/布局尘埃落定
    l, t, r, b = rect()
    img = PIL.ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
    img.save(os.path.join(outdir, name))
    print("saved", name, (l, t, r, b))


def move(x, y, steps=8):
    w = user32.GetSystemMetrics(0)
    hh = user32.GetSystemMetrics(1)
    for i in range(steps + 1):
        user32.mouse_event(0x8000 | 0x0001, x * 65535 // w, y * 65535 // hh, 0, 0)
        time.sleep(0.015)


def click(x, y):
    move(x, y)
    time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.04)
    user32.mouse_event(4, 0, 0, 0, 0)


def main():
    outdir = sys.argv[1]
    theme = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    time.sleep(1.0)

    # 指针驻停屏幕左下: 避免主页截图出现头像悬停 tooltip
    move(30, 1000, steps=14)
    time.sleep(0.4)

    # 挪出 ZCode 遮挡区 (主屏右侧), 编辑页展开 (784 宽) 也留在屏内
    move_window(1150, 80)

    # ---- 主页 (360×510) ----
    grab(f"{theme}-1-home.png", outdir)

    l, t, r, _ = rect()
    click(r - 98, t + 29)          # 配置钮 (右起第 3)
    time.sleep(3.0)                # 窗口展开 784×600 + rev.ini lazy load

    # ---- 编辑页 (784×600): 导航项 x=左+48 ----
    grab(f"{theme}-2-edit-general.png", outdir)
    l, t, _, _ = rect()
    click(l + 48, t + 170)         # 加载器
    grab(f"{theme}-3-edit-loader.png", outdir)
    click(l + 48, t + 234)         # 修复工具
    grab(f"{theme}-4-edit-tools.png", outdir)
    click(l + 48, t + 298)         # CFG 配置
    grab(f"{theme}-5-edit-cfg.png", outdir)

    # ---- 返回主页 → 修改头像 ----
    click(l + 32, t + 28)          # 返回
    time.sleep(2.2)
    l, t, _, _ = rect()
    click(l + 180, t + 127)        # 头像
    time.sleep(2.2)
    grab(f"{theme}-6-avatar.png", outdir)


if __name__ == "__main__":
    main()
