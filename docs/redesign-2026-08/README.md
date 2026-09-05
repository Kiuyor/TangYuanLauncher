# 2026-08 UI 大改战役 — 视觉语言换代

> **状态：已暂停（2026-08-30）。** 用户决定暂不改当前 UI，v2.3.1 设计继续生效（本战役从未改动任何 flet_app 代码与 docs 四件套）。本目录仅作过程存档；将来重启战役时从「方向稿」续起。

> 本目录是本次大改的唯一战役档案。规则与流程见工作区 skill `D:\re-la\.zcode\skills\tangyuan-ui\SKILL.md`。

## 授权定稿（2026-08-30 三轮拷问）

- 幅度：**换视觉语言**（颜色/字体档/圆角/质感全部重开）；信息架构仅微调
- 否决清单：居中卡片文字/发光/800 字重 = **永久**；40px 扁框/自绘圆角/Win11 圆角档/矢车菊蓝体系/字号档/动效性格 = **本次重开**
- 硬约束：深浅双主题、禁止位图资产（允许程序化渐变/噪点）、字体 HarmonyOS Sans SC + JetBrains Mono（字重 400/500/700）、组件只进 `components/ui.py`
- 流程：HTML preview 路线保留 → 新事实源 `preview v2.html`；**主页试点先行**；编辑页 784×600 尺寸解锁（阶段 2 决策）

## 状态

| 阶段 | 状态 |
|---|---|
| 0 现状痛点扫描 | ✅ [painpoints.md](painpoints.md)（P1 空间利用低 · P2 操作可达性差 · P3 层次单一 · P4 状态表达弱 · P5 主题人格缺失 · P6 无动效记忆点） |
| 1 方向稿 ×4 | ✅ 见下表，**待用户挑选** |
| 2 深化定稿（四页 + preview v2.html + 令牌同步） | ⬜ |
| 3 Flet 落地（主页试点 → 铺开） | ⬜ |
| 4 全量验收 + 宪法回写 | ⬜ |

## 方向稿（仅主页 360×510，双主题，真实数据）

| 方向 | 文件 | 一句话 |
|---|---|---|
| A 雾面 | [direction-A-acrylic.html](direction-A-acrylic.html) | 亚克力层次 + 冷调蓝灰，服务器改为可见玻璃卡，启动钮带文字标签 |
| B 图纸 | [direction-B-industrial.html](direction-B-industrial.html) | 工业高对比 + 信号琥珀 + 等宽数据，启动=满宽琥珀条，图纸网格与角标 |
| C 软陶 | [direction-C-soft.html](direction-C-soft.html) | 暖调亲和（浅色优先）+ 大圆角软卡片 + 珊瑚橘胶囊启动钮 |
| D 终端 | [direction-D-terminal.html](direction-D-terminal.html) | 等宽极简 + 终端绿 + 左对齐高密度，`[ 启动 csgo.exe ]` 命令条 |

截图存档：`screenshots/direction-{A,B,C,D}-{dark,light}.png`（现状对照：`current-{dark,light}.png`）。

## 放飞批次（第二批，2026-08-30 用户反馈"太拘束，放飞自我"后追加）

保留永久否决与功能硬约束，解除布局骨架限制——四个高个性方向：

| 方向 | 文件 | 一句话 |
|---|---|---|
| E 座舱 | [direction-E-cockpit.html](direction-E-cockpit.html) | HUD 军绿×冷青，斜切轮廓，雷达扫掠环包住启动钮，双列仪表布局 |
| F 街机 | [direction-F-arcade.html](direction-F-arcade.html) | CRT 扫描线，洋红×电青硬阴影像素框，PRESS START 闪烁，RANKING 服务器表 |
| G 大字报 | [direction-G-poster.html](direction-G-poster.html) | 瑞士海报×中式印章，竖排 168px 巨字"启动"出血，朱红点睛，浅色优先 |
| H 极光 | [direction-H-aurora.html](direction-H-aurora.html) | 紫×品红渐变 blob 漂移（唯一循环动画），玻璃浮岛，大胶囊渐变启动钮 |

截图存档：`screenshots/direction-{E,F,G,H}-{dark,light}.png`。

**Flet 可实现性预警（选型时纳入考量）**：H 的 backdrop-filter 玻璃与 blob 漂移动画在 Flet 0.86.5 需实机验证，可能降级为静态渐变背景；F 的扫描线/硬阴影、E 的雷达扫掠（transform 旋转）预期可落地；G 纯静态最安全。

## 已知留白项（阶段 2 处理）

- B/C/D 中段留白偏大（仅 2 台服务器，内容密度不足）——定稿后按真实内容密度重排节奏
- 四方向共同新增元素（服务器可见列表、练枪/目录快捷、启动标签）需在 editor 四导航里找到对应落位
- 动效性格（每方向 1 个记忆点，循环动画 ≤1）随方向定稿再定

## 下一步

用户挑选方向 → 阶段 2：深化其余三页（编辑/头像/CFG）+ 编辑页尺寸决策 → 产出 `preview v2.html` → 同步四件套与 `theme.py`。
