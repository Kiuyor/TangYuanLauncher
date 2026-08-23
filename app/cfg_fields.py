"""CFG 表单化: 字段定义 + 解析/写回引擎 (CFG 配置页, 2026-08-22 定稿)

范围: 仅 s0up 预设 (auto.cfg 主文件 + crosshair.cfg 准星文件)。
- auto.cfg      值不带引号, 行尾注释保留 (预设排版: 命令名后多空格对齐值列)
- crosshair.cfg 值带引号 ("0"), 写回保留引号
- 写回 = 行内值替换, 保留缩进/分隔空格/行尾注释; 缺失命令追加到组标题后
- 保存前 .bak 备份由调用方负责 (main.py 同 rev.ini 模式)
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass

# s0up 预设随包文件清单 (CFG 页一键植入 / 打包链共用; 排除说明文档 启动项.txt)
S0UP_FILES = [
    "auto.cfg", "bind_default.cfg", "cals.cfg", "chatwheel.cfg",
    "crosshair.cfg", "crosshair_throw.cfg", "demo.cfg", "ffmpeg.cfg",
    "practice.cfg", "practiceExt.nut", "solo.cfg", "stream.cfg", "stream2.cfg",
]

# ---------------- 字段定义 ----------------

@dataclass(frozen=True)
class CfgField:
    key: str                  # cfg 行首命令名
    label: str                # 界面中文名
    kind: str                 # float | int | enum
    min_v: float | None = None
    max_v: float | None = None
    default: str | float | int | None = None
    options: tuple = ()       # enum: (值, 中文标签) 序列
    file: str = "auto.cfg"    # 目标文件 (准星组 -> crosshair.cfg)
    unit: str = ""            # 后缀说明 (如 "越小越亮")
    scale: float = 1.0        # 显示值 ↔ 文件值换算 (显示=文件值/scale; 写回=显示值*scale) — 准星透明度 255→100%

    def validate(self, raw: str) -> tuple[bool, str]:
        """范围校验: 返回 (是否合法, 错误信息)。空串视为未填(不校验)。"""
        if raw == "":
            return True, ""
        if self.kind == "enum":
            ok = raw in [str(v) for v, _ in self.options]
            return (ok, f"仅支持 {'/'.join(str(v) for v, _ in self.options)}") if not ok else (True, "")
        try:
            v = float(raw) if self.kind == "float" else int(raw)
        except ValueError:
            return False, "需为数字"
        if self.kind == "int" and raw.strip() != str(int(raw)):
            return False, "需为整数"
        if not math.isfinite(v):
            # NaN/±inf: 与 min/max 比较恒 False 会绕过范围检查, 必须显式拦截
            # (deep-review 12轮: float("nan") 不抛 ValueError, 会写 sensitivity nan 进 cfg)
            return False, "需为数字"
        if self.min_v is not None and v < self.min_v:
            return False, f"最小 {self.min_v}"
        if self.max_v is not None and v > self.max_v:
            return False, f"最大 {self.max_v}"
        return True, ""


# ---- 鼠标组 (auto.cfg) ----
MOUSE_FIELDS = [
    CfgField("sensitivity", "鼠标灵敏度", "float", 0.01, 10, 2,
             unit="DPI × 灵敏度 = eDPI"),
    CfgField("zoom_sensitivity_ratio_mouse", "开镜灵敏度", "float", 0.1, 2, 1),
    CfgField("m_rawinput", "原始鼠标输入", "enum", None, None, 1,
             options=(("0", "关闭"), ("1", "开启"))),
    CfgField("m_customaccel", "鼠标加速", "enum", None, None, 0,
             options=(("0", "关闭"), ("3", "开启"))),
    CfgField("m_customaccel_exponent", "鼠标加速值", "float", 1, 2, 1.05),
    CfgField("m_yaw", "X 轴速度", "float", 0.016, 0.025, 0.022),
]

# ---- 准星组 (crosshair.cfg, 值带引号) ----
CROSSHAIR_FIELDS = [
    CfgField("cl_crosshaircolor_r", "准星颜色 R", "int", 0, 255, 0, file="crosshair.cfg"),
    CfgField("cl_crosshaircolor_g", "准星颜色 G", "int", 0, 255, 255, file="crosshair.cfg"),
    CfgField("cl_crosshaircolor_b", "准星颜色 B", "int", 0, 255, 145, file="crosshair.cfg"),
    CfgField("cl_crosshairstyle", "准星样式", "enum", None, None, 4,
             options=(("0", "经典"), ("1", "经典静态"), ("2", "经典动态"),
                      ("3", "动态混合"), ("4", "线"), ("5", "十字")),
             file="crosshair.cfg"),
    CfgField("cl_crosshairsize", "准星大小", "int", -5, 20, 1, file="crosshair.cfg"),
    CfgField("cl_crosshairthickness", "准星粗细", "int", 0, 10, 0, file="crosshair.cfg"),
    CfgField("cl_crosshairgap", "准星间隙", "int", -10, 10, -4, file="crosshair.cfg"),
    CfgField("cl_crosshairdot", "中心点", "enum", None, None, 0,
             options=(("0", "关闭"), ("1", "开启")), file="crosshair.cfg"),
    # 透明度 0-100% (文件值 0-255, scale=2.55 换算 — 玩家看不懂 255, 2026-08-23 优化)
    CfgField("cl_crosshairalpha", "准星透明度", "int", 0, 100, 100,
             unit="100=完全不透明", scale=255 / 100, file="crosshair.cfg"),
]

# ---- 声音组 (auto.cfg) ----
SOUND_FIELDS = [
    CfgField("volume", "主音量", "float", 0, 1, 0.6, unit="0.6=100% 0.3=50%"),
    CfgField("voice_scale", "队友语音音量", "float", 0, 1, 1),
    CfgField("snd_menumusic_volume", "主菜单音乐", "float", 0, 1, 0.05),
    CfgField("snd_mute_losefocus", "后台静音", "enum", None, None, 0,
             options=(("0", "后台继续播放"), ("1", "后台静音"))),
]

# ---- 性能组 (auto.cfg) ----
PERF_FIELDS = [
    CfgField("fps_max", "帧数上限", "int", 30, 400, 400),
    CfgField("fps_max_menu", "主界面帧数", "int", 30, 300, 120),
    CfgField("r_dynamic", "动态光", "enum", None, None, 1,
             options=(("1", "开启"), ("0", "关闭(省帧数)")),
             unit="关闭可减少掉帧, 但影响战局"),
    CfgField("mat_monitorgamma", "亮度", "float", 1.6, 2.6, 2.2,
             unit="越小越亮"),
]

GROUPS = [
    ("鼠标", MOUSE_FIELDS, "auto.cfg"),
    ("准星", CROSSHAIR_FIELDS, "crosshair.cfg"),
    ("声音", SOUND_FIELDS, "auto.cfg"),
    ("性能", PERF_FIELDS, "auto.cfg"),
]
FIELD_INDEX = {f.key: f for _, fs, _ in GROUPS for f in fs}


# ---------------- 解析 ----------------

# 行结构: 缩进 + 命令名 + 分隔空白 + 值(可带引号) + 行尾注释(//...)
_LINE_RE = re.compile(r"^(\s*)([a-zA-Z_][a-zA-Z_0-9]*)(\s+)(.*)$")


def parse_cfg(path: str) -> dict[str, tuple[str, str, int]]:
    """解析 cfg 文件: {命令名: (值, 注释段, 行号0基)}。值已去引号;
    注释段 = 值后尾部空格 + // 注释 (写回时原样拼回, 保留排版)。
    newline="" 保留 \r\n (写回不混行尾)。非目标格式行忽略。"""
    out: dict[str, tuple[str, str, int]] = {}
    if not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        m = _LINE_RE.match(line.rstrip("\r\n"))
        if not m:
            continue
        _indent, key, _sep, rest = m.groups()
        if key in ("alias", "exec", "echo", "clear", "host_writeconfig", "unbindall"):
            continue
        # 拆行尾注释, 保留值后尾部空格 (对齐排版)
        ci = rest.find("//")
        if ci >= 0:
            body, comment = rest[:ci], rest[ci:]
        else:
            body, comment = rest, ""
        val = body.strip()
        trail = body[len(body.rstrip()):]  # 值后尾部空格
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1]
        if val == "":
            continue
        out[key] = (val, trail + comment, i)
    return out


# ---------------- 写回 ----------------

# 组名 -> 组标题关键字 (auto.cfg 分节标题, 追加缺失命令的锚点)
_GROUP_TITLE_KEYWORDS = {
    "鼠标": ("鼠标设置",),
    "准星": ("准星",),          # auto.cfg 第 2 节标题含"准星"; crosshair.cfg 无分节走文件尾
    "声音": ("声音设置",),
    "性能": ("基础设置",),       # fps/r_dynamic 在预设"6. 基础设置"节
}
_GROUP_HEAD_RE = re.compile(r"//[═＝=].*\d\.\s*([^═＝=\s]+)")


def _group_head_line(lines: list[str], group_name: str) -> int:
    """定位组标题注释行的下一行 (追加缺失命令的锚点)。
    匹配 auto.cfg 分节标题; 找不到或 crosshair.cfg → 文件尾。"""
    if group_name == "准星":
        return len(lines)  # crosshair.cfg 无分节, 追加到文件尾
    kws = _GROUP_TITLE_KEYWORDS.get(group_name, ())
    if not kws:
        return len(lines)
    for i, line in enumerate(lines):
        m = _GROUP_HEAD_RE.search(line)
        if not m:
            continue
        for kw in kws:
            if kw in m.group(1):
                return i + 1
    return len(lines)


def _fmt_value(field: CfgField, raw: str) -> str:
    """按文件格式格式化值: crosshair.cfg 带引号, auto.cfg 裸值。"""
    if field.file == "crosshair.cfg":
        return f'"{raw}"'
    return raw


def apply_values(cfg_dir: str, updates: dict[str, str]) -> dict[str, str]:
    """将更新写回 auto.cfg / crosshair.cfg。

    updates: {命令名: 文件值字符串} (已换算为最终文件值, 含 scale 字段, 如透明度 255)。
    写回保留原行缩进/分隔空格/行尾注释; 命令缺失时按组追加到对应组标题后。
    返回 {文件路径: 修改的行数} (调用方负责 .bak 备份与 dirty 管理)。
    """
    changed: dict[str, str] = {}
    # 按文件分组 (updates 已是文件值, 不再在此做 scale 换算——
    # scale 换算移到 UI 层, 以便用原始文件值精确判断「未修改」防 round 往返丢精度)
    by_file: dict[str, dict[str, str]] = {}
    for key, val in updates.items():
        f = FIELD_INDEX[key]
        by_file.setdefault(f.file, {})[key] = val

    for file_name, upd in by_file.items():
        path = os.path.join(cfg_dir, file_name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            lines = f.readlines()
        # 主行尾 (auto/crosshair 预设均为 CRLF; 检测避免混行尾)
        eol = "\r\n" if any(l.endswith("\r\n") for l in lines) else "\n"
        parsed = parse_cfg(path)
        remaining = dict(upd)
        n_changed = 0
        # 已存在命令: 行内替换
        for key, (val, comment, ln) in parsed.items():
            if key not in remaining:
                continue
            field = FIELD_INDEX[key]
            line = lines[ln]
            m = _LINE_RE.match(line.rstrip("\r\n"))
            if not m:
                continue
            indent, _k, sep, _rest = m.groups()
            new_line = f"{indent}{key}{sep}{_fmt_value(field, remaining[key])}{comment}{eol}"
            if new_line != line:
                lines[ln] = new_line
                n_changed += 1
            remaining.pop(key, None)
        # 缺失命令: 按所属组分组, 各自追加到对应组标题后 (crosshair.cfg 无分节走文件尾)
        # (deep-review 12轮: 原实现用第一个缺失命令的组名代理全部, 跨组缺失时错位)
        if remaining:
            by_group: dict[str, list[tuple[str, str]]] = {}
            for key, val in remaining.items():
                by_group.setdefault(_GROUP_OF.get(key, "性能"), []).append((key, val))
            insertions: list[tuple[int, list[str]]] = []
            for gn, items in by_group.items():
                anchor = _group_head_line(lines, gn)
                insertions.append((anchor, [
                    f"{key} {_fmt_value(FIELD_INDEX[key], val)}  // 由汤圆启动器添加{eol}"
                    for key, val in items]))
            # 从后往前插, 避免行号偏移
            for anchor, ins_lines in sorted(insertions, key=lambda x: -x[0]):
                lines[anchor:anchor] = ins_lines
                n_changed += len(ins_lines)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        changed[path] = str(n_changed)
    return changed


# 组名 -> 组标题关键字 (auto.cfg 分节标题, 追加缺失命令的锚点)
_GROUP_OF = {f.key: gn for gn, fs, _ in GROUPS for f in fs}


def cfg_dir_from_csgo(csgo_dir: str | None) -> str | None:
    """从 CS:GO 根目录推导 cfg 目录 (与 app/locator.find_cfg_dir 一致, 供本模块独立使用)"""
    if not csgo_dir:
        return None
    cand = os.path.join(csgo_dir, "csgo", "cfg")
    return cand if os.path.isdir(cand) else None
