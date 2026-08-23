"""汤圆启动器 UI 组件库 — 与 docs/design-system.md 组件索引一一对应。

规则 (docs/rules.md):
- 产品 UI 只能用本模块组件构建; 禁止在页面代码堆砌"伪组件"
- 禁止新建组件; 确需新建须登记 design-system.md (例外通道)
- 颜色一律引用 flet_app.theme, 禁止硬编码色值
"""
import flet as ft

from flet_app.theme import (
    COL_BG_CARD,
    COL_BG_CARD_2,
    COL_BG_DEEP,
    COL_BG_GHOST,
    COL_BG_GHOST_2,
    COL_BG_GHOST_3,
    COL_BG_INPUT,
    COL_BORDER_BRAND,
    COL_BORDER_SUBTLE,
    COL_BORDER_VISIBLE,
    COL_BRAND,
    COL_BRAND_BG_10,
    COL_BRAND_BG_15,
    COL_BRAND_BG_18,
    COL_BRAND_BG_20,
    COL_BRAND_HOVER,
    COL_BRAND_LIGHT,
    COL_ERR,
    COL_OK,
    COL_TEXT_DIM,
    COL_TEXT_MUTED,
    COL_TEXT_PRIMARY,
    COL_TEXT_SECONDARY,
    COL_WARN,
    FONT_10,
    FONT_11,
    FONT_12,
    FONT_14,
    FONT_15,
    FONT_18,
    FONT_36,
    FONT_44,
    FONT_MONO,
    H_BTN_RUN,
    H_INPUT,
    RADIUS_PILL,
    S_AVATAR,
    S_BTN_LAUNCH,
    SHADOW_BTN,
    SHADOW_BTN_HOVER,
    SPACE_6,
    SPACE_8,
    SPACE_10,
    SPACE_12,
    SPACE_16,
)

# ---------- flet 0.86.5 兼容辅助 ----------

def _border_all(width: int, color: str) -> ft.Border:
    """四边等宽 Border (0.86.5 无 ft.border.all)"""
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def _border_top(width: int, color: str) -> ft.Border:
    return ft.Border(top=ft.BorderSide(width, color),
                     right=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                     bottom=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                     left=ft.BorderSide(0, ft.Colors.TRANSPARENT))


def _pad(h: int | None = None, v: int | None = None) -> ft.Padding:
    """水平/垂直 padding (0.86.5 无 ft.padding.symmetric)"""
    return ft.Padding(left=h or 0, right=h or 0, top=v or 0, bottom=v or 0)


# ==================== 3. 版本徽章 VersionTag ====================
def version_tag(text: str) -> ft.Container:
    """版本徽章: 主页标题栏左端。props: text"""
    return ft.Container(
        content=ft.Text(text, size=FONT_10, weight=ft.FontWeight.W_700,
                        color=COL_BRAND_LIGHT, font_family=FONT_MONO),
        bgcolor=COL_BRAND_BG_20,
        border=_border_all(1, COL_BORDER_BRAND),
        border_radius=RADIUS_PILL,
        padding=_pad(h=8, v=2),
    )


# ==================== 4. 窗口控制按钮 WinBtn ====================
def win_btn(icon: ft.Icons, tooltip: str, on_click=None, variant="normal") -> ft.IconButton:
    """窗口控制图标按钮。props: icon, tooltip, on_click, variant(normal/close)"""
    return ft.IconButton(
        icon=icon, icon_size=14, tooltip=tooltip, on_click=on_click,
        icon_color=COL_TEXT_MUTED,
        style=ft.ButtonStyle(
            bgcolor={"": ft.Colors.TRANSPARENT,
                     "hovered": COL_ERR if variant == "close" else COL_BG_GHOST_2},
            color={"": COL_TEXT_MUTED, "hovered": ft.Colors.WHITE},
            shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 全 UI 去圆角)
        ),
    )


