"""头像处理模块 — 修改头像功能的数据层(纯函数 + 文件操作, 无 UI 依赖)。

数据契约 (2026-08-23 实测 D:/re-la/CSGO/platform/):
- avatar.dat  = 64×64 24 位 BMP (游戏内头像, Steam medium 尺寸)
- avatar1.dat = 64×64 PNG   (同尺寸备选)
两者同源同尺寸, 改头像须同时写两个文件, 否则游戏内不同渲染路径可能读旧图。

流程: 玩家选图 → UI 裁剪框(1:1 方形) → 反推原图像素 box → crop + 缩放 64×64
      → 转 BMP 写 avatar.dat + 转 PNG 写 avatar1.dat; 替换前 .bak 备份(仅保留最近一个)。
透明区域填黑(24 位 BMP 无 alpha 通道); 重启游戏生效(游戏运行中不会覆盖, 已实测)。
"""
from __future__ import annotations

import io
import os
import shutil
import sys

from PIL import Image

AVATAR_SIZE = 64          # 头像边长 (avatar.dat/avatar1.dat 均为 64×64)
PREVIEW_SIZE = 256        # 启动器展示用清晰头像边长 (主页 100px 显示, 2.5x 超采样)
MAX_FILE_SIZE = 20 * 1024 * 1024   # 20MB 上限 (用户决策)
MAX_DIM = 8000            # 单边最大像素 (用户决策)

# 平台目录相对游戏目录
_PLATFORM = os.path.join("platform")


def validate_image(data: bytes) -> str | None:
    """校验图片字节; 返回错误消息(中文)或 None 表示合法。

    限制: 大小 ≤20MB; 能解码; 单边 ≤8000px。防超大图卡死/内存暴涨。
    """
    if not data:
        return "图片为空"
    if len(data) > MAX_FILE_SIZE:
        return "图片超过 20MB, 请换一张"
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:  # noqa: BLE001 - PIL 解不开统一按非法格式处理
        return "无法识别的图片格式"
    if img.width > MAX_DIM or img.height > MAX_DIM:
        return f"图片尺寸超过 {MAX_DIM}×{MAX_DIM}"
    return None


def _flatten_alpha(img: Image.Image) -> Image.Image:
    """透明区域填黑。24 位 BMP 无 alpha 通道, 透明像素会变垃圾色,
    故先合成到纯黑底(用户决策: 透明填黑)。"""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[3])   # alpha 通道作 mask
        return bg
    return img.convert("RGB")


def _crop_resize(data: bytes, box: tuple[int, int, int, int],
                 size: int = AVATAR_SIZE) -> Image.Image:
    """解码 → 裁剪 box → 缩放 size×size。box=(left, top, right, bottom) 原图像素坐标。"""
    img = Image.open(io.BytesIO(data))
    img.load()
    img = img.crop(box)
    img = img.resize((size, size), Image.LANCZOS)
    return _flatten_alpha(img)


def crop_to_bmp(data: bytes, box: tuple[int, int, int, int]) -> bytes:
    """裁剪并输出 64×64 24 位 BMP 字节 (写 avatar.dat)。"""
    img = _crop_resize(data, box)
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    return buf.getvalue()


def crop_to_png(data: bytes, box: tuple[int, int, int, int]) -> bytes:
    """裁剪并输出 64×64 PNG 字节 (写 avatar1.dat)。"""
    img = _crop_resize(data, box)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def crop_to_preview(data: bytes, box: tuple[int, int, int, int]) -> bytes:
    """裁剪并输出 PREVIEW_SIZE×PREVIEW_SIZE PNG (启动器展示用清晰头像)。

    两套逻辑 (2026-08-23 用户决策): 游戏头像固定 64×64 (avatar.dat/
    avatar1.dat), 启动器主页 100px 展示读 PREVIEW_SIZE 清晰版, 不糊。
    """
    img = _crop_resize(data, box, PREVIEW_SIZE)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _backup(path: str) -> str | None:
    """备份单个文件为 <path>.bak (覆盖旧 .bak, 只保留最近一个备份 — 用户决策)。

    源不存在则跳过(返回 None), 首次改头像时 avatar1.dat 可能缺失属正常。
    """
    if not os.path.isfile(path):
        return None
    bak = path + ".bak"
    try:
        shutil.copy2(path, bak)
        return bak
    except OSError:
        return None


def _atomic_write(path: str, data: bytes) -> bool:
    """原子写: tmp + os.replace, 避免写一半崩溃留坏文件。"""
    tmp = path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False


def save_avatar(csgo_dir: str, data: bytes, box: tuple[int, int, int, int],
                preview_path: str | None = None) -> tuple[bool, str]:
    """写头像: 备份 → 写 avatar.dat(BMP) + avatar1.dat(PNG) + 可选清晰预览版。

    preview_path 非空时另写 PREVIEW_SIZE 清晰版 PNG (启动器展示用, 存
    用户数据目录); 预览版写失败不阻断主流程 (主页自动回退 64×64 版)。
    返回 (ok, err_msg)。
    """
    platform = os.path.join(csgo_dir, _PLATFORM)
    dat = os.path.join(platform, "avatar.dat")
    dat1 = os.path.join(platform, "avatar1.dat")
    if not os.path.isdir(platform):
        return False, "未找到游戏 platform 目录"
    try:
        bmp = crop_to_bmp(data, box)
        png = crop_to_png(data, box)
    except Exception as e:  # noqa: BLE001 - 裁剪异常统一报错
        return False, f"图片处理失败: {e}"
    _backup(dat)
    _backup(dat1)
    if not _atomic_write(dat, bmp):
        return False, "写入 avatar.dat 失败"
    if not _atomic_write(dat1, png):
        return False, "写入 avatar1.dat 失败"
    if preview_path:
        try:
            pv = crop_to_preview(data, box)
            pdir = os.path.dirname(preview_path)
            if pdir and not os.path.isdir(pdir):
                os.makedirs(pdir, exist_ok=True)
            _atomic_write(preview_path, pv)
        except Exception:  # noqa: BLE001, S110 - 预览版失败不阻断 (主页回退 64 版)
            pass
    return True, ""


def _asset_dir() -> str:
    """assets/ 目录: 打包版 = exe 同级 assets/, 开发版 = 仓库根 assets/。"""
    if getattr(sys, "frozen", False) or getattr(sys, "__compiled__", False):
        return os.path.join(os.path.dirname(sys.executable), "assets")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def restore_default_avatar(csgo_dir: str) -> tuple[bool, str]:
    """从 assets/ 恢复出厂默认头像(default_avatar.dat / default_avatar1.dat)。

    规则(rules.md §4.6): 出厂头像必须随包备份到 assets/, 禁止依赖目标机器残留。
    """
    assets = _asset_dir()
    platform = os.path.join(csgo_dir, _PLATFORM)
    src_dat = os.path.join(assets, "default_avatar.dat")
    src_dat1 = os.path.join(assets, "default_avatar1.dat")
    if not (os.path.isfile(src_dat) and os.path.isfile(src_dat1)):
        return False, "出厂默认头像缺失, 无法恢复"
    if not os.path.isdir(platform):
        return False, "未找到游戏 platform 目录"
    _backup(os.path.join(platform, "avatar.dat"))
    _backup(os.path.join(platform, "avatar1.dat"))
    try:
        shutil.copy2(src_dat, os.path.join(platform, "avatar.dat"))
        shutil.copy2(src_dat1, os.path.join(platform, "avatar1.dat"))
    except OSError as e:
        return False, f"恢复默认头像失败: {e}"
    return True, ""
