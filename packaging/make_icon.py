# -*- coding: utf-8 -*-
"""图标抠图 v3: 保留内圈圆角方块(深蓝底+白色图形), 裁掉方块外的角落蓝色。
判定: dist_inner 远(>60)=白色主体保留; 蓝色像素按 (dist_inner - dist_outer) 符号区分内外。
"""
import math
from PIL import Image

SRC = r"C:\Users\75017\Downloads\IMG_20260805_113851.png"
OUT_ALPHA = r"D:\cs\revini-editor\packaging\assets\icon_alpha.png"
OUT_PREVIEW = r"D:\cs\revini-editor\packaging\assets\icon_preview.png"

im = Image.open(SRC).convert("RGBA")
w, h = im.size
px = im.load()

BG_OUTER = (56, 95, 151)   # 圆角方块外的角落蓝
BG_INNER = (45, 77, 126)   # 圆角方块底蓝

def d2(p, c):
    return math.sqrt(sum((p[i] - c[i]) ** 2 for i in range(3)))

out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
opx = out.load()

stats = {"keep_white": 0, "keep_inner": 0, "drop_outer": 0, "edge": 0}
for y in range(h):
    for x in range(w):
        p = px[x, y]
        di = d2(p, BG_INNER)
        do = d2(p, BG_OUTER)
        if di > 60:
            # 白色主体或其抗锯齿过渡
            a = 255
            stats["keep_white"] += 1
            opx[x, y] = p
            continue
        delta = di - do
        if delta < -8:
            a = 255
            stats["keep_inner"] += 1
            opx[x, y] = p
        elif delta > 8:
            a = 0
            stats["drop_outer"] += 1
        else:
            # 圆角过渡带: 渐变 alpha
            a = int(255 * (delta + 8) / 16)
            f = a / 255.0
            col = tuple(int(BG_INNER[i] * f + BG_OUTER[i] * (1 - f)) for i in range(3))
            opx[x, y] = (col[0], col[1], col[2], a)
            stats["edge"] += 1

print(stats)
total = w * h
for k, v in stats.items():
    print(f"{k}: {v} ({v/total*100:.1f}%)")

out.save(OUT_ALPHA)
print("saved:", OUT_ALPHA)
print("content bbox:", out.getbbox())

# 居中修正: 方块中心 -> 图中心 (用户反馈 2026-08: 图标没在正中间)
# 方块 bbox (7,5,724,742) 中心 (365.5,373.5) vs 图中心 (376,376)
SHIFT = (10, 2)
if SHIFT != (0, 0):
    centered = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    centered.alpha_composite(out, SHIFT)
    out = centered
    out.save(OUT_ALPHA)
    print(f"re-centered with shift {SHIFT}, saved again")

# 预览: 深色底
PAD = 40
pv = Image.new("RGBA", (w + PAD * 2, h + PAD * 2), (0x11, 0x12, 0x16, 255))
pv.alpha_composite(out, (PAD, PAD))
pv.convert("RGB").save(OUT_PREVIEW)
print("saved:", OUT_PREVIEW)

# 棋盘格版
CHECK = 24
pv2 = Image.new("RGB", (w + PAD * 2, h + PAD * 2), (60, 60, 60))
for gy in range((h + PAD * 2) // CHECK + 1):
    for gx in range((w + PAD * 2) // CHECK + 1):
        if (gx + gy) % 2 == 0:
            for yy in range(gy * CHECK, min((gy + 1) * CHECK, h + PAD * 2)):
                for xx in range(gx * CHECK, min((gx + 1) * CHECK, w + PAD * 2)):
                    pv2.putpixel((xx, yy), (110, 110, 110))
pv2.paste(out, (PAD, PAD), out)
pv2.save(r"D:\cs\revini-editor\packaging\assets\icon_preview_checker.png")
print("saved checker")
