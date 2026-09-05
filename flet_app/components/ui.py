"""汤圆启动器 UI 组件库 — 与 docs/design-system.md 组件索引一一对应。

规则 (docs/rules.md):
- 产品 UI 只能用本模块组件构建; 禁止在页面代码堆砌"伪组件"
- 禁止新建组件; 确需新建须登记 design-system.md (例外通道)
- 颜色一律引用 flet_app.theme, 禁止硬编码色值
"""
import threading
import time
import types

import flet as ft

from flet_app import theme

# 颜色/阴影一律 theme.COL_X 属性动态访问 (v2.3.0 深浅换装: from-import 会冻结
# 启动时的深色值)。此处仅保留与主题无关的静态令牌。
from flet_app.theme import (
    CROP_MIN,
    FONT_10,
    FONT_11,
    FONT_12,
    FONT_13,
    FONT_14,
    FONT_15,
    FONT_18,
    FONT_20,
    FONT_36,
    FONT_44,
    FONT_MONO,
    H_BTN_AV,
    H_BTN_RUN,
    H_INPUT,
    RADIUS_CARD,
    RADIUS_CTRL,
    RADIUS_PILL,
    S_AVATAR,
    S_BTN_LAUNCH,
    S_CROP_CANVAS,
    S_CROP_HANDLE,
    S_PREVIEW_AVATAR,
    SPACE_6,
    SPACE_8,
    SPACE_10,
    SPACE_12,
    SPACE_16,
)

# ---------- flet 0.86.5 兼容辅助 ----------

def _is_hovered(e) -> bool:
    """on_hover 事件 data 兼容: flet 0.86.5 传真布尔, 旧版本传字符串 'true'/'false'。
    (0.86.5 存量缺陷: 按 "true" 字符串比较使全部 hover 处理器恒走 else 分支)"""
    return e.data is True or e.data == "true"


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
    """版本徽章: 主页标题栏左端。props: text
    (v2.3.1 三轮去 mono: 版本号属界面文字, 改 font-cn)"""
    return ft.Container(
        content=ft.Text(text, size=FONT_10, weight=ft.FontWeight.W_700,
                        color=theme.COL_BRAND_LIGHT),
        bgcolor=theme.COL_BRAND_BG_20,
        border=_border_all(1, theme.COL_BORDER_BRAND),
        border_radius=RADIUS_PILL,
        padding=_pad(h=8, v=2),
    )


# ==================== 4. 窗口控制按钮 WinBtn ====================
def win_btn(icon: ft.Icons, tooltip: str, on_click=None, variant="normal") -> ft.IconButton:
    """窗口控制图标按钮。props: icon, tooltip, on_click, variant(normal/close)
    显式 28×28 (W_BTN_WIN 档): IconButton 默认最小 40×40, 主页 5 钮会撑出
    360px 标题栏把「关闭」裁掉 (2026-08-30 实机验收发现)。"""
    return ft.IconButton(
        icon=icon, icon_size=14, tooltip=tooltip, on_click=on_click,
        width=28, height=28,
        icon_color=theme.COL_TEXT_MUTED,
        style=ft.ButtonStyle(
            bgcolor={"": ft.Colors.TRANSPARENT,
                     "hovered": theme.COL_ERR if variant == "close" else theme.COL_WINBTN_HOVER},
            color={"": theme.COL_TEXT_MUTED, "hovered": ft.Colors.WHITE},
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CTRL),  # Win11 控件档 4px (v2.3.1)
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
                          weight=ft.FontWeight.W_700, color=theme.COL_BRAND_LIGHT)
    return ft.Container(
        content=content,
        width=S_AVATAR, height=S_AVATAR,
        border_radius=RADIUS_PILL,
        bgcolor=theme.COL_BG_CARD_2,
        border=_border_all(2, theme.COL_BORDER_VISIBLE),
        alignment=ft.alignment.Alignment(0, 0),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


# ==================== 6. 昵称 Nickname ====================
def nickname(text: str, size: int = FONT_18) -> ft.Text:
    """昵称单行省略。props: text, size(默认 18, 主页大昵称传 24)"""
    return ft.Text(text, size=size, weight=ft.FontWeight.W_700,
                   color=theme.COL_TEXT_PRIMARY, max_lines=1,
                   overflow=ft.TextOverflow.ELLIPSIS)


# ==================== 7. 服务器状态胶囊 ServerMonitor ====================
class ServerMonitor(ft.Row):
    """服务器在线状态胶囊。props: status(online/offline), label, count,
    on_hover_change(bool 回调, ServerPanel 展开/收起触发, main.py 接线)。

    在线点呼吸 dot-breathe (tokens.md §7): 2s 周期 opacity 1↔0.55,
    全页唯一循环动画 (rules.md §4.6); 右侧淡 chevron 悬停旋转 180°。
    ⚠ 数据红线: count 必须来自状态 API 真实查询; offline 时隐藏人数 (rules.md §4.2)。
    """

    def __init__(self, label="在线", count="", status="online", on_hover_change=None):
        self.on_hover_change = on_hover_change
        self._status = status
        self._breathe_alive = True
        self._ever_attached = False   # 是否曾挂上 page (区分"构建初期未挂载"与"已被重建分离")
        self._hovered = False
        self._dot = ft.Container(
            width=8, height=8, border_radius=RADIUS_PILL,
            bgcolor=theme.COL_OK, shadow=theme.SHADOW_DOT_ONLINE,
            animate_opacity=ft.Animation(1000, theme.EASE_STANDARD),
        )
        # label 用 text-muted 而非 text-dim: 灰字对比度实测偏低 (~2:1),
        # 提亮一档保证低亮度屏可读 (2026-08 UI 审查落地, design-system #7 已同步)
        self._label = ft.Text(label, size=FONT_15, color=theme.COL_TEXT_MUTED)
        self._count = ft.Text(count, size=FONT_15, weight=ft.FontWeight.W_600,
                              color=theme.COL_TEXT_SECONDARY)
        # 淡 chevron (悬停提示可展开 ServerPanel; 悬停旋转 180°)
        self._chev = ft.Container(
            content=ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=12,
                            color=theme.COL_TEXT_DIM),
            margin=ft.margin.Margin(left=2, top=0, right=0, bottom=0),
            animate_rotation=ft.Animation(theme.MOTION_FAST, theme.EASE_STANDARD),
            rotate=ft.Rotate(0),
        )
        self._container = ft.Container(
            content=ft.Row([self._dot, self._label, self._count, self._chev], spacing=7),
            padding=_pad(h=12, v=5),
            border_radius=RADIUS_PILL,
            bgcolor=theme.COL_BG_GHOST,
            border=_border_all(1, theme.COL_BORDER_SUBTLE),
            on_hover=self._on_hover,
        )
        # 按初始 status 应用点色/人数 (offline=灰点隐藏人数, online=绿点呼吸)
        if status == "offline":
            self._apply_offline_dot()
            self._count.visible = False
        else:
            self._count.visible = True
            self._start_breathe()
        # tight=True: Row 收缩到内容宽度 (0.86.5 无 mainAxisSize), 否则撑满父容器
        # 导致 Column 的 horizontal_alignment=CENTER 失效, 胶囊靠左 (用户反馈 2026-08)
        super().__init__([self._container], spacing=0, tight=True)

    # ---- 呼吸循环 (dot-breathe, 全页唯一循环动画) ----
    def _start_breathe(self):
        threading.Thread(target=self._breathe_loop, daemon=True).start()

    def _breathe_loop(self):
        while self._breathe_alive:
            time.sleep(1.0)
            if not self._breathe_alive or self._status != "online":
                continue
            page = self.page
            if page is None:
                # 曾挂上 page 后变 None = 已随换装重建/页面关闭: 自停线程, 防泄漏
                # (原 continue 空转, 每次换装泄漏一条每秒空转的线程, 2026-08-30 审查);
                # 构建初期尚未挂载 (_ever_attached=False) 则继续等待 — 否则首拍落
                # 在挂载前会永久失去呼吸动画 (2026-09-05 审查)
                if self._ever_attached:
                    self._breathe_alive = False
                continue
            self._ever_attached = True

            def _tick(self=self):
                try:
                    self._dot.opacity = 0.55 if self._dot.opacity != 0.55 else 1.0
                    self._dot.update()
                except Exception:  # noqa: BLE001 - 控件已随换装重建/页面关闭: 停线程
                    self._breathe_alive = False
            # 项目线程规则 (main.py H1): 工作线程不直改控件, 经 page.run_thread
            try:
                page.run_thread(_tick)
            except Exception:  # noqa: BLE001 - 会话已关: 停线程
                self._breathe_alive = False

    def _apply_offline_dot(self):
        self._dot.bgcolor = theme.COL_TEXT_DIM
        self._dot.shadow = None
        self._dot.opacity = 1.0

    def _on_hover(self, e):
        hovered = _is_hovered(e)
        self._hovered = hovered
        self._chev.rotate = ft.Rotate(3.14159 if hovered else 0)
        try:
            self._chev.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page 时跳过
            pass
        if self.on_hover_change:
            self.on_hover_change(hovered)

    def set_status(self, status: str, label: str, count: str):
        """在线: 绿点(呼吸)+人数; 离线: 灰点+隐藏人数"""
        self._status = status
        self._label.value = label
        if status == "offline":
            self._apply_offline_dot()
            self._count.value = ""
            self._count.visible = False
        else:
            self._dot.bgcolor = theme.COL_OK
            self._dot.shadow = theme.SHADOW_DOT_ONLINE
            self._count.value = count
            self._count.visible = True
            if not self._breathe_alive:
                self._breathe_alive = True
                self._start_breathe()
        # 与 ServerPanel.set_servers 对称: 控件已随换装重建/离开主页时静默,
        # 防状态 API 回包竞态在工作线程抛异常 (2026-09-05 审查)
        try:
            self.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page: 跳过
            pass


