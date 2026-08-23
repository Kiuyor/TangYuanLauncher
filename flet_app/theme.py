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

# 启动态 (收编硬编码, rules.md §2.3)
COL_LAUNCH_BUSY = COL_BRAND_HOVER  # 启动中 = 主色 hover
COL_LAUNCH_DONE = COL_OK           # 已启动 = 成功绿
COL_LAUNCH_GLOW = "#6610b981"      # 已启动辉光 rgba(16,185,129,0.4)

# 开关 (design-system.md #28 Switch)
COL_SWITCH_INACTIVE_THUMB = "#8A8494"
COL_SWITCH_INACTIVE_TRACK = "#2A2730"

# 阴影
SHADOW_WINDOW = ft.BoxShadow(blur_radius=80, spread_radius=0, color="#99000000",
                             offset=ft.Offset(0, 24))
SHADOW_BTN = ft.BoxShadow(blur_radius=8, spread_radius=0, color="#59000000",
                          offset=ft.Offset(0, 2))
SHADOW_BTN_HOVER = ft.BoxShadow(blur_radius=12, spread_radius=0, color="#66000000",
                                offset=ft.Offset(0, 4))
SHADOW_DOT_ONLINE = ft.BoxShadow(blur_radius=0, spread_radius=3, color="#2610b981")
SHADOW_THUMB = ft.BoxShadow(blur_radius=3, spread_radius=0, color="#66000000",
                            offset=ft.Offset(0, 1))
SHADOW_CARD = ft.BoxShadow(blur_radius=30, spread_radius=0, color="#00000059",
                           offset=ft.Offset(0, 8))

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

# ==================== 圆角 Radius ====================
RADIUS_CIRCLE = 999      # 正圆/胶囊 (Container 用 999 或 尺寸/2)
RADIUS_PILL = 999
RADIUS_LG = 16           # 窗口
RADIUS_MD = 12           # 工具栏 (非产品)
RADIUS_SM = 8            # 卡片/按钮
RADIUS_XS = 6            # 输入框
RADIUS_2XS = 4           # 代码标签

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

# ==================== 字体族 ====================
FONT_CN = "HarmonyOS Sans SC"   # HTML 事实源同款 (docs/fonts/sc 自托管 woff2; 2026-08 装系统版 ttf 用户级)
FONT_MONO = "JetBrains Mono"    # HTML 事实源同款 (2026-08 装系统版)
