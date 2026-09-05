"""设计令牌 — 汤圆启动器 (矢车菊蓝纯色体系)

来源: docs/tokens.md (与 docs/preview v1.html 保持双向一致, 见 rules.md §3 同步义务)
规则: 产品 UI 禁止硬编码色值, 一律引用本模块常量 (rules.md §2)
"""
import flet as ft

# ==================== 颜色 Colors ====================

# 背景
COL_BG_DEEP = "#0c0e14"        # 窗口外壳/标题栏/状态栏
COL_BG_MAIN = "#0f1117"        # 内容区
COL_BG_CARD = "#161922"        # 卡片
COL_BG_CARD_2 = "#1e293b"      # 头像底/次级卡
COL_BG_SIDEBAR = "#11141d"     # 侧栏
COL_BG_INPUT = "#20000000"     # 输入控件底 rgba(0,0,0,0.2)
COL_BG_GHOST = "#0affffff"     # 幽灵底 rgba(255,255,255,0.04)
COL_BG_GHOST_2 = "#08ffffff"   # rgba(255,255,255,0.03)
COL_BG_GHOST_3 = "#05ffffff"   # rgba(255,255,255,0.02)
# 历史别名 (main.py 仍在引用; 必须是模块常量 — 否则 _DARK 快照不含它,
# set_scheme 切回深色时残留浅色值 → 根容器/导航白底白字, v2.3.0 存量缺陷)
COL_BG = COL_BG_DEEP           # = COL_BG_DEEP
COL_CARD = COL_BG_CARD         # = COL_BG_CARD

# 品牌 (矢车菊蓝系)
COL_BRAND = "#6495ED"          # 主色
COL_BRAND_HOVER = "#4F7FE0"    # hover/启动中
COL_BRAND_LIGHT = "#9DB9F3"    # 浅 (文字/高亮)
COL_BRAND_SOFT = "#8FB1F0"     # 柔 (图标)
COL_BRAND_BG_10 = "#1a6495ED"  # 10% 底
COL_BRAND_BG_15 = "#266495ED"  # 15% 底
COL_BRAND_BG_18 = "#2e6495ED"  # 18% 底
COL_BRAND_BG_20 = "#336495ED"  # 20% 底

# 文字
COL_TEXT_PRIMARY = "#ffffff"
COL_TEXT_SECONDARY = "#e2e8f0"
COL_TEXT_MUTED = "#a0aec0"
COL_TEXT_DIM = "#64748b"
COL_TEXT_DISABLED = "#6b7280"

# 功能色
COL_OK = "#10b981"             # 成功/在线/低风险
COL_WARN = "#f59e0b"           # 运行中/中风险
COL_ERR = "#ef4444"            # 失败/高危
COL_WARN_BG = "#1ff59e0b"      # 警告提示条底 rgba(245,158,11,0.12) (tokens §1.4 warn-bg)
COL_ERR_BG = "#1fef4444"       # 错误提示条底 rgba(239,68,68,0.12) (tokens §1.4 err-bg)

# 边框
COL_BORDER_SUBTLE = "#0dffffff"    # rgba(255,255,255,0.05)
COL_BORDER_VISIBLE = "#1affffff"   # rgba(255,255,255,0.1)
COL_BORDER_BRAND = "#4d6495ED"     # rgba(100,149,237,0.3)
COL_FOCUS_RING = "#336495ED"       # rgba(100,149,237,0.2)

# 顶栏按钮 hover 提亮 (tokens.md §1.6 hover-btnbar 收编; 2026-08 UI 审查落地)
COL_BTN_BAR_HOVER = "#12ffffff"    # rgba(255,255,255,0.07)
# 窗口按钮/chip hover 提亮 (tokens.md §1.6 hover-winbtn, 白 8%)
COL_WINBTN_HOVER = "#14ffffff"     # rgba(255,255,255,0.08)

# 裁剪 (tokens.md §1.7, 修改头像页 2026-08-23)
COL_CROP_CANVAS_BG = "#0a0b10"     # 裁剪画布底 (比 bg-deep 更深)
COL_CROP_MASK = "#8c000000"        # 裁剪框外遮罩 rgba(0,0,0,0.55)
COL_CROP_GRID = "#40ffffff"        # 九宫格线 rgba(255,255,255,0.25)