# ==================== 34. 服务器悬停面板 ServerPanel ====================
class ServerPanel(ft.Container):
    """悬停 ServerMonitor 胶囊展开的分服面板 (design-system.md #34)。

    形态: 覆盖层 w=264, 卡片底/圆角 8/浮层柔影; 行 = 状态点(8px) + 名称(13/600)
    + 人数(11, N / M) + 悬停行浮现 28×28「进入」钮。展开/收起动效 (panel-in) 与
    悬停保持由 main.py 接线 (on_hover + 150ms 延迟收起)。
    ⚠ 数据红线: 在线状态与人数只来自状态 API 真实查询; 拉取失败该行显示
    「获取失败」灰点, 禁止编造 (rules.md §4.2)。
    """

    def __init__(self, on_enter=None):
        self.on_enter = on_enter
        self._col = ft.Column([], spacing=2, tight=True)
        super().__init__(
            content=self._col, width=264,
            bgcolor=theme.COL_BG_CARD,
            border=_border_all(1, theme.COL_BORDER_VISIBLE),
            border_radius=RADIUS_CARD,
            shadow=theme.SHADOW_FLOAT,
            padding=_pad(h=6, v=6),
            visible=False,
        )

    def set_servers(self, rows):
        """rows: [{name, addr, status('online'|'offline'|'error'), players, maxplayers}]
        空列表 → 引导文案 (design-system #34: 去常用设置配 ConnectServer)。"""
        if not rows:
            self._col.controls = [ft.Container(
                content=ft.Text("暂无预设服务器\n可在常用设置中配置后快速进服",
                                size=FONT_12, color=theme.COL_TEXT_DIM,
                                text_align=ft.TextAlign.CENTER),
                padding=_pad(v=14),
            )]
        else:
            controls = []
            for r in rows:
                dot = ft.Container(width=8, height=8, border_radius=RADIUS_PILL)
                if r.get("status") == "online":
                    dot.bgcolor = theme.COL_OK
                    dot.shadow = theme.SHADOW_DOT_ONLINE
                    count = (f"{r.get('players') if r.get('players') is not None else '?'}"
                             f" / {r.get('maxplayers') if r.get('maxplayers') is not None else '?'}")
                elif r.get("status") == "error":
                    dot.bgcolor = theme.COL_TEXT_DIM
                    count = "获取失败"
                else:
                    dot.bgcolor = theme.COL_TEXT_DIM
                    count = "离线"
                count_text = ft.Text(count, size=FONT_11, color=theme.COL_TEXT_MUTED)
                enter = ft.Container(
                    content=ft.Icon(ft.Icons.ARROW_FORWARD, size=14,
                                    color=theme.COL_TEXT_MUTED),
                    width=28, height=28, border_radius=RADIUS_CTRL,
                    alignment=ft.alignment.Alignment(0, 0),
                    tooltip="进入服务器",
                    on_click=(lambda e, addr=r["addr"]: self.on_enter(addr))
                    if (self.on_enter and r.get("addr")) else None,
                    animate_opacity=ft.Animation(theme.MOTION_FAST, theme.EASE_STANDARD),
                    opacity=0,
                )
                row = ft.Container(
                    content=ft.Row([dot,
                                    ft.Text(r.get("name") or "", size=FONT_13,
                                            weight=ft.FontWeight.W_600,
                                            color=theme.COL_TEXT_PRIMARY,
                                            expand=True, max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS),
                                    count_text, enter],
                                   spacing=8),
                    padding=_pad(h=10, v=8),
                    border_radius=RADIUS_CTRL,
                    on_hover=lambda e, btn=enter: self._row_hover(e, btn),
                )
                controls.append(row)
            self._col.controls = controls
        try:
            self.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page 时跳过 (换装重建期)
            pass

    @staticmethod
    def _row_hover(e, btn):
        hovered = _is_hovered(e)
        e.control.bgcolor = theme.COL_BG_GHOST if hovered else None
        btn.opacity = 1 if hovered else 0
        try:
            e.control.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page 时跳过
            pass


