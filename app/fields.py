# -*- coding: utf-8 -*-
"""
rev.ini 字段定义(UI 表现层数据)
- 与 ini_model.py 分离: 模型只管解析/序列化, 字段定义描述"界面上要展示哪些配置项"
- 字段类型: bool / text / int / combo / textarea / rank
- 高级分组支持 type="tabs" 收纳子分组, type="tools" 渲染修复工具页
- schema 唯一来源: FieldDef dataclass; *_field() 构造器是兼容层的薄封装,
  输出 dict 结构完全一致, 旧调用方(test/外部脚本)无需改动。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Optional

# ---------- 类型安全字段定义 (dataclass, schema 唯一来源) ----------

@dataclass
class FieldDef:
    """字段定义的强类型表示。to_dict() 输出与 *_field() 构造器完全兼容。"""
    section: str
    key: str
    label: str
    type: str
    desc: str = ""
    default: Any = None
    maxlen: int = 0          # text
    placeholder: str = ""    # text / textarea
    lo: int = 0              # int
    hi: int = 0              # int
    suffix: str = ""         # int
    items: list = dc_field(default_factory=list)       # combo
    display_map: Optional[dict] = None                 # combo
    chips: list = dc_field(default_factory=list)       # textarea

    def to_dict(self) -> dict:
        """转换为与 *_field() 构造器输出完全一致的 dict"""
        d = {"section": self.section, "key": self.key, "label": self.label,
             "desc": self.desc, "type": self.type}
        if self.default is not None:
            d["default"] = self.default
        if self.type == "text":
            d["maxlen"] = self.maxlen
            d["placeholder"] = self.placeholder
        elif self.type == "int":
            d["lo"] = self.lo
            d["hi"] = self.hi
            d["suffix"] = self.suffix
        elif self.type in ("combo", "rank"):
            if self.type == "combo":
                d["items"] = self.items
                # display_map 为 None 时不输出该键, 与旧构造器行为一致 (M4)
                if self.display_map is not None:
                    d["display_map"] = self.display_map
        elif self.type == "textarea":
            d["placeholder"] = self.placeholder
            d["chips"] = self.chips
        return d

    @classmethod
    def bool(cls, section, key, label, desc="", default=False):
        assert isinstance(default, bool), \
            f"{key} 的 bool 默认值必须是 bool, 得到 {type(default).__name__}"
        return cls(section, key, label, "bool", desc, default).to_dict()

    @classmethod
    def text(cls, section, key, label, desc="", default="", maxlen=64, placeholder=""):
        assert isinstance(default, str), \
            f"{key} 的 text 默认值必须是 str, 得到 {type(default).__name__}"
        assert isinstance(maxlen, int), f"{key} 的 maxlen 必须是 int"
        return cls(section, key, label, "text", desc, default,
                   maxlen, placeholder).to_dict()

    @classmethod
    def int(cls, section, key, label, desc="", default=0, lo=0, hi=100, suffix=""):
        assert isinstance(default, int) and not isinstance(default, bool), \
            f"{key} 的 int 默认值必须是 int, 得到 {type(default).__name__}"
        assert isinstance(lo, int) and isinstance(hi, int) and lo <= hi, \
            f"{key} 的范围无效: lo={lo!r} hi={hi!r}"
        return cls(section, key, label, "int", desc, default,
                   lo=lo, hi=hi, suffix=suffix).to_dict()

    @classmethod
    def combo(cls, section, key, label, desc="", default="", items=(), display_map=None):
        """下拉选择。display_map: 存储值 -> 显示名 的映射(如语言代码 -> 中文名)"""
        assert isinstance(default, str), f"{key} 的 combo 默认值必须是 str"
        assert isinstance(items, (list, tuple)), f"{key} 的 items 必须是序列"
        assert display_map is None or isinstance(display_map, dict), \
            f"{key} 的 display_map 必须是 dict 或 None"
        return cls(section, key, label, "combo", desc, default,
                   items=list(items), display_map=display_map).to_dict()

    @classmethod
    def textarea(cls, section, key, label, desc="", default="", placeholder="", chips=()):
        """多行大输入框:保存时自动合并为一行(空格分隔)
        chips: 推荐启动项列表 [{"args": "...", "label": "...", "tip": "..."}]"""
        assert isinstance(default, str), f"{key} 的 textarea 默认值必须是 str"
        assert isinstance(chips, (list, tuple)), f"{key} 的 chips 必须是序列"
        return cls(section, key, label, "textarea", desc, default,
                   placeholder=placeholder, chips=list(chips)).to_dict()

    @classmethod
    def rank(cls, section, key, label, desc="", default=18):
        """伪装段位:下拉选择段位名,存储 1-18 数字"""
        assert isinstance(default, int) and not isinstance(default, bool), \
            f"{key} 的 rank 默认值必须是 int"
        return cls(section, key, label, "rank", desc, default).to_dict()


# ---------- 字段构造器 (兼容层: 委托 FieldDef, 保持旧 API 与校验行为) ----------
def bool_field(section, key, label, desc="", default=False):
    return FieldDef.bool(section, key, label, desc, default)


def text_field(section, key, label, desc="", default="", maxlen=64, placeholder=""):
    return FieldDef.text(section, key, label, desc, default, maxlen, placeholder)


def int_field(section, key, label, desc="", default=0, lo=0, hi=100, suffix=""):
    return FieldDef.int(section, key, label, desc, default, lo, hi, suffix)


def combo_field(section, key, label, desc="", default="", items=(), display_map=None):
    return FieldDef.combo(section, key, label, desc, default, items, display_map)


def textarea_field(section, key, label, desc="", default="", placeholder="", chips=()):
    return FieldDef.textarea(section, key, label, desc, default, placeholder, chips)


def rank_field(section, key, label, desc="", default=18):
    return FieldDef.rank(section, key, label, desc, default)


# 伪装段位 (RankLevel 1-18) — 官方名 + 玩家俗称,index+1 = 存储值
RANK_DISPLAY = [
    "白银一",                       # 1
    "白银二",                       # 2
    "白银三",                       # 3
    "白银四",                       # 4
    "白银精英",                     # 5
    "白银精英大师",                 # 6
    "黄金新星一",                   # 7
    "黄金新星二",                   # 8
    "黄金新星三",                   # 9
    "黄金新星大师",                 # 10
    "大师守卫一 (麦穗)",            # 11
    "大师守卫二 (双麦穗)",          # 12
    "大师守卫精英 (菊花)",          # 13
    "杰出大师守卫 (大老鹰)",        # 14
    "传奇之鹰 (老鹰)",              # 15
    "传奇之鹰大师 (老鹰大师)",      # 16
    "至尊大师 (小地球)",            # 17
    "全球精英 (大地球)",            # 18
]


def rank_name_to_level(name: str) -> int:
    """段位名 → 1-18 等级"""
    try:
        return RANK_DISPLAY.index(name) + 1
    except ValueError:
        return 18


def rank_level_to_name(level: int) -> str:
    """1-18 等级 → 段位名"""
    try:
        return RANK_DISPLAY[int(level) - 1]
    except (ValueError, IndexError):
        return RANK_DISPLAY[17]


# 语言代码 -> 中文名 (combo 的 display_map)
LANG_NAMES = {
    "schinese": "简体中文", "tchinese": "繁体中文", "english": "英文",
    "russian": "俄语", "german": "德语", "french": "法语",
    "spanish": "西班牙语", "portuguese": "葡萄牙语", "polish": "波兰语",
    "turkish": "土耳其语", "japanese": "日语", "korean": "韩语",
}

# 字段分组定义
FIELD_GROUPS = [
    {
        "title": "常用设置",
        "icon_key": "tune",
        "desc": "游戏内昵称、段位伪装、界面语言与头像显示 · 保存后自动备份 · 重启游戏生效",
        "fields": [
            text_field("steamclient", "PlayerName", "游戏昵称",
                       "显示在游戏内与服务器列表中的名字", "Player", 32, "输入你的昵称"),
            text_field("steamclient", "ClanTag", "战队标签",
                       "显示在昵称前的短标签,留空则不显示", "", 16, "如: [CN]"),
            combo_field("Emulator", "Language", "界面语言",
                        "游戏客户端显示语言", "schinese",
                        ["schinese", "tchinese", "english", "russian", "german",
                         "french", "spanish", "portuguese", "polish", "turkish",
                         "japanese", "korean"],
                        display_map=LANG_NAMES),
            rank_field("steamclient", "RankLevel", "伪装段位",
                       "别人看到的你的竞技段位(按官方名+俗称显示)",
                       default=18),
            int_field("steamclient", "PrivatRank", "服役勋章等级",
                      "0 = 无勋章,1~40 为勋章等级", 1, 0, 40),
            bool_field("steamclient", "Use_avatar", "显示头像",
                       "使用 Steam 模拟头像", True),
        ],
    },
    {
        "title": "加载器",
        "icon_key": "play",
        "desc": "启动参数与主进程设置",
        "fields": [
            textarea_field("Loader", "ProcName", "启动命令",
                           "游戏启动参数,每个参数一行,保存时自动合并为一行。点击下方推荐项即可一键添加",
                           "csgo.exe -steam -silent -high +sv_lan 1",
                           "csgo.exe -steam -silent -high +sv_lan 1",
                           chips=[
                               {"args": "-high", "label": "-high",
                                "tip": "提高 CS:GO 进程优先级"},
                               {"args": "-novid", "label": "-novid",
                                "tip": "关闭开场动画"},
                               {"args": "-nojoy", "label": "-nojoy",
                                "tip": "禁用摇杆,优化帧数"},
                               {"args": "-w 1920 -h 1080", "label": "-w 1920 -h 1080",
                                "tip": "设置窗口分辨率 1920x1080"},
                               {"args": "-tickrate 128 +cl_cmdrate 128 +cl_updaterate 128",
                                "label": "128 tick 参数",
                                "tip": "设置服务器/客户端 128 tick"},
                           ]),
            text_field("Loader", "ConnectServer", "自动进入服务器",
                       "启动游戏后自动连接该服务器(留空则不自动进服)。格式 IP:端口, 如 127.0.0.1:27015",
                       "", 32, "如: 127.0.0.1:27015"),
        ],
    },
    {
            "title": "修复工具",
            "icon_key": "wrench",
            "desc": "一键运行 CS:GO 内置维护脚本:清缓存、修复 Steam 错误",
            "type": "tools",
        },
    ]