# 主页品牌氛围垫层 (tokens.md §1.7 home-wash, v2.3.1 三轮):
# radial 椭圆置于主页内容区底层, 极低透明度品牌蓝, 非发光
COL_HOME_WASH = "#126495ED"        # rgba(100,149,237,0.07)

# 启动态 (收编硬编码, rules.md §2.3)
COL_LAUNCH_BUSY = COL_BRAND_HOVER  # 启动中 = 主色 hover
COL_LAUNCH_DONE = COL_OK           # 已启动 = 成功绿
COL_LAUNCH_GLOW = "#6610b981"      # 已启动辉光 rgba(16,185,129,0.4)

# 开关 (design-system.md #28 Switch)
COL_SWITCH_INACTIVE_THUMB = "#8A8494"
COL_SWITCH_INACTIVE_TRACK = "#2A2730"

# 阴影 (HTML 事实源 :root; 换装整体重建见 _rebuild_shadows)
SHADOW_WINDOW = ft.BoxShadow(blur_radius=80, spread_radius=0, color="#99000000",
                             offset=ft.Offset(0, 24))
SHADOW_BTN = ft.BoxShadow(blur_radius=8, spread_radius=0, color="#59000000",
                          offset=ft.Offset(0, 2))
SHADOW_BTN_HOVER = ft.BoxShadow(blur_radius=12, spread_radius=0, color="#66000000",
                                offset=ft.Offset(0, 4))
SHADOW_DOT_ONLINE = ft.BoxShadow(blur_radius=0, spread_radius=3, color="#2610b981")
SHADOW_THUMB = ft.BoxShadow(blur_radius=3, spread_radius=0, color="#66000000",
                            offset=ft.Offset(0, 1))
# 卡片柔影 (tokens.md §1.7 card-shadow): 0 2px 10px rgba(0,0,0,0.25)
SHADOW_CARD = ft.BoxShadow(blur_radius=10, spread_radius=0, color="#40000000",
                           offset=ft.Offset(0, 2))
# 浮层投影 (HTML --float-shadow: 下拉菜单/悬停面板/主题菜单): 0 8px 24px rgba(0,0,0,0.4)
SHADOW_FLOAT = ft.BoxShadow(blur_radius=24, spread_radius=0, color="#66000000",
                            offset=ft.Offset(0, 8))

# ==================== 动效 Motion (tokens.md §7, v2.3.1 三轮) ====================
MOTION_FAST = 150        # 面板/菜单/弹窗进出、遮罩淡入
MOTION_GROUP = 180       # 编辑页分组切换
MOTION_NORMAL = 220      # 视图切换、换装淡入
# ease-standard = cubic-bezier(0.4,0,0.2,1); Flet AnimationCurve 无自定义 cubic,
# EASE_IN_OUT 为最接近的内置档 (150~220ms 下与标准曲线无可感差异)
EASE_STANDARD = ft.AnimationCurve.EASE_IN_OUT

# ==================== 字号 Font Sizes ====================
FONT_44 = 44        # 启动按钮图标
FONT_36 = 36        # 头像占位首字
FONT_20 = 20        # 页面标题 (800)
FONT_20_IC = 20     # 导航图标
FONT_18 = 18        # 昵称/主页标题 (700)
FONT_16 = 16        # 启动命令输入框 (mono)
FONT_15 = 15        # 在线人数/标签
FONT_14 = 14        # 卡片标题/输入框
FONT_13 = 13        # 下拉框
FONT_12 = 12        # 描述/按钮
FONT_11 = 11        # 标签/提示
FONT_10 = 10        # 徽章/键名

# ==================== 圆角 Radius (tokens.md §3, v2.3.1 Win11 档位) ====================
# 旧常量 RADIUS_LG/SM/XS/2XS 已由 RADIUS_CARD/RADIUS_CTRL 取代 (tokens.md §3)
RADIUS_CARD = 8          # 卡片/面板/弹窗/菜单/悬停面板
RADIUS_CTRL = 4          # 按钮/输入框/下拉/chip/标签/窗口控制钮/导航项/提示条
RADIUS_CIRCLE = 999      # 正圆/胶囊 (Container 用 999 或 尺寸/2)
RADIUS_PILL = 999
RADIUS_MD = 12           # 预览工具栏 (非产品)

# ==================== 间距 Spacing ====================
SPACE_4 = 4
SPACE_6 = 6
SPACE_7 = 7
SPACE_8 = 8
SPACE_10 = 10
SPACE_12 = 12
SPACE_14 = 14
SPACE_16 = 16
SPACE_20 = 20
SPACE_24 = 24
SPACE_36 = 36
SPACE_48 = 48