# ==================== 8. 启动按钮 LaunchButton ====================
class LaunchButton(ft.Container):
    """主页主操作: 110px 圆形纯图标启动按钮。props: state(idle/launching/running)。

    状态机: idle(主色) → launching(主色hover) → running(成功绿+辉光) → idle
    点击由 on_click 处理 (业务逻辑在 main.py, 本组件只提供样式/状态切换)。
    动效: hover 变色+阴影加深 (上移 -2px 试做后降级, 见 _on_hover 留档);
    启动中火箭抖动 rocket-nudge (tokens.md §7): 0.45s×2 有限次非循环。
    """

    # 抖动关键帧 (角度 deg): HTML rocket-nudge 含 translateX±2 + rotate±6;
    # offset 分量已降级删去 (offset 位移动画实机破坏布局, 批次④留档), 保留旋转
    _NUDGE_SEQ = ((-6,), (6,), (0,), (-6,), (6,), (0,))
    _NUDGE_STEP = 0.225   # 每关键帧 225ms → 单周期 0.45s (tokens §7 rocket-nudge 0.45s×2)

    def __init__(self, on_click=None, tooltip="启动游戏"):
        self._icon = ft.Icon(ft.Icons.ROCKET_LAUNCH, size=FONT_44,
                             color=ft.Colors.WHITE)
        self._state = "idle"
        self._nudging = False
        # 火箭载体盒: 抖动只动 offset/rotate (rules §4.6 动效纪律)
        self._icon_box = ft.Container(
            content=self._icon,
            animate=ft.Animation(int(self._NUDGE_STEP * 1000), theme.EASE_STANDARD),
            rotate=ft.Rotate(0),
        )
        super().__init__(
            content=self._icon_box,
            width=S_BTN_LAUNCH, height=S_BTN_LAUNCH,
            border_radius=RADIUS_PILL,
            bgcolor=theme.COL_BRAND,
            alignment=ft.alignment.Alignment(0, 0),
            shadow=theme.SHADOW_BTN,
            tooltip=tooltip,
            on_click=on_click,
            on_hover=self._on_hover,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _on_hover(self, e):
        if self._state == "launching":
            return
        if _is_hovered(e):
            self.bgcolor = theme.COL_BRAND_HOVER
            self.shadow = theme.SHADOW_BTN_HOVER
            # hover 上移 -2px 已试做并降级 (批次④留档): 通用 animate + offset 在
            # flet 0.86.5 实机上会永久破坏 Column 布局 (按钮叠到头像), 移除位移,
            # 只保留变色 + 阴影加深 (HTML hover 语义的可用子集)
        else:
            self.bgcolor = theme.COL_BRAND
            self.shadow = theme.SHADOW_BTN
        self.update()

    def _nudge(self):
        """启动中火箭抖动: 有限 2 周期非循环; 状态切走立即终止。"""
        page = self.page
        if page is None:
            return
        self._nudging = True
        seq = self._NUDGE_SEQ

        def _step(i):
            if not self._nudging:
                return
            (deg,) = seq[i]
            try:
                self._icon_box.rotate = ft.Rotate(deg * 3.14159265 / 180)
                self._icon_box.update()
            except Exception:  # noqa: BLE001 - 控件已重建: 终止序列
                self._nudging = False

        for k in range(len(seq)):
            threading.Timer(self._NUDGE_STEP * k,
                            lambda k=k: page.run_thread(lambda k=k: _step(k))).start()
        threading.Timer(self._NUDGE_STEP * len(seq),
                        lambda: page.run_thread(self._nudge_end)).start()

    def _nudge_end(self):
        self._nudging = False
        try:
            self._icon_box.rotate = ft.Rotate(0)
            self._icon_box.update()
        except Exception:  # noqa: BLE001, S110 - 控件已重建: 静默
            pass

    def set_state(self, state: str, tooltip: str | None = None):
        self._state = state
        if state == "launching":
            self.bgcolor = theme.COL_BRAND_HOVER
            self._nudge()
        elif state == "running":
            self.bgcolor = theme.COL_OK
            # 已启动绿辉光 (HTML: 0 4px 20px var(--launch-glow), tokens §1.6)
            self.shadow = ft.BoxShadow(blur_radius=20, spread_radius=0,
                                       color=theme.COL_LAUNCH_GLOW,
                                       offset=ft.Offset(0, 4))
            self._nudging = False
        else:
            self.bgcolor = theme.COL_BRAND
            self.shadow = theme.SHADOW_BTN
            self._nudging = False
            # idle 显式复位 tooltip, 否则残留"游戏运行中" (deep-review 7轮 F5)
            self.tooltip = tooltip or "启动游戏"
        if tooltip:
            self.tooltip = tooltip
        self.update()


# ==================== 15. ~~代码键名标签 CodeTag~~ ====================
# 已删 (v2.3.1 三轮, rules.md §4.3 隐藏技术细节红线): rev.ini 键名是对用户
# 无价值的内部细节, 也是 "web coding 味" 来源之一。编号保留防错位;
# 极少数需要键名的场景用控件 tooltip 呈现, 不占版面。

# ==================== 12. 页头 PageHead ====================
def page_head(title: str, desc: str = "") -> ft.Container:
    """编辑页页头: 标题 + 描述。props: title, desc。
    (v2.3.1 三轮: 代码注释式 kicker 已删 — 典型 web coding 味装饰;
    字重 700 — 800/Black 未随包分发, rules.md §4.5)"""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=FONT_20, weight=ft.FontWeight.W_700,
                    color=theme.COL_TEXT_PRIMARY),
            ft.Text(desc, size=FONT_12, color=theme.COL_TEXT_DIM) if desc else ft.Text(""),
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
def config_card(title: str, desc: str, control, on_hover_shift=False,
                desc_lines: int = 0) -> ft.Container:
    """设置项卡片。props: title, desc, control, on_hover_shift, desc_lines。

    标题/描述/控件文字一律左对齐 (v2.3.1 用户否决过水平居中, 勿再提)。
    on_hover_shift: hover 右移 +4px (批次④试做项; 双列网格内 False —
    design-system.md #14; 卡顿即降级删 offset 行)。
    desc_lines: >0 时描述固定行高容器 (双列等高, main.py 用 2)。
    """
    title_row = ft.Row([
        ft.Text(title, size=FONT_14, weight=ft.FontWeight.W_700,
                color=theme.COL_TEXT_PRIMARY),
    ], spacing=SPACE_8)
    desc_text = ft.Text(desc, size=FONT_12, color=theme.COL_TEXT_DIM,
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
        border_radius=RADIUS_CARD,          # Win11 卡片档 8px (v2.3.1)
        bgcolor=theme.COL_BG_CARD,
        border=_border_all(1, theme.COL_BORDER_SUBTLE),
        shadow=theme.SHADOW_CARD,           # 卡片柔影 (tokens.md §1.7 card-shadow)
    )
    # hover 右移 +4px 已试做并降级 (批次④留档): offset 位移在 flet 0.86.5 实机
    # 上会破坏 ListView 内卡片渲染 (卡片有界不绘制), 与 design-system #14
    # "双列内无位移" 收敛 — hover 只保留 提亮 + 品牌边框

    def _hover(e):
        hover = _is_hovered(e)
        card.bgcolor = theme.COL_BG_GHOST_2 if hover else theme.COL_BG_CARD
        card.border = _border_all(1, theme.COL_BORDER_BRAND if hover
                                  else theme.COL_BORDER_SUBTLE)
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
    min_lines/max_lines(multiline 时行数, 加载器启动命令卡用 3/6)

    max_length 不传引擎 (2026-09-05 启动崩溃回归): flet 0.86.5 的 TextField
    没有 counter_text 参数 (只有 counter/counter_style), 而引擎只要设了
    maxLength 就必自带 "0/32" 计数器且无法隐藏 (字段卡高度差元凶) —
    改为 on_change 内手动截断, 限制语义不变, 计数器消失。"""
    def _on_change(e):
        v = e.control.value or ""
        if max_length is not None and len(v) > max_length:
            e.control.value = v[:max_length]
            try:
                e.control.update()   # 控件随重建分离时静默 (与 set_status 同纪律)
            except RuntimeError:
                pass
        if on_change:
            on_change(e)
    return ft.TextField(
        value=value, hint_text=placeholder, multiline=multiline,
        min_lines=min_lines if multiline else 1,
        max_lines=max_lines if multiline else 1,
        height=None if multiline else height,
        width=width,
        text_size=font_size,
        bgcolor=theme.COL_BG_INPUT,
        border=ft.InputBorder.OUTLINE,
        border_color=theme.COL_BORDER_VISIBLE,
        focused_border_color=theme.COL_BRAND,
        content_padding=_pad(h=12, v=10),
        border_radius=RADIUS_CTRL,   # Win11 控件档 4px (v2.3.1)
        text_style=ft.TextStyle(color=theme.COL_TEXT_PRIMARY,
                                font_family=FONT_MONO if mono else None),
        hint_style=ft.TextStyle(color=theme.COL_TEXT_DIM),
        on_change=_on_change,
        max_length=None,   # 引擎层不设限 (见 docstring), 截断在上面的 _on_change
        text_align=text_align or ft.TextAlign.LEFT,
    )


# ==================== 17. 下拉框 SelectDark (v2.3.1 四轮重构) ====================
class SelectDark(ft.PopupMenuButton):
    """自绘下拉 (design-system.md #17, 原生 ft.Dropdown 弃用)。

    收起态 = InputDark 同款按钮: 同宽 236/同高 48/同边框圆角, 值左对齐,
    箭头距右缘 8px; 展开态 = 应用同款菜单: bg-card 底 + border-visible +
    圆角 8 + 浮层柔影, 选中项 brand-bg-10 底 + brand-soft 字 600,
    悬停 bg-ghost。展开时边框变主色、箭头旋转 180° 变品牌蓝 (motion-fast)。

    实现路线: ft.PopupMenuButton + 自定义 content/items — 引擎弹出层只承担
    定位/外点关闭/超长列表滚动, 视觉全部自绘。不用纯 Stack 面板的原因:
    字段卡在 ListView 内, Stack 菜单会被视口裁切、被后续行卡片盖住
    (Flet 无跨控件层级); 引擎 overlay 路线无此缺陷, 动效为引擎内置
    弹出过渡 (~150ms, 近似 panel-in)。
    兼容 ft.Dropdown 消费面: .value / .options(元素含 .key) / .error_text。
    """

    def __init__(self, options, selected=None, placeholder="", width=None,
                 height=H_INPUT, on_select=None, font_size=FONT_14):
        self._on_select_cb = on_select
        self._open = False
        self._error: str | None = None
        self._entries: list[tuple[str, str]] = []
        for o in options:
            if isinstance(o, ft.dropdown.Option):
                self._entries.append((str(o.key), str(o.text or o.key)))
            elif isinstance(o, (tuple, list)):
                self._entries.append((str(o[0]), str(o[1])))
            else:
                self._entries.append((str(o), str(o)))
        self._value: str | None = selected if selected in self._keys() else None
        self._value_text = ft.Text(
            self._label_of(self._value) or placeholder,
            size=font_size, color=theme.COL_TEXT_PRIMARY,
            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
        )
        self._chev = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=14,
                             color=theme.COL_TEXT_MUTED)
        self._chev_box = ft.Container(
            content=self._chev,
            animate_rotation=ft.Animation(theme.MOTION_FAST, theme.EASE_STANDARD),
            rotate=ft.Rotate(0),
        )
        self._btn = ft.Container(
            content=ft.Row([self._value_text, self._chev_box],
                           spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            width=width, height=height,
            padding=_pad(h=12),
            bgcolor=theme.COL_BG_INPUT,
            border=_border_all(1, theme.COL_BORDER_VISIBLE),
            border_radius=RADIUS_CTRL,
        )
        self._items: list[ft.PopupMenuItem] = []
        self._render_items()
        super().__init__(
            content=self._btn,
            items=self._items,
            padding=0,
            menu_padding=_pad(h=4, v=4),
            bgcolor=theme.COL_BG_CARD,
            elevation=8,
            shadow_color=theme.SHADOW_FLOAT.color,   # 浮层柔影色 (随换装重建)
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
            clip_behavior=ft.ClipBehavior.NONE,
            menu_position=ft.PopupMenuPosition.UNDER,
            on_open=self._on_open,
            on_cancel=self._on_cancel,
            tooltip=None,
        )

    # ---- duck-typing: ft.Dropdown 消费面 (main.py populate_all) ----
    def _keys(self):
        return [k for k, _ in self._entries]

    def _label_of(self, key):
        for k, t in self._entries:
            if k == key:
                return t
        return None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        v = str(v) if v is not None else None
        self._value = v if v in self._keys() else None
        self._value_text.value = self._label_of(self._value) or ""
        self._render_items()
        self._safe_update()

    @property
    def options(self):
        """仅 .key 被 main.py populate_all 消费; 返回 Option 以保持鸭子类型。"""
        return [ft.dropdown.Option(key=k, text=t) for k, t in self._entries]

    @property
    def error_text(self):
        return self._error

    @error_text.setter
    def error_text(self, msg):
        self._error = msg or None
        if not self._open:
            self._btn.border = _border_all(
                1, theme.COL_ERR if self._error else theme.COL_BORDER_VISIBLE)
        self._safe_update()

    # ---- 内部 ----
    def _safe_update(self):
        try:
            self.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page (首次构建期) 跳过
            pass

    def _render_items(self):
        # 菜单与收起钮同宽: menu_padding 4×2, item 撑满菜单内宽 (HTML .dd-menu left:0 right:0)
        item_w = (self._btn.width - 8) if self._btn.width else None
        self._items = []
        for k, t in self._entries:
            selected = (k == self._value)
            item_box = ft.Container(
                content=ft.Text(
                    t, size=FONT_13,
                    weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                    color=theme.COL_BRAND_SOFT if selected else theme.COL_TEXT_SECONDARY,
                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=item_w,
                padding=_pad(h=10, v=8),
                border_radius=RADIUS_CTRL,
                bgcolor=theme.COL_BRAND_BG_10 if selected else None,
                on_hover=lambda e: self._item_hover(e),
            )
            self._items.append(ft.PopupMenuItem(
                content=item_box, on_click=lambda e, key=k: self._pick(key)))

    @staticmethod
    def _item_hover(e):
        # 选中项保持 brand 底; 未选中项悬停提亮 bg-ghost (design-system #17)
        box = e.control
        if box.bgcolor != theme.COL_BRAND_BG_10:
            box.bgcolor = theme.COL_BG_GHOST if _is_hovered(e) else None
            try:
                box.update()
            except Exception:  # noqa: BLE001, S110 - 菜单已关闭: 跳过
                pass

    def _apply_open_visual(self, opened: bool):
        self._open = opened
        self._btn.border = _border_all(
            1, theme.COL_BRAND if opened
            else (theme.COL_ERR if self._error else theme.COL_BORDER_VISIBLE))
        self._chev_box.rotate = ft.Rotate(3.14159265 if opened else 0)
        self._chev.color = theme.COL_BRAND if opened else theme.COL_TEXT_MUTED
        self._btn.update()

    def _on_open(self, e):
        self._apply_open_visual(True)

    def _on_cancel(self, e):
        self._apply_open_visual(False)

    def _pick(self, key):
        changed = (key != self._value)
        self._value = key
        self._value_text.value = self._label_of(key) or ""
        self._error = None
        self._render_items()
        self._apply_open_visual(False)
        self._safe_update()
        if changed and self._on_select_cb:
            self._on_select_cb(types.SimpleNamespace(control=self, data=key, name="change"))


def select_dark(options, selected=None, placeholder="", width=None,
                height=H_INPUT, on_select=None, font_size=FONT_14,
                **_legacy) -> SelectDark:
    """工厂函数 (组件名与 design-system.md 索引一致)。
    旧版 ft.Dropdown 的 filled/fill_color/border_color 参数不再生效,
    以 **_legacy 吞掉以兼容旧调用点 (v2.3.1 四轮自绘重构)。"""
    return SelectDark(options, selected=selected, placeholder=placeholder,
                      width=width, height=height, on_select=on_select,
                      font_size=font_size)


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
                             color=theme.COL_BRAND_LIGHT if added else theme.COL_TEXT_MUTED,
                             font_family=FONT_MONO, max_lines=1,
                             overflow=ft.TextOverflow.ELLIPSIS)
        super().__init__(
            content=self._text,
            padding=_pad(h=10, v=5),
            border_radius=RADIUS_CTRL,   # Win11 控件档 4px (v2.3.1)
            bgcolor=theme.COL_BRAND_BG_18 if added else theme.COL_BG_GHOST,
            border=_border_all(1, theme.COL_BORDER_BRAND if added else theme.COL_BORDER_VISIBLE),
            on_click=lambda e: self.toggle(),
            ink=False,
            animate_scale=ft.Animation(160, theme.EASE_STANDARD),   # chip-pop (tokens §7)
        )
        self._on_toggle = on_toggle

    def set_added(self, added: bool):
        """外部同步 added 态 (加载器 _sync_chips 用): 不触发 on_toggle"""
        self._added = added
        self._text.value = ("✓ " if added else "") + self._label
        self._text.color = theme.COL_BRAND_LIGHT if added else theme.COL_TEXT_MUTED
        self.bgcolor = theme.COL_BRAND_BG_18 if added else theme.COL_BG_GHOST
        self.border = _border_all(1, theme.COL_BORDER_BRAND if added else theme.COL_BORDER_VISIBLE)

    def toggle(self):
        self._added = not self._added
        self.set_added(self._added)
        self._pop()
        self.update()
        if self._on_toggle:
            self._on_toggle(self._label, self._added)

    def _pop(self):
        """chip-pop 勾选弹跳 (tokens §7): scale 0.94→1, 160ms 有限 1 次。"""
        page = self.page
        if page is None:
            return
        try:
            self.scale = ft.Scale(0.94)
            self.update()
        except Exception:  # noqa: BLE001 - 未挂 page: 跳过动效
            return

        def _up():
            try:
                self.scale = ft.Scale(1)
                self.update()
            except Exception:  # noqa: BLE001, S110 - 已重建: 静默
                pass
        threading.Timer(0.06, lambda: page.run_thread(_up)).start()


# ==================== 22. 类别标签 CatTag ====================
def cat_tag(text: str) -> ft.Container:
    """工具类别标签。props: text"""
    return ft.Container(
        content=ft.Text(text, size=FONT_10, weight=ft.FontWeight.W_600,
                        color=theme.COL_BRAND_LIGHT),
        bgcolor=theme.COL_BRAND_BG_15,
        border=_border_all(1, theme.COL_BORDER_BRAND),
        border_radius=RADIUS_CTRL,   # Win11 控件档 4px (v2.3.1)
        padding=_pad(h=8, v=2),
    )


# ==================== 23. 风险标签 RiskTag ====================
# key 兼容中英文: REPAIR_TOOLS 的 risk 是中文 (低/中/高, app/tools.py),
# design-system.md #23 记 low/mid/high — 两套都收, 未知 key 回退"低" (deep-review 5轮 LOW-8)
# 函数化取色: 模块级 dict 会在 import 时冻结深色值, 换装后不可见 (v2.3.0)
def _risk_color(level: str) -> str:
    return {"low": theme.COL_OK, "mid": theme.COL_WARN, "high": theme.COL_ERR,
            "低": theme.COL_OK, "中": theme.COL_WARN, "高": theme.COL_ERR}.get(
        level, theme.COL_OK)


def risk_tag(level: str, text: str | None = None) -> ft.Text:
    """工具风险等级。props: level(低/中/高 或 low/mid/high)"""
    label = text or {"low": "风险:低", "mid": "风险:中", "high": "风险:高",
                     "低": "风险:低", "中": "风险:中", "高": "风险:高"}.get(level, "风险:低")
    return ft.Text(label, size=FONT_11, weight=ft.FontWeight.W_600,
                   color=_risk_color(level))


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
                bgcolor=theme.COL_BRAND,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=RADIUS_CTRL),  # Win11 控件档
            ),
            on_click=on_click,
        )
        # 0.86.5 ButtonStyle 无 hover 态, 手动切换 bgcolor (main.py 同模式)
        self.on_hover = self._on_hover

    def _on_hover(self, e):
        if self.disabled:
            return
        self.style = ft.ButtonStyle(
            bgcolor=theme.COL_BRAND_HOVER if _is_hovered(e) else theme.COL_BRAND,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CTRL),  # Win11 控件档
        )
        self.update()

    def set_busy(self, busy: bool):
        self.disabled = busy
        self._icon.name = ft.Icons.HOURGLASS_TOP if busy else ft.Icons.PLAY_ARROW
        self._label.value = "运行中" if busy else "运行"
        self.update()


# ==================== 25. 工具状态 ToolStatus ====================
# 函数化取色: 模块级 dict 会在 import 时冻结深色值, 换装后不可见 (v2.3.0)
def _status_color(state: str) -> str:
    return {"idle": theme.COL_TEXT_DIM, "running": theme.COL_WARN,
            "ok": theme.COL_OK, "fail": theme.COL_ERR}.get(state, theme.COL_TEXT_DIM)


def tool_status(state="idle", text="待运行") -> ft.Text:
    """工具运行状态。props: state(idle/running/ok/fail), text"""
    return ft.Text(text, size=FONT_11, color=_status_color(state),
                   text_align=ft.TextAlign.RIGHT)


# ==================== 19. 推荐面板 RecPanel ====================
def rec_panel(chips, title: str = "推荐启动项", expand: int = 2) -> ft.Container:
    """推荐项面板 (design-system.md #19): 竖排 chips 单行省略。
    props: chips(ft.Container 列表), title, expand(Row 内分栏比例, LaunchSplit 右栏 2)。
    (deep-review 7轮 F4: 原 textarea 分支内联堆砌, 抽组件)"""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=11, weight=ft.FontWeight.W_600,
                    color=theme.COL_TEXT_MUTED),
            ft.Column(chips, spacing=6,
                      horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        ], spacing=8),
        bgcolor=theme.COL_BG_GHOST_3,
        border=_border_all(1, theme.COL_BORDER_SUBTLE),
        border_radius=RADIUS_CARD,   # Win11 卡片档 8px (v2.3.1, design-system #19)
        shadow=theme.SHADOW_CARD,
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
                    color=theme.COL_TEXT_PRIMARY),
            status,
        ], spacing=SPACE_6),
        padding=SPACE_16,
        border_radius=RADIUS_CARD,    # Win11 卡片档 8px (v2.3.1)
        bgcolor=theme.COL_BG_CARD,
        border=_border_all(1, theme.COL_BORDER_SUBTLE),
        shadow=theme.SHADOW_CARD,
        expand=expand,
    )

    def _hover(e):
        if _is_hovered(e):
            card.border = _border_all(1, theme.COL_BORDER_BRAND)
        else:
            card.border = _border_all(1, theme.COL_BORDER_SUBTLE)
        card.update()

    card.on_hover = _hover
    card._run_btn = run_btn  # type: ignore[attr-defined]
    card._status = status  # type: ignore[attr-defined]
    return card


# ==================== 27. 编码切换 EncGroup ====================
class EncGroup(ft.Container):
    """编码切换 (design-system.md #27, HTML .enc-group 结构)。

    2026-08 UI 审查: 原 ft.SegmentedButton 的 style 只能整体应用(选中/未选中
    无法分离, 亮蓝实心被用户反馈"难看", 状态字典在 0.86.5 上失效回退 M3 默认)
    → 自绘: ghost 底容器 + 分段按钮, 选中段 = 20% 主色浅底 + 主色浅字,
    未选中 = 透明 + 灰字 (与 chip 已添加态/导航激活态同一视觉语言)。
    props: segments([(value, label), ...]), selected(当前值), on_change(value)。

    selected property (2026-08-30 审查): load_file 按文件实际编码回填显示 —
    原实现返回裸 Container, `enc_selector.selected = [...]` 是 no-op, 显示
    恒为构建时的初始段, 与实际保存编码脱钩 (恰好是本控件要防的乱码误导场景)。
    property 静默换段不触发 on_change — st['enc'] 由调用方自行维护。
    """

    def __init__(self, segments, selected, on_change=None):
        # 命名注意: 不能用 _values/_dirty/_frozen 等 — flet 基类把它们用作
        # 响应式存储, super().__init__() 会覆盖 (实测 _values 被换成 dict,
        # setter 的成员判断随之永远失真)
        self._enc_values = [v for v, _ in segments]
        self._sel = selected
        self._on_change_cb = on_change
        self._btn_of: dict = {}
        for value, label in segments:
            self._btn_of[value] = ft.Container(
                content=ft.Text(label, size=FONT_11, weight=ft.FontWeight.W_600,
                                color=theme.COL_TEXT_DIM),
                padding=_pad(h=12, v=5),
                border_radius=3,   # 段内 3px (v2.3.1 Win11 档, HTML .enc-btn)
                on_click=lambda e, v=value: self._pick(v),
                ink=False,
            )
        self._render()
        super().__init__(
            content=ft.Row(list(self._btn_of.values()), spacing=2),
            bgcolor=theme.COL_BG_GHOST,   # HTML .enc-group rgba(255,255,255,0.05)
            border=_border_all(1, theme.COL_BORDER_SUBTLE),
            border_radius=RADIUS_CTRL,    # 外组 4px (v2.3.1 Win11 档)
            padding=_pad(h=3, v=3),
        )

    def _render(self):
        for value, btn in self._btn_of.items():
            active = value == self._sel
            btn.bgcolor = theme.COL_BRAND_BG_20 if active else ft.Colors.TRANSPARENT
            btn.border = _border_all(1, theme.COL_BORDER_BRAND if active else ft.Colors.TRANSPARENT)
            btn.content.color = theme.COL_BRAND_LIGHT if active else theme.COL_TEXT_DIM  # type: ignore[union-attr]

    def _safe_update(self):
        try:
            self.update()
        except Exception:  # noqa: BLE001, S110 - 未挂 page (首次构建期) 跳过
            pass

    def _pick(self, v):
        if v == self._sel:
            return
        self._sel = v
        self._render()
        self._safe_update()
        if self._on_change_cb:
            self._on_change_cb(v)

    @property
    def selected(self):
        return self._sel

    @selected.setter
    def selected(self, v):
        """外部回填 (load_file)。接受 str 或 [str] (兼容旧列表写法); 未知值忽略。
        静默换段: 不触发 on_change (st['enc'] 由调用方同步维护)。"""
        if isinstance(v, (list, tuple)):
            v = v[0] if v else None
        if v not in self._enc_values or v == self._sel:
            return
        self._sel = v
        self._render()
        self._safe_update()


def enc_group(segments, selected, on_change=None) -> EncGroup:
    """工厂函数 (组件名与 design-system.md 索引一致)。"""
    return EncGroup(segments, selected, on_change)


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
            else ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=theme.COL_OK)]
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
        bgcolor=theme.COL_BG_DEEP,   # HTML 事实源 .statusbar 用 var(--bg-deep) (deep-review 5轮修正)
        border=_border_top(1, theme.COL_BORDER_SUBTLE),
    )


# ==================== 33. 头像操作按钮 AvatarActionBtn ====================
def btn_av(label: str, icon=None, on_click=None, variant="normal"):
    """修改头像页操作按钮 (design-system.md #33)。variant: primary/ghost/normal"""
    if variant == "primary":
        return ft.FilledButton(label, icon=icon, on_click=on_click, height=H_BTN_AV,
                               style=ft.ButtonStyle(
                                   bgcolor=theme.COL_BRAND, color=theme.COL_TEXT_PRIMARY,
                                   shape=ft.RoundedRectangleBorder(radius=RADIUS_CTRL)))
    return ft.OutlinedButton(label, icon=icon, on_click=on_click, height=H_BTN_AV,
                             style=ft.ButtonStyle(
                                 bgcolor=ft.Colors.TRANSPARENT,
                                 color=theme.COL_TEXT_SECONDARY,
                                 side=ft.BorderSide(1, theme.COL_BORDER_VISIBLE),
                                 shape=ft.RoundedRectangleBorder(radius=RADIUS_CTRL)))


# ==================== 32. 头像预览 PreviewAvatar ====================
def preview_avatar() -> ft.Container:
    """修改头像页预览 (96px 圆, design-system.md #32)。content 由调用方持引用更新"""
    return ft.Container(
        width=S_PREVIEW_AVATAR, height=S_PREVIEW_AVATAR,
        border_radius=RADIUS_PILL,
        bgcolor=theme.COL_BG_CARD_2,
        border=_border_all(2, theme.COL_BORDER_VISIBLE),
        alignment=ft.alignment.Alignment(0, 0),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


# ==================== 30/31. 裁剪画布 CropCanvas ====================
class CropCanvas(ft.Container):
    """修改头像裁剪画布: 原图 + 1:1 裁剪框 (design-system.md #30/#31)。

    交互: 拖动框体移动 / 拖动四角缩放(保持 1:1) / 滚轮围绕中心缩放。
    约束: 边长 CROP_MIN ~ 画布边长, 位置不越界。
    on_change(box): box=(left, top, right, bottom) 原图像素坐标, cover 缩放反推。
    """

    def __init__(self, on_change=None):
        self.on_change = on_change
        self._iw = 0          # 原图宽
        self._ih = 0          # 原图高
        self._x = 0.0         # 框左上角 x (画布坐标)
        self._y = 0.0         # 框左上角 y
        self._size = 0.0      # 框边长
        self._mode = None     # None | 'move' | 'nw' | 'ne' | 'sw' | 'se'
        self._drag = {}

        # 1×1 透明 PNG base64: flet Image src 不能为空, 空串会渲染
        # "A valid src value must be specified" 错误块且后续更新不消失
        _TRANSPARENT_1PX = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
                            "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
        self._img = ft.Image(src=_TRANSPARENT_1PX, fit=ft.BoxFit.COVER,
                             filter_quality=ft.FilterQuality.HIGH)
        self._box = ft.Container(border=_border_all(2, theme.COL_BRAND))
        # 框外遮罩 (4 片半透明, 覆盖裁剪框外区域; design-system.md #31)
        self._masks = [ft.Container(bgcolor=theme.COL_CROP_MASK) for _ in range(4)]
        # 九宫格线 (框内 2 横 2 竖)
        self._grids = [ft.Container(bgcolor=theme.COL_CROP_GRID) for _ in range(4)]
        self._handles = {
            d: ft.Container(width=S_CROP_HANDLE, height=S_CROP_HANDLE,
                            bgcolor=theme.COL_BRAND, border=_border_all(2, theme.COL_TEXT_PRIMARY))
            for d in ("nw", "ne", "sw", "se")
        }
        self._stack = ft.Stack(
            [self._img, *self._masks, self._box, *self._grids, *self._handles.values()],
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        gd = ft.GestureDetector(
            content=self._stack,
            on_pan_start=self._on_pan_start,
            on_pan_update=self._on_pan_update,
            on_pan_end=self._on_pan_end,
            on_scroll=self._on_scroll,
        )
        # 初始隐藏裁剪框系 (未选图时不显示; set_image 时才显示)
        self._box.visible = False
        for _m in self._masks:
            _m.visible = False
        for _g in self._grids:
            _g.visible = False
        for _h in self._handles.values():
            _h.visible = False
        super().__init__(
            content=gd,
            width=S_CROP_CANVAS, height=S_CROP_CANVAS,
            bgcolor=theme.COL_CROP_CANVAS_BG,
            border=_border_all(1, theme.COL_BORDER_SUBTLE),
        )

    # ---- 外部接口 ----
    def set_image(self, src: str, natural_w: int, natural_h: int):
        """设置原图 + 记录尺寸, 并重置裁剪框为居中 70%。"""
        self._iw = natural_w
        self._ih = natural_h
        self._img.src = src
        self._reset()

    def current_box(self) -> tuple[int, int, int, int] | None:
        """当前裁剪区域的原图像素 box; 未设图返回 None。"""
        return self._emit_box()

    # ---- 内部 ----
    def _reset(self):
        # 选图后显示裁剪框系
        self._box.visible = True
        for _m in self._masks:
            _m.visible = True
        for _g in self._grids:
            _g.visible = True
        for _h in self._handles.values():
            _h.visible = True
        s = S_CROP_CANVAS * 0.7
        self._size = s
        self._x = (S_CROP_CANVAS - s) / 2
        self._y = (S_CROP_CANVAS - s) / 2
        self._render()

    def _clamp(self):
        c = S_CROP_CANVAS
        self._size = max(CROP_MIN, min(self._size, c))
        self._x = max(0.0, min(self._x, c - self._size))
        self._y = max(0.0, min(self._y, c - self._size))

    def _render(self, emit: bool = True):
        self._clamp()
        c = S_CROP_CANVAS
        x, y, s = self._x, self._y, self._size
        self._box.left = x
        self._box.top = y
        self._box.width = s
        self._box.height = s
        # 遮罩 (上/下/左/右)
        m = self._masks
        m[0].left, m[0].top, m[0].width, m[0].height = 0, 0, c, y
        m[1].left, m[1].top, m[1].width, m[1].height = 0, y + s, c, c - (y + s)
        m[2].left, m[2].top, m[2].width, m[2].height = 0, y, x, s
        m[3].left, m[3].top, m[3].width, m[3].height = x + s, y, c - (x + s), s
        # 九宫格线 (2 横 2 竖)
        g = self._grids
        g[0].left, g[0].top, g[0].width, g[0].height = x, y + s / 3, s, 1
        g[1].left, g[1].top, g[1].width, g[1].height = x, y + 2 * s / 3, s, 1
        g[2].left, g[2].top, g[2].width, g[2].height = x + s / 3, y, 1, s
        g[3].left, g[3].top, g[3].width, g[3].height = x + 2 * s / 3, y, 1, s
        half = S_CROP_HANDLE / 2
        pos = {
            "nw": (self._x - half, self._y - half),
            "ne": (self._x + self._size - half, self._y - half),
            "sw": (self._x - half, self._y + self._size - half),
            "se": (self._x + self._size - half, self._y + self._size - half),
        }
        for d, (hx, hy) in pos.items():
            self._handles[d].left = hx
            self._handles[d].top = hy
        if emit:
            self._emit()
        self.update()

    def _on_pan_start(self, e):
        lx, ly = e.local_position.x, e.local_position.y
        s = self._size
        half = S_CROP_HANDLE / 2 + 6   # 命中容差
        corners = {
            "nw": (self._x, self._y),
            "ne": (self._x + s, self._y),
            "sw": (self._x, self._y + s),
            "se": (self._x + s, self._y + s),
        }
        for d, (cx, cy) in corners.items():
            if abs(lx - cx) <= half and abs(ly - cy) <= half:
                self._mode = d
                if d == "se":
                    fx, fy = self._x, self._y
                elif d == "nw":
                    fx, fy = self._x + s, self._y + s
                elif d == "ne":
                    fx, fy = self._x, self._y + s   # 固定对角 sw
                else:
                    fx, fy = self._x + s, self._y   # 固定对角 ne
                self._drag = {"fx": fx, "fy": fy}
                return
        if self._x <= lx <= self._x + s and self._y <= ly <= self._y + s:
            self._mode = "move"
            self._drag = {"ox": lx - self._x, "oy": ly - self._y}
        else:
            self._mode = None

    def _on_pan_update(self, e):
        if not self._mode:
            return
        lx, ly = e.local_position.x, e.local_position.y
        if self._mode == "move":
            self._x = lx - self._drag["ox"]
            self._y = ly - self._drag["oy"]
        else:
            fx, fy = self._drag["fx"], self._drag["fy"]
            ns = max(abs(lx - fx), abs(ly - fy))
            ns = max(CROP_MIN, min(ns, S_CROP_CANVAS))
            self._size = ns
            if self._mode == "se":
                self._x, self._y = fx, fy
            elif self._mode == "nw":
                self._x, self._y = fx - ns, fy - ns
            elif self._mode == "ne":
                self._x, self._y = fx, fy - ns      # 对角(sw)固定: 左缘=对角x, 底缘=对角y
            else:
                self._x, self._y = fx - ns, fy      # 对角(ne)固定: 右缘=对角x, 顶缘=对角y
        # 拖动中不触发 on_change (预览每帧重解码+编码实测卡顿):
        # 预览更新在 main.py 节流, 松手时 _on_pan_end 强制补最后一帧
        self._render(emit=False)

    def _on_pan_end(self, e):
        """松手: 清拖拽模式 + 强制 emit 最终 box (预览刷新到最后状态)。"""
        self._mode = None
        if self._drag:
            self._drag = None
        self._render()

    def _on_scroll(self, e):
        factor = 0.9 if e.scroll_delta.y > 0 else 1.1
        ns = max(CROP_MIN, min(self._size * factor, S_CROP_CANVAS))
        cx = self._x + self._size / 2
        cy = self._y + self._size / 2
        self._size = ns
        self._x = cx - ns / 2
        self._y = cy - ns / 2
        self._render()

    def _emit_box(self) -> tuple[int, int, int, int] | None:
        """cover 缩放反推原图像素 box (与 HTML applyPreviewTo 同语义)。"""
        if not self._iw or not self._ih or self._size <= 0:
            return None
        c = S_CROP_CANVAS
        scale = max(c / self._iw, c / self._ih)
        ox = (c - self._iw * scale) / 2
        oy = (c - self._ih * scale) / 2
        sx = (self._x - ox) / scale
        sy = (self._y - oy) / scale
        ss = self._size / scale
        return (max(0, round(sx)), max(0, round(sy)),
                min(self._iw, round(sx + ss)), min(self._ih, round(sy + ss)))

    def _emit(self):
        box = self._emit_box()
        if box is not None and self.on_change:
            self.on_change(box)