# ==================== 5. 头像 Avatar ====================
def avatar(fallback_char: str, image_path: str | None = None) -> ft.Container:
    """玩家头像; 无图显示昵称首字。props: fallbackChar, image"""
    content = None
    if image_path:
        try:
            content = ft.Image(src=image_path, width=S_AVATAR, height=S_AVATAR,
                               fit=ft.BoxFit.COVER,
                               filter_quality=ft.FilterQuality.HIGH)  # 低清 avatar.dat 缩放出锯齿, HIGH 平滑 (2026-08 UI 审查)
        except Exception:  # noqa: BLE001 - 头像加载失败回退首字
            content = None
    if content is None:
        content = ft.Text(fallback_char, size=FONT_36,
                          weight=ft.FontWeight.W_700, color=COL_BRAND_LIGHT)
    return ft.Container(
        content=content,
        width=S_AVATAR, height=S_AVATAR,
        border_radius=RADIUS_PILL,
        bgcolor=COL_BG_CARD_2,
        border=_border_all(2, COL_BORDER_VISIBLE),
        alignment=ft.alignment.Alignment(0, 0),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


# ==================== 6. 昵称 Nickname ====================
def nickname(text: str, size: int = FONT_18) -> ft.Text:
    """昵称单行省略。props: text, size(默认 18, 主页大昵称传 24)"""
    return ft.Text(text, size=size, weight=ft.FontWeight.W_700,
                   color=COL_TEXT_PRIMARY, max_lines=1,
                   overflow=ft.TextOverflow.ELLIPSIS)


# ==================== 7. 服务器状态胶囊 ServerMonitor ====================
class ServerMonitor(ft.Row):
    """服务器在线状态胶囊。props: status(online/offline), label, count。

    ⚠ 数据红线: count 必须来自 A2S 真实查询; offline 时隐藏人数 (rules.md §4.2)。
    """

    def __init__(self, label="在线", count="", status="online"):
        self._dot = ft.Container(width=8, height=8, border_radius=RADIUS_PILL,
                                 bgcolor=COL_OK)
        # label 用 text-muted 而非 text-dim: 灰字对比度实测偏低 (~2:1),
        # 提亮一档保证低亮度屏可读 (2026-08 UI 审查落地, design-system #7 已同步)
        self._label = ft.Text(label, size=FONT_15, color=COL_TEXT_MUTED,
                              font_family=FONT_MONO)
        self._count = ft.Text(count, size=FONT_15, weight=ft.FontWeight.W_600,
                              color=COL_TEXT_SECONDARY, font_family=FONT_MONO)
        self._container = ft.Container(
            content=ft.Row([self._dot, self._label, self._count], spacing=7),
            padding=_pad(h=12, v=5),
            border_radius=RADIUS_PILL,
            bgcolor=COL_BG_GHOST,
            border=_border_all(1, COL_BORDER_SUBTLE),
        )
        self._status = status
        # 按初始 status 应用点色/人数 (offline=灰点隐藏人数, online=绿点显示)
        if status == "offline":
            self._dot.bgcolor = COL_TEXT_DIM
            self._count.visible = False
        else:
            self._dot.bgcolor = COL_OK
            self._count.visible = True
        # tight=True: Row 收缩到内容宽度 (0.86.5 无 mainAxisSize), 否则撑满父容器
        # 导致 Column 的 horizontal_alignment=CENTER 失效, 胶囊靠左 (用户反馈 2026-08)
        super().__init__([self._container], spacing=0, tight=True)

    def set_status(self, status: str, label: str, count: str):
        """在线: 绿点+人数; 离线: 灰点+隐藏人数"""
        self._status = status
        self._label.value = label
        if status == "offline":
            self._dot.bgcolor = COL_TEXT_DIM
            self._count.value = ""
            self._count.visible = False
        else:
            self._dot.bgcolor = COL_OK
            self._count.value = count
            self._count.visible = True
        self.update()


# ==================== 8. 启动按钮 LaunchButton ====================
class LaunchButton(ft.Container):
    """主页主操作: 110px 圆形纯图标启动按钮。props: state(idle/launching/running)。

    状态机: idle(主色) → launching(主色hover) → running(成功绿+辉光) → idle
    点击由 on_click 处理 (业务逻辑在 main.py, 本组件只提供样式/状态切换)。
    """

    def __init__(self, on_click=None, tooltip="启动游戏"):
        self._icon = ft.Icon(ft.Icons.ROCKET_LAUNCH, size=FONT_44,
                             color=ft.Colors.WHITE)
        self._state = "idle"
        super().__init__(
            content=self._icon,
            width=S_BTN_LAUNCH, height=S_BTN_LAUNCH,
            border_radius=RADIUS_PILL,
            bgcolor=COL_BRAND,
            alignment=ft.alignment.Alignment(0, 0),
            shadow=SHADOW_BTN,
            tooltip=tooltip,
            on_click=on_click,
            on_hover=self._on_hover,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _on_hover(self, e):
        if self._state == "launching":
            return
        if e.data == "true":
            self.bgcolor = COL_BRAND_HOVER
            self.shadow = SHADOW_BTN_HOVER
        else:
            self.bgcolor = COL_BRAND
            self.shadow = SHADOW_BTN
        self.update()

    def set_state(self, state: str, tooltip: str | None = None):
        self._state = state
        if state == "launching":
            self.bgcolor = COL_BRAND_HOVER
        elif state == "running":
            self.bgcolor = COL_OK
        else:
            self.bgcolor = COL_BRAND
            self.shadow = SHADOW_BTN
            # idle 显式复位 tooltip, 否则残留"游戏运行中" (deep-review 7轮 F5)
            self.tooltip = tooltip or "启动游戏"
        if tooltip:
            self.tooltip = tooltip
        self.update()


# ==================== 15. 代码键名标签 CodeTag ====================
def code_tag(text: str) -> ft.Container:
    """代码键名标签。props: text"""
    return ft.Container(
        content=ft.Text(text, size=FONT_10, color=COL_BRAND,
                        font_family=FONT_MONO),
        bgcolor=COL_BRAND_BG_10,
        # 矩形 (2026-08 全 UI 去圆角; 原 RADIUS_2XS)
        padding=_pad(h=6, v=2),
    )


# ==================== 12. 页头 PageHead ====================
def page_head(code: str, title: str, desc: str = "") -> ft.Container:
    """编辑页页头: 代码键名 kicker + 标题 + 描述。props: code, title, desc。
    (deep-review 7轮 F4: 原 build_page/build_tools_page 内联重复堆砌, 抽组件)"""
    return ft.Container(
        content=ft.Column([
            ft.Text(f"// CFG.{code.upper()}", size=11, color=COL_BRAND_LIGHT,
                    opacity=0.8, font_family=FONT_MONO),
            ft.Text(title, size=20, weight=ft.FontWeight.W_800),
            ft.Text(desc, size=12, color=COL_TEXT_DIM, opacity=0.85) if desc else ft.Text(""),
        ], spacing=4),
        padding=ft.padding.Padding(left=18, top=10, right=18, bottom=14))


# ==================== 13. 字段网格 FieldGrid ====================
def field_grid(fields, build_row, spacing: int = 10,
               header: ft.Control | None = None) -> ft.ListView:
    """双列字段网格: 每行两个卡片等高, 奇数个末行单卡。props: fields(数据列表),
    build_row(单卡构建回调), spacing, header(可选页头控件, 置于网格上方)。
    (deep-review 7轮 F4: 原 build_page 内联双列循环, 抽组件;
    STRETCH 在 ListView 无界高度下塌陷 → 等高靠内容统一 + 固定行高)"""
    rows = []
    for i in range(0, len(fields), 2):
        pair = [build_row(f) for f in fields[i:i + 2]]
        if len(pair) == 1:
            rows.append(pair[0])
        else:
            rows.append(ft.Row([
                ft.Container(pair[0], expand=True),
                ft.Container(width=10),
                ft.Container(pair[1], expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
    controls = ([header] if header is not None else []) + rows
    return ft.ListView(controls=controls,
                       padding=ft.padding.Padding(left=20, top=20, right=20, bottom=40),
                       expand=True, spacing=spacing)


# ==================== 14. 配置卡片 ConfigCard ====================
def config_card(title: str, desc: str, control, tag: str | None = None,
                on_hover_shift=True, title_expand=False,
                desc_lines: int = 0) -> ft.Container:
    """设置项卡片。props: title, desc, control, tag(可选 CodeTag)。

    on_hover_shift: 双列网格内 False (hover 不右移, 见 design-system.md #14)。
    title_expand: 标题占满剩余宽度 (键名徽章贴右)。
    desc_lines: >0 时描述固定行高容器 (双列等高, main.py 用 2)。
    """
    title_row = ft.Row([
        ft.Text(title, size=FONT_14, weight=ft.FontWeight.W_700,
                color=COL_TEXT_PRIMARY, expand=title_expand),
        code_tag(tag) if tag else ft.Container(),
    ], spacing=SPACE_8)
    desc_text = ft.Text(desc, size=FONT_12, color=COL_TEXT_DIM,
                        max_lines=desc_lines or None,
                        overflow=ft.TextOverflow.ELLIPSIS if desc_lines else None)
    if desc_lines:
        # 固定行高容器: 双列卡等高 (2 行 × 18px = 36px, main.py 同款)
        desc_box: ft.Control = ft.Container(
            content=desc_text, height=desc_lines * 18,
            alignment=ft.alignment.Alignment(-1, 0))
    else:
        desc_box = desc_text
    top = ft.Column([
        title_row,
        desc_box,
    ], spacing=2)
    card = ft.Container(
        content=ft.Column([top, control], spacing=SPACE_10),
        padding=SPACE_16,
        # 矩形 (2026-08 用户决策去圆角, 全 UI 卡片直角)
        bgcolor=COL_BG_CARD,
        border=_border_all(1, COL_BORDER_SUBTLE),
    )

    def _hover(e):
        if e.data == "true":
            card.bgcolor = COL_BG_GHOST_2
            card.border = _border_all(1, COL_BORDER_BRAND)
        else:
            card.bgcolor = COL_BG_CARD
            card.border = _border_all(1, COL_BORDER_SUBTLE)
        card.update()

    card.on_hover = _hover
    return card


# ==================== 16. 输入框 InputDark ====================
def input_dark(value="", placeholder="", mono=False, multiline=False,
               height=H_INPUT, font_size=FONT_14, width=None,
               on_change=None, max_length=None, text_align=None,
               min_lines: int = 4, max_lines: int = 12) -> ft.TextField:
    """文本输入框。props: value, placeholder, mono, multiline, height, font_size,
    width(固定宽, 字段卡内 236), on_change, max_length, text_align,
    min_lines/max_lines(multiline 时行数, 加载器启动命令卡用 3/6)"""
    return ft.TextField(
        value=value, hint_text=placeholder, multiline=multiline,
        min_lines=min_lines if multiline else 1,
        max_lines=max_lines if multiline else 1,
        height=None if multiline else height,
        width=width,
        text_size=font_size,
        bgcolor=COL_BG_INPUT,
        border=ft.InputBorder.OUTLINE,
        border_color=COL_BORDER_VISIBLE,
        focused_border_color=COL_BRAND,
        content_padding=_pad(h=12, v=10),
        # 矩形 (2026-08 全 UI 去圆角; 原 RADIUS_XS)
        border_radius=0,
        text_style=ft.TextStyle(color=COL_TEXT_PRIMARY,
                                font_family=FONT_MONO if mono else None),
        hint_style=ft.TextStyle(color=COL_TEXT_DIM),
        on_change=on_change,
        max_length=max_length,
        text_align=text_align or ft.TextAlign.LEFT,
    )


# ==================== 17. 下拉框 SelectDark ====================
def select_dark(options, selected=None, placeholder="", width=None, height=None,
                on_select=None, filled=False, fill_color=None,
                border_color=COL_BORDER_VISIBLE) -> ft.Dropdown:
    """选项下拉框。props: options, selected, placeholder, width, height, on_select,
    filled/fill_color(0.86.5 Dropdown 必须 filled=True 才绘制 fill_color),
    border_color(字段卡内用 INPUT_BORDER 等价 COL_BORDER_VISIBLE)。
    options 兼容两种输入: 字符串列表(自动包 Option)或已构建的 Option 列表
    (main.py rank/combo 分支传 Option, 直接透传——双重包装会让下拉全坏,
    deep-review 7轮 task-4 迟到发现 HIGH)"""
    return ft.Dropdown(
        options=[o if isinstance(o, ft.dropdown.Option) else ft.dropdown.Option(o)
                 for o in options],
        value=selected,
        width=width,
        height=height,
        text_size=FONT_14,
        color=COL_TEXT_PRIMARY,
        bgcolor=COL_BG_INPUT,
        border_color=border_color,
        focused_border_color=COL_BRAND,
        # 矩形 (2026-08 全 UI 去圆角; 原 RADIUS_XS)
        border_radius=0,
        content_padding=_pad(h=12),
        hint_text=placeholder,
        on_select=on_select,
        filled=filled,
        fill_color=fill_color,
    )


# ==================== 18. 推荐项 Chip ====================
class Chip(ft.Container):
    """可点击标签, 点击切换 added 态(前缀 ✓)。props: label, added

    竖排时须置于 horizontal_alignment=STRETCH 的 Column 内 (单行省略防溢出,
    design-system.md #18)。
    """

    def __init__(self, label, added=False, on_toggle=None):
        self._label = label
        self._added = added
        self._text = ft.Text(("✓ " if added else "") + label, size=FONT_11,
                             color=COL_BRAND_LIGHT if added else COL_TEXT_MUTED,
                             font_family=FONT_MONO, max_lines=1,
                             overflow=ft.TextOverflow.ELLIPSIS)
        super().__init__(
            content=self._text,
            padding=_pad(h=10, v=5),
            # 方形 (2026-08 用户决策: 推荐启动项胶囊改方形; 原 RADIUS_PILL)
            bgcolor=COL_BRAND_BG_18 if added else COL_BG_GHOST,
            border=_border_all(1, COL_BORDER_BRAND if added else COL_BORDER_VISIBLE),
            on_click=lambda e: self.toggle(),
            ink=False,
        )
        self._on_toggle = on_toggle

    def set_added(self, added: bool):
        """外部同步 added 态 (加载器 _sync_chips 用): 不触发 on_toggle"""
        self._added = added
        self._text.value = ("✓ " if added else "") + self._label
        self._text.color = COL_BRAND_LIGHT if added else COL_TEXT_MUTED
        self.bgcolor = COL_BRAND_BG_18 if added else COL_BG_GHOST
        self.border = _border_all(1, COL_BORDER_BRAND if added else COL_BORDER_VISIBLE)

    def toggle(self):
        self._added = not self._added
        self.set_added(self._added)
        self.update()
        if self._on_toggle:
            self._on_toggle(self._label, self._added)


# ==================== 22. 类别标签 CatTag ====================
def cat_tag(text: str) -> ft.Container:
    """工具类别标签。props: text"""
    return ft.Container(
        content=ft.Text(text, size=FONT_10, weight=ft.FontWeight.W_600,
                        color=COL_BRAND_LIGHT),
        bgcolor=COL_BRAND_BG_15,
        border=_border_all(1, COL_BORDER_BRAND),
        # 矩形 (2026-08 全 UI 去圆角; 原 RADIUS_2XS)
        padding=_pad(h=8, v=2),
    )


# ==================== 23. 风险标签 RiskTag ====================
# key 兼容中英文: REPAIR_TOOLS 的 risk 是中文 (低/中/高, app/tools.py),
# design-system.md #23 记 low/mid/high — 两套都收, 未知 key 回退"低" (deep-review 5轮 LOW-8)
_RISK_COLORS = {"low": COL_OK, "mid": COL_WARN, "high": COL_ERR,
                "低": COL_OK, "中": COL_WARN, "高": COL_ERR}


def risk_tag(level: str, text: str | None = None) -> ft.Text:
    """工具风险等级。props: level(低/中/高 或 low/mid/high)"""
    label = text or {"low": "风险:低", "mid": "风险:中", "high": "风险:高",
                     "低": "风险:低", "中": "风险:中", "高": "风险:高"}.get(level, "风险:低")
    return ft.Text(label, size=FONT_11, weight=ft.FontWeight.W_600,
                   color=_RISK_COLORS.get(level, COL_OK))


# ==================== 24. 运行按钮 RunButton ====================
class RunButton(ft.FilledButton):
    """工具运行按钮。props: label, disabled, icon(play/clock)"""

    def __init__(self, on_click=None):
        self._label = ft.Text("运行", size=FONT_12, weight=ft.FontWeight.W_700,
                              color=ft.Colors.WHITE)
        self._icon = ft.Icon(ft.Icons.PLAY_ARROW, size=14, color=ft.Colors.WHITE)
        super().__init__(
            content=ft.Row([self._icon, self._label], spacing=5),
            height=H_BTN_RUN,
            style=ft.ButtonStyle(
                bgcolor=COL_BRAND,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
            ),
            on_click=on_click,
        )
        # 0.86.5 ButtonStyle 无 hover 态, 手动切换 bgcolor (main.py 同模式)
        self._base_style = self.style
        self.on_hover = self._on_hover

    def _on_hover(self, e):
        if self.disabled:
            return
        self.style = ft.ButtonStyle(
            bgcolor=COL_BRAND_HOVER if e.data == "true" else COL_BRAND,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=0),  # 矩形 (2026-08 去圆角)
        )
        self.update()

    def set_busy(self, busy: bool):
        self.disabled = busy
        self._icon.name = ft.Icons.HOURGLASS_TOP if busy else ft.Icons.PLAY_ARROW
        self._label.value = "运行中" if busy else "运行"
        self.update()


# ==================== 25. 工具状态 ToolStatus ====================
_STATUS_COLORS = {"idle": COL_TEXT_DIM, "running": COL_WARN,
                  "ok": COL_OK, "fail": COL_ERR}


def tool_status(state="idle", text="待运行") -> ft.Text:
    """工具运行状态。props: state(idle/running/ok/fail), text"""
    return ft.Text(text, size=FONT_11, color=_STATUS_COLORS[state],
                   text_align=ft.TextAlign.RIGHT)


# ==================== 19. 推荐面板 RecPanel ====================
def rec_panel(chips, title: str = "推荐启动项", expand: int = 2) -> ft.Container:
    """推荐项面板 (design-system.md #19): 竖排 chips 单行省略。
    props: chips(ft.Container 列表), title, expand(Row 内分栏比例, LaunchSplit 右栏 2)。
    (deep-review 7轮 F4: 原 textarea 分支内联堆砌, 抽组件)"""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=11, weight=ft.FontWeight.W_600,
                    color=COL_TEXT_MUTED),
            ft.Column(chips, spacing=6,
                      horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        ], spacing=8),
        bgcolor=COL_BG_GHOST_3,
        border=_border_all(1, COL_BORDER_SUBTLE),
        # 矩形 (2026-08 用户决策去圆角)
        padding=SPACE_12,
        expand=expand,
    )


# ==================== 20. 启动分栏 LaunchSplit ====================
def launch_split(ta, rec: ft.Control, gap_width: int = 14) -> ft.Row:
    """启动命令 3:2 分栏 (design-system.md #20): 左=textarea(expand 3),
    右=RecPanel(expand 2)。props: ta(TextField), rec(RecPanel), gap_width。
    (deep-review 7轮 F4: 原内联 ft.Row 3:2 分栏, 抽组件)"""
    ta.expand = 3
    return ft.Row([
        ta,
        ft.Container(width=gap_width),
        rec,
    ], expand=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)


# ==================== 21. 工具卡片 ToolCard ====================
def tool_card(cat: str, risk: str, name: str, on_run=None,
              expand: bool = False) -> ft.Container:
    """修复工具卡片。props: cat(类别), risk(低/中/高 或 low/mid/high), name, onRun, expand。

    结构: 顶行(类别+风险|运行按钮) → 工具名 → 状态文本 (design-system.md #21)。
    返回的 Container 附带 `_run_btn`(RunButton) 与 `_status`(ToolStatus) 引用,
    供调用方驱动运行中/完成/失败状态 (make_runner 用)。
    expand: 2×2 网格内等宽 (Row 内占满半宽)。
    """
    run_btn = RunButton(on_run)
    status = tool_status()
    top = ft.Row([
        ft.Row([cat_tag(cat), risk_tag(risk)], spacing=SPACE_8),
        run_btn,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    card = ft.Container(
        content=ft.Column([
            top,
            ft.Text(name, size=FONT_14, weight=ft.FontWeight.W_700,
                    color=COL_TEXT_PRIMARY),
            status,
        ], spacing=SPACE_6),
        padding=SPACE_16,
        # 矩形 (2026-08 用户决策去圆角)
        bgcolor=COL_BG_CARD,
        border=_border_all(1, COL_BORDER_SUBTLE),
        expand=expand,
    )

    def _hover(e):
        if e.data == "true":
            card.border = _border_all(1, COL_BORDER_BRAND)
        else:
            card.border = _border_all(1, COL_BORDER_SUBTLE)
        card.update()

    card.on_hover = _hover
    card._run_btn = run_btn  # type: ignore[attr-defined]
    card._status = status  # type: ignore[attr-defined]
    return card


# ==================== 27. 编码切换 EncGroup ====================
def enc_group(segments, selected, on_change=None) -> ft.Container:
    """编码切换 (design-system.md #27, HTML .enc-group 结构)。

    2026-08 UI 审查: 原 ft.SegmentedButton 的 style 只能整体应用(选中/未选中
    无法分离, 亮蓝实心被用户反馈"难看", 状态字典在 0.86.5 上失效回退 M3 默认)
    → 自绘: ghost 底容器 + 分段按钮, 选中段 = 20% 主色浅底 + 主色浅字,
    未选中 = 透明 + 灰字 (与 chip 已添加态/导航激活态同一视觉语言)。
    props: segments([(value, label), ...]), selected(当前值), on_change(value)。
    """
    state = {"sel": selected}
    btns: list[ft.Container] = []

    def _render():
        for (value, _), btn in zip(segments, btns):
            active = value == state["sel"]
            btn.bgcolor = COL_BRAND_BG_20 if active else ft.Colors.TRANSPARENT
            btn.border = _border_all(1, COL_BORDER_BRAND if active else ft.Colors.TRANSPARENT)
            btn.content.color = COL_BRAND_LIGHT if active else COL_TEXT_DIM  # type: ignore[union-attr]

    def _set(v):
        if v == state["sel"]:
            return
        state["sel"] = v
        _render()
        if on_change:
            on_change(v)

    for value, label in segments:
        btn = ft.Container(
            content=ft.Text(label, size=FONT_11, weight=ft.FontWeight.W_600,
                            color=COL_TEXT_DIM),
            padding=_pad(h=12, v=5),
            # 矩形 (2026-08 全 UI 去圆角; 原 RADIUS_XS)
            on_click=lambda e, v=value: _set(v),
            ink=False,
        )
        btns.append(btn)
    _render()
    return ft.Container(
        content=ft.Row(btns, spacing=2),
        bgcolor=COL_BG_GHOST,   # HTML .enc-group rgba(255,255,255,0.05)
        border=_border_all(1, COL_BORDER_SUBTLE),
        # 矩形 (2026-08 用户决策去圆角)
        padding=_pad(h=3, v=3),
    )


# ==================== 26. 状态栏 StatusBar ====================
def status_bar(enc_selector, status_msg: ft.Text | None = None,
               status_icon: ft.Icon | None = None) -> ft.Container:
    """编辑页底部状态栏: 左=状态图标+消息(可选), 右=编码切换。props: encSelector, statusMsg, statusIcon

    status_msg: 可选状态文本 (加载/保存错误临时显示, main.py set_status 用); None 时仅图标。
    status_icon: 可选状态图标控件 (main.py 持有引用, 错误时切 ERROR 红图标);
                 None 时内部创建默认绿勾。常态"仅图标"由调用方传空 status_msg 保证
                 (design-system.md #26, 2026-08 UI 审查落地)。
    """
    left = [status_icon if status_icon is not None
            else ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=COL_OK)]
    if status_msg is not None:
        left.append(status_msg)
    return ft.Container(
        content=ft.Row([
            *left,
            ft.Container(expand=True),
            enc_selector,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        height=64,
        padding=_pad(h=SPACE_16),
        bgcolor=COL_BG_DEEP,   # HTML 事实源 .statusbar 用 var(--bg-deep) (deep-review 5轮修正)
        border=_border_top(1, COL_BORDER_SUBTLE),
    )