# ==================== 布局常量 Layout ====================
WIN_LAUNCHER = (360, 510)
WIN_EDIT = (784, 600)
H_TITLEBAR = 56
H_STATUSBAR = 64
W_SIDEBAR = 96
H_NAV_ITEM = 80
S_AVATAR = 100
S_BTN_LAUNCH = 110
# H_INPUT: 输入控件设计高度 (HTML tokens 40px; flet 实机 TextField 默认 ~63px、
# Dropdown 默认 48px — 双列卡片等高时 Dropdown 用 64 匹配 TextField, 见 main.py 实测注释)
H_INPUT = 48
H_BTN_BAR = 34
H_BTN_RUN = 32
W_BTN_WIN = 28
S_DOT = 8
# 修改头像页 (tokens.md §5, 2026-08-23)
S_CROP_CANVAS = 480     # 裁剪画布边长
S_CROP_HANDLE = 14      # 裁剪把手边长
CROP_MIN = 32           # 裁剪框最小边长
S_PREVIEW_AVATAR = 96   # 头像预览直径
W_AVATAR_SIDE = 200     # 修改头像右栏宽
H_BTN_AV = 36           # 头像操作按钮高

# ==================== 字体族 ====================
FONT_CN = "HarmonyOS Sans SC"   # HTML 事实源同款 (docs/fonts/sc 自托管 woff2; 2026-08 装系统版 ttf 用户级)
FONT_MONO = "JetBrains Mono"    # HTML 事实源同款 (2026-08 装系统版)

# ==================== 深浅双主题 (v2.3.0 深色模式定时切换) ====================
# 深色 = 上方全部常量 (事实源不变); 浅色 = 下表覆盖项, 未覆盖的 token 深浅通用
# (品牌主色族/功能色/半透明主色底/间距字号布局全部共用)。
# 消费方铁律: 颜色/阴影一律 theme.COL_X 属性访问 — from-import 会冻结启动时的深色值,
# set_scheme 换装后不可见 (main.py/ui.py 2026-08-30 已全部改为动态访问)。

_LIGHT = {
    # 背景: 浅灰蓝纸面 + 纯白卡片 (保持窗口三层层次: 外壳 < 内容区 < 卡片)
    "COL_BG_DEEP": "#eef1f8",
    "COL_BG": "#eef1f8",           # main.py 历史别名 (= COL_BG_DEEP)
    "COL_BG_MAIN": "#f6f8fc",
    "COL_BG_CARD": "#ffffff",
    "COL_CARD": "#ffffff",         # main.py 历史别名 (= COL_BG_CARD)
    "COL_BG_CARD_2": "#e3eaf6",
    "COL_BG_SIDEBAR": "#f0f3fa",
    "COL_BG_INPUT": "#0d1e293b",       # slate 5%
    "COL_BG_GHOST": "#0a1e293b",       # slate 4%
    "COL_BG_GHOST_2": "#081e293b",     # slate 3%
    "COL_BG_GHOST_3": "#051e293b",     # slate 2%
    # 品牌: 主色/悬停不变; "浅"变体在浅色底下改为深品牌 (文字对比度)
    "COL_BRAND_LIGHT": "#3d63c9",
    "COL_BRAND_SOFT": "#5a7fd6",
    # 文字: 深墨字阶 (slate)
    "COL_TEXT_PRIMARY": "#1e293b",
    "COL_TEXT_SECONDARY": "#334155",
    "COL_TEXT_MUTED": "#64748b",
    "COL_TEXT_DIM": "#94a3b8",
    "COL_TEXT_DISABLED": "#a8b3c4",
    # 边框: 深色细线 (slate 半透明)
    "COL_BORDER_SUBTLE": "#0d1e293b",
    "COL_BORDER_VISIBLE": "#1f1e293b",
    "COL_BTN_BAR_HOVER": "#121e293b",
    "COL_WINBTN_HOVER": "#141e293b",
    # 主页氛围垫层: 浅色档 6% 透明度 (tokens.md §1.7 home-wash)
    "COL_HOME_WASH": "#0f6495ED",
    # 裁剪画布: 浅灰底 (遮罩/九宫格深浅通用不覆盖)
    "COL_CROP_CANVAS_BG": "#e6e9f1",
    # 开关: 白钮 + 浅灰轨
    "COL_SWITCH_INACTIVE_THUMB": "#ffffff",
    "COL_SWITCH_INACTIVE_TRACK": "#c7d0de",
}

