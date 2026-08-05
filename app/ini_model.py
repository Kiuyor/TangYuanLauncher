# -*- coding: utf-8 -*-
"""
rev.ini 解析 / 序列化模型
- 保留注释、空行与原始格式(含行尾风格 CRLF/LF、键名大小写、= 两侧空白)
- 只做定向键值修改,不破坏配置文件结构
"""
from __future__ import annotations

import shutil
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import VERSION

# 兼容编码:revLoader(2017 C++ 程序)按 ANSI(GBK)读 ini,
# 现代编辑器用 UTF-8。读取时自动探测,保存时由 UI 指定。
SUPPORTED_ENCODINGS = ("utf-8", "gbk")


@dataclass
class RevIni:
    """rev.ini 配置模型,按行保留原始结构"""

    lines: List[str] = field(default_factory=list)
    # (section_lower, key_lower) -> line_index
    _index: Dict[Tuple[str, str], int] = field(default_factory=dict)
    _section_lines: Dict[str, int] = field(default_factory=dict)  # section_lower -> 首个键行
    _section_tail: Dict[str, int] = field(default_factory=dict)   # section_lower -> 末尾行
    _section_keys: Dict[str, List[str]] = field(default_factory=dict)  # section_lower -> 键列表(文件序,去重)
    source_encoding: str = "utf-8"  # 读取时探测到的编码
    trailing_newline: bool = True   # 原文件是否以换行结尾(保存时还原,避免格式漂移)
    line_ending: str = "\n"         # 原文件行尾风格 ("\n" 或 "\r\n",保存时还原)

    # ---------- 解析 ----------
    @classmethod
    def load(cls, path: str) -> "RevIni":
        with open(path, "rb") as f:
            data = f.read()
        text, enc = decode_ini_bytes(data)
        model = cls.from_text(text)
        model.source_encoding = enc
        return model

    @classmethod
    def from_text(cls, text: str) -> "RevIni":
        model = cls()
        model.lines = text.splitlines()
        # 记录原始文件是否以换行结尾: splitlines() 会丢弃末尾换行,
        # 保存时若不还原,每保存一次文件末尾结构都会变化(格式漂移)
        model.trailing_newline = text.endswith(("\n", "\r"))
        # 记录行尾风格: CRLF 文件保存时同样要还原, 否则整个文件被改写为 LF
        lf = text.count("\n")
        model.line_ending = "\r\n" if lf and text.count("\r\n") * 2 >= lf else "\n"
        section = ""

        for i, raw in enumerate(model.lines):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith(";"):
                if section:
                    model._section_tail[section] = i
                continue
            if stripped.startswith("["):
                section = stripped.strip("[]").strip().lower()
                model._section_lines.setdefault(section, i)
                model._section_tail[section] = i
                continue
            if "=" in stripped:
                key_raw, _ = stripped.split("=", 1)
                key = _unquote(key_raw.strip())
                key_lower = key.lower()
                sec_lower = section
                model._index[(sec_lower, key_lower)] = i
                sk = model._section_keys.setdefault(section, [])
                if key_lower not in sk:
                    sk.append(key_lower)
                if section:
                    model._section_tail[section] = i
        return model

    # ---------- 查询 ----------
    def get(self, section: str, key: str, default: str = "") -> str:
        idx = self._index.get((section.lower(), key.lower()))
        if idx is None:
            return default
        raw = self.lines[idx]
        _, val = raw.split("=", 1)
        return _unquote(val.strip())

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        v = self.get(section, key, "").strip().lower()
        if v in ("true", "1", "yes", "on"):
            return True
        if v in ("false", "0", "no", "off"):
            return False
        return default

    def has(self, section: str, key: str) -> bool:
        return (section.lower(), key.lower()) in self._index

    def keys(self, section: str) -> List[str]:
        """指定 section 的键列表(文件序,去重)。增量维护,O(section 键数)"""
        return list(self._section_keys.get(section.lower(), []))

    # ---------- 修改 ----------
    def set(self, section: str, key: str, value: str) -> None:
        """设置键值;存在则原地更新(保留键名大小写与 = 两侧空白),
        不存在则追加到对应 section 末尾"""
        sec = section.lower()
        key_lower = key.lower()
        idx = self._index.get((sec, key_lower))

        if idx is not None:
            raw = self.lines[idx]
            stripped = raw.lstrip()
            indent = raw[: len(raw) - len(stripped)]
            key_part, old_val = stripped.split("=", 1)
            stored_key = key_part.rstrip()          # 原键名(保留大小写)
            eq_left = key_part[len(stored_key):]    # 键名与 = 之间的空白
            eq_right = old_val[: len(old_val) - len(old_val.lstrip())]  # = 与值之间的空白
            # 保留原始引号风格: 原值带双/单引号则新值用同款引号包裹 (deep-review F11)
            stripped_old = old_val.strip()
            if len(stripped_old) >= 2 and stripped_old[0] == stripped_old[-1] \
                    and stripped_old[0] in ('"', "'"):
                q = stripped_old[0]
                # 新值自身已带同款引号则不重复包裹——否则每轮编辑引号 +2 累积 (deep-review R8)
                sv = value.strip()
                if not (len(sv) >= 2 and sv[0] == sv[-1] == q):
                    value = f"{q}{value}{q}"
            self.lines[idx] = f"{indent}{stored_key}{eq_left}={eq_right}{value}"
            return

        # 追加新键
        insert_at = None
        if sec in self._section_tail:
            insert_at = self._section_tail[sec] + 1
        elif self.lines:
            insert_at = len(self.lines)

        new_lines: List[str] = []
        is_new_section = sec not in self._section_lines
        if is_new_section:
            # 需要新建 section: 文件非空时用空行分隔, 空文件直接写头 (L2)
            prefix = "\n" if self.lines else ""
            new_lines.append(f"{prefix}[{section}]")
        new_lines.append(f"{key} = {value}")

        if insert_at is None:
            insert_at = 0
            self.lines.extend(new_lines)
        else:
            self.lines[insert_at:insert_at] = new_lines

        # 增量维护索引:只平移受影响行号 + 登记新键,不全量重建
        n = len(new_lines)
        self._shift_from(insert_at, n)
        if is_new_section:
            self._section_lines[sec] = insert_at
        if sec:
            self._section_tail[sec] = insert_at + n - 1
        self._index[(sec, key_lower)] = insert_at + n - 1
        sk = self._section_keys.setdefault(sec, [])
        if key_lower not in sk:
            sk.append(key_lower)

    def set_bool(self, section: str, key: str, value: bool) -> None:
        self.set(section, key, "true" if value else "false")

    def remove(self, section: str, key: str) -> None:
        sec = section.lower()
        key_lower = key.lower()
        idx = self._index.get((sec, key_lower))
        if idx is None:
            return
        del self.lines[idx]
        del self._index[(sec, key_lower)]
        sk = self._section_keys.get(sec)
        if sk and key_lower in sk:
            sk.remove(key_lower)
        # 增量维护:平移后续行号 + 局部重算该 section 的 tail
        self._shift_from(idx + 1, -1)
        self._refresh_tail(sec)

    def _shift_from(self, at: int, delta: int) -> None:
        """把行号 >= at 的索引项平移 delta(增量插入/删除后局部维护)"""
        if not delta:
            return
        for k, v in self._index.items():
            if v >= at:
                self._index[k] = v + delta
        for k, v in self._section_tail.items():
            if v >= at:
                self._section_tail[k] = v + delta
        for k, v in self._section_lines.items():
            if v >= at:
                self._section_lines[k] = v + delta

    def _refresh_tail(self, sec: str) -> None:
        """局部重算指定 section 的 tail(删行后),只扫该 section 范围"""
        if sec not in self._section_tail:
            return
        lines = self.lines
        h = self._section_lines.get(sec)
        if h is None:
            # 无 header 的 section(理论上不存在),退化为清除
            self._section_tail.pop(sec, None)
            return
        tail = h
        for i in range(h + 1, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("["):
                break
            if not stripped:
                continue
            tail = i
        self._section_tail[sec] = tail

    def _reindex(self) -> None:
        self._index.clear()
        self._section_lines.clear()
        self._section_tail.clear()
        self._section_keys.clear()
        section = ""
        for i, raw in enumerate(self.lines):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith(("#", ";")):
                if section:
                    self._section_tail[section] = i
                continue
            if stripped.startswith("["):
                section = stripped.strip("[]").strip().lower()
                self._section_lines.setdefault(section, i)
                self._section_tail[section] = i
                continue
            if "=" in stripped:
                key_raw, _ = stripped.split("=", 1)
                key_lower = _unquote(key_raw.strip()).lower()
                self._index[(section, key_lower)] = i
                sk = self._section_keys.setdefault(section, [])
                if key_lower not in sk:
                    sk.append(key_lower)
                if section:
                    self._section_tail[section] = i

    # ---------- 序列化 ----------
    def to_text(self) -> str:
        return self.line_ending.join(self.lines)

    def save(self, path: str, encoding: str = "utf-8") -> None:
        """保存文件。encoding: 'utf-8' 或 'gbk'。
        revLoader 按 ANSI(GBK)读配置,中文名建议用 gbk。
        未知编码直接报错 (L1): 静默回退 UTF-8 会把 GBK 文件写成 UTF-8,
        导致 revLoader 端中文昵称乱码且无任何提示。"""
        if encoding not in SUPPORTED_ENCODINGS:
            raise ValueError(
                f"不支持的编码: {encoding!r}, 仅支持 {'/'.join(SUPPORTED_ENCODINGS)}")
        # 还原原始结尾与行尾风格: 原文件以换行结尾才追加,
        # 行尾风格(CRLF/LF)按读取时探测的结果还原, 避免无端改变文件结构
        text = self.to_text()
        if self.trailing_newline:
            text += self.line_ending
        data = encode_ini_text(text, encoding)
        with open(path, "wb") as f:
            f.write(data)

    # ---------- 备份 ----------
    @staticmethod
    def backup(path: str) -> Optional[str]:
        """保存前自动备份为 rev.ini.bak,返回备份路径;失败返回 None"""
        try:
            bak = path + ".bak"
            shutil.copy2(path, bak)
            return bak
        except OSError:
            return None


def _unquote(s: str) -> str:
    # 双引号与单引号对称处理 (deep-review F11: 原实现只剥双引号,
    # 单引号值会带引号进入 UI 显示并导致 populate/collect 解析不一致)
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def decode_ini_bytes(data: bytes) -> Tuple[str, str]:
    """探测 rev.ini 字节编码:优先 UTF-8(含 BOM),失败回退 GBK。
    返回 (文本, 使用的编码)"""
    # 带 BOM 的 UTF-8
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8"
    # 严格 UTF-8 校验:有中文时 UTF-8 字节序列特征明显
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        # 纯 ASCII(无多字节字符)在 GBK/UTF-8 下字节完全一致, 无法区分。
        # 按 revLoader(2017) 的原生编码 GBK 标记, 避免用户随后输入中文时
        # 下拉框默认 UTF-8 保存, 导致游戏端昵称乱码。
        if text.isascii():
            return text, "gbk"
        return text, "utf-8"
    # 回退 GBK(revLoader 原生编码)
    try:
        return data.decode("gbk"), "gbk"
    except UnicodeDecodeError:
        # 最终兜底:替换损坏字节(原始数据不可逆,给出警告便于排查)
        warnings.warn(
            "rev.ini 编码无法识别(非 UTF-8/GBK),损坏字节将被替换,原数据不可恢复",
            RuntimeWarning, stacklevel=2)
        return data.decode("utf-8", errors="replace"), "utf-8"


def encode_ini_text(text: str, encoding: str) -> bytes:
    """按指定编码序列化 rev.ini 文本"""
    if encoding == "gbk":
        return text.encode("gbk")
    return text.encode("utf-8")


def default_ini_text() -> str:
    """生成一份默认 rev.ini 模板(版本号来自 app.VERSION 单一来源)"""
    return f"""# Rev.Ini 配置文件
# 修改后需重启游戏生效
# MasterServer 是局域网主服务器地址,联机依赖,请谨慎修改
# 中文昵称请用 ANSI (GBK) 编码保存,否则 revLoader 读出来会乱码
# Loader.ProcName 是启动命令,可追加 -window / -w 1280 -h 720 等参数

[Loader]
ProcName = csgo.exe -steam -silent -high +sv_lan 1

[Emulator]
CacheEnabled = false
CachePath = D:\\Steam\\SteamApps
Language = schinese
Logging = false
SteamDll = .\\steam\\Steam2.dll
SteamClient = true
SteamUser = Nosteam-CSGO-USER

[Log]
FileSystem = false
Account = false
UserID = false

[steamclient]
Logging = false
PlayerName = Player
ClanTag = 
Use_avatar = true
RankLevel = 18
PrivatRank = 1

MasterServer = 127.0.0.1:27011
GameVersion = {VERSION}

[GameServer]
AllowOldRev74 = false
AllowOldRev = false
AllowUnknown = false
AllowCracked = true
AllowLegit = false
AllowedAnyCountConnectUnknownClientWithOneIP = false
Fake_player = false
RevEmu_2012 = false
AddCountPlayerInServerName = false

Check_Ticket = true
Allow_Fail_Check = false
Check_Ticket_Async = true

[GameServerNSNet]
EnableNSNetSvc = BOTH

[version]
game = {VERSION}
"""

# ---------- 字段定义(已移至 fields.py) ----------
# 兼容导入: 旧代码可能写 `from ini_model import FIELD_GROUPS / rank_* / *_field()`。
# 新代码应直接 `from .fields import ...`。保留此层避免外部脚本/测试中断,
# 但内部模块已迁移到直接从 fields.py 导入。
from .fields import (  # noqa: E402, F401
    FIELD_GROUPS, LANG_NAMES, RANK_DISPLAY,
    bool_field, combo_field, int_field, rank_field,
    rank_level_to_name, rank_name_to_level,
    text_field, textarea_field,
)