_scheme = "dark"

# 捕获 import 时的深色默认值 (上方常量即深色事实源)
_DARK = {n: globals()[n] for n in list(globals()) if n.startswith(("COL_", "SHADOW_"))}


def _rebuild_shadows(light: bool) -> None:
    """阴影对象不可原地改色, 换装时整体重建 (浅色用 slate 灰低透明度)。"""
    g = globals()
    if light:
        g["SHADOW_WINDOW"] = ft.BoxShadow(blur_radius=80, spread_radius=0,
                                          color="#3d94a3b8", offset=ft.Offset(0, 24))
        g["SHADOW_BTN"] = ft.BoxShadow(blur_radius=8, spread_radius=0,
                                       color="#2e334155", offset=ft.Offset(0, 2))
        g["SHADOW_BTN_HOVER"] = ft.BoxShadow(blur_radius=12, spread_radius=0,
                                             color="#33334155", offset=ft.Offset(0, 4))
        g["SHADOW_THUMB"] = ft.BoxShadow(blur_radius=3, spread_radius=0,
                                         color="#4d334155", offset=ft.Offset(0, 1))
        # card-shadow 浅色: 0 2px 10px rgba(30,41,59,0.06) (tokens.md §1.7)
        g["SHADOW_CARD"] = ft.BoxShadow(blur_radius=10, spread_radius=0,
                                        color="#0f1e293b", offset=ft.Offset(0, 2))
        # float-shadow 浅色: 0 8px 24px rgba(30,41,59,0.16)
        g["SHADOW_FLOAT"] = ft.BoxShadow(blur_radius=24, spread_radius=0,
                                         color="#291e293b", offset=ft.Offset(0, 8))
        # SHADOW_DOT_ONLINE (绿色微光) 深浅通用, 不重建
    else:
        g["SHADOW_WINDOW"] = ft.BoxShadow(blur_radius=80, spread_radius=0,
                                          color="#99000000", offset=ft.Offset(0, 24))
        g["SHADOW_BTN"] = ft.BoxShadow(blur_radius=8, spread_radius=0,
                                       color="#59000000", offset=ft.Offset(0, 2))
        g["SHADOW_BTN_HOVER"] = ft.BoxShadow(blur_radius=12, spread_radius=0,
                                             color="#66000000", offset=ft.Offset(0, 4))
        g["SHADOW_THUMB"] = ft.BoxShadow(blur_radius=3, spread_radius=0,
                                         color="#66000000", offset=ft.Offset(0, 1))
        # card-shadow 深色: 0 2px 10px rgba(0,0,0,0.25) (tokens.md §1.7)
        g["SHADOW_CARD"] = ft.BoxShadow(blur_radius=10, spread_radius=0,
                                        color="#40000000", offset=ft.Offset(0, 2))
        # float-shadow 深色: 0 8px 24px rgba(0,0,0,0.4)
        g["SHADOW_FLOAT"] = ft.BoxShadow(blur_radius=24, spread_radius=0,
                                         color="#66000000", offset=ft.Offset(0, 8))


def _rebuild_derived() -> None:
    """派生色 (原 main.py 模块级常量, v2.3.0 收编进令牌模块随换装更新):
    主色底上的文字深浅两套均为白字 (品牌蓝底); 其余跟随当前 token。"""
    g = globals()
    g["ON_BRAND"] = "#ffffff"
    g["CHIP_ADDED_BG"] = g["COL_BRAND_LIGHT"]
    g["INPUT_BORDER"] = g["COL_BORDER_VISIBLE"]
    g["INPUT_FILL"] = g["COL_BG_INPUT"]


def set_scheme(name: str) -> None:
    """整体换装: 'dark' | 'light'。只动本模块全局, 消费方下次取 theme.COL_X 即新值;
    已创建控件的颜色不会自动变, 由调用方负责重建可见视图 (main.py rebuild)。"""
    global _scheme
    g = globals()
    light = (name == "light")
    if light:
        for k, v in _LIGHT.items():
            g[k] = v
    else:
        for k, v in _DARK.items():
            g[k] = v
    _rebuild_shadows(light)
    _rebuild_derived()
    _scheme = "light" if light else "dark"


def get_scheme() -> str:
    return _scheme


_rebuild_derived()   # 派生色初始生成 (深色)
