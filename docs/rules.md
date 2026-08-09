# 编码约束 Rules — 汤圆启动器 Rev.Ini 编辑器

> 本文件是 **写死的约束**,实现阶段(Flet 翻译与后续迭代)必须遵守;违反即视为代码缺陷。
> 配套: `design-system.md`(组件库)/ `tokens.md`(令牌字典)/ `DESIGN.md`(设计语言)
> 唯一事实源: `docs/preview v1.html`(HTML 是唯一事实源)

---

## §1 组件使用约束(硬性)

1. **组件来源唯一**: 产品 UI 只能用 `flet_app/components/ui/` 目录下的组件构建。
2. **禁止新建组件**: 不允许在 `components/ui/` 之外另起炉灶定义新组件;也不允许在 `main.py` 或页面代码里用基础控件堆砌出"伪组件"(重复的结构必须抽到 `components/ui/`)。
3. **组件命名**: 组件名与 `design-system.md` 组件索引一致(如 `LaunchButton`、`ConfigCard`、`ServerMonitor`),文件名/类名用语义名,不引入第二套命名。
4. **原生豁免**: Flet 原生基础控件(`ft.Text`/`ft.Container`/`ft.Row`/`ft.Column`/`ft.TextField`/`ft.Dropdown`/`ft.Switch`/`ft.Icon`/`ft.IconButton`/`ft.Scrollbar` 等)不受 §1.1/1.2 限制——它们是组件库的原材料,但**页面布局中组合出来的可复用结构**必须组件化。
5. **例外通道**: 确需新建组件(现有组件无法表达)时,必须满足:
   - 先在 `design-system.md` 组件索引登记(用途/props/何时用/何时不用),同步 `tokens.md`;
   - 组件必须落在 `flet_app/components/ui/` 下;
   - 在代码评审中说明"为什么现有组件无法组合实现"。
   未登记就新建 = 违规。

## §2 颜色约束(硬性)

1. **禁止硬编码色值**: 代码中不允许出现十六进制色(`#6495ED`)、`rgb()`/`rgba()` 字面量(除透明 `rgba(0,0,0,0)` 等语义明确场景)。
2. **必须引用令牌**: 所有颜色通过 `tokens.md` 定义的语义令牌取用:
   - Flet: `COL_*` 常量(集中定义于 `flet_app/theme.py` 或 `components/ui/` 的令牌模块);
   - HTML 预览: `var(--token)`。
3. **状态色也走令牌**: 启动中/已启动/运行中/失败等动态状态色,引用 `launch-busy`/`launch-done`/`status-amber`/`status-red` 等令牌,**不得在状态切换代码里写新色值**。
4. **新增颜色**: 必须先登记到 `tokens.md` 并给出语义名,再使用;禁止"临时色值先写,后补登记"。
5. **令牌与 HTML 一致性**: 令牌值以 `preview v1.html` 为准;HTML 有调整时,`tokens.md` 同步更新,双方必须双向核对一致(验证脚本核对)。

## §3 同步义务(硬性)

1. **改组件必改文档**: 任何组件外观/结构/行为的变更,必须同步更新 `design-system.md` 对应条目 + `tokens.md`(若涉及令牌)+ 本文件(若涉及约束)。
2. **改令牌必改两端**: 令牌变更必须同时更新 `tokens.md` 与 `preview v1.html` 的 `:root` 变量,保持两端一致。
3. **文档滞后视为缺陷**: 评审时若发现代码与三件套不一致,优先修文档;文档缺失条目视为组件未登记(违反 §1)。

## §4 产品级约束(用户红线,硬性)

1. **全中文界面**: 界面文案全部中文(专有名词/技术标识符/代码键名除外,如 `rev.ini`、`Loader.ConnectServer`、`ANSI/UTF-8`、版本号)。
2. **禁止编造数据**: 所有状态信息(在线人数、运行结果、错误提示)必须来自真实检测/查询结果;查询失败显示离线/未知,禁止展示编造数字。服务器人数必须来自 A2S 真实查询,离线时隐藏人数。
3. **隐藏技术细节**: 面向普通玩家,对用户无价值的内部细节(执行命令、字段描述小字、时间戳、冗余状态文字)主动删除,用户不需要知道这些。
4. **主操作突出**: 主操作按钮(启动)始终是页面最大视觉元素,优先放大强调;次要操作弱化。
5. **字体必须随包分发**: 设计字体(HarmonyOS Sans SC + JetBrains Mono,见 tokens.md §字体族)必须随安装包携带 ttf 并自动安装/注册(或打包时嵌入),**禁止依赖目标机器已装字体**——否则陌生用户机器会回退默认字体,出现"一细一粗"渲染缺陷(2026-08 实机教训)。安装脚本见 `inno-setup` 打包配置。

## §5 自查清单(提交前逐条过)

- [ ] 代码中所有颜色都来自 `COL_*` 令牌,无十六进制/rgba 字面量?
- [ ] 新结构是否已组件化到 `flet_app/components/ui/`,未在页面代码堆砌?
- [ ] 是否新建了组件?(若是:已在 design-system.md 登记 + 满足例外条件?)
- [ ] 组件/token 变更是否同步了三件套(design-system.md / tokens.md / rules.md)?
- [ ] 界面文案全中文,无英文残留(专有名词除外)?
- [ ] 没有编造数据(人数/状态必须真实)?
- [ ] 没有把执行命令/内部细节暴露给用户?
- [ ] 启动按钮尺寸/样式符合 design-system.md(110px 圆形)?
- [ ] 打包配置包含字体随包(ttf 安装/注册),不依赖目标机器字体?

---

## 附: 项目落地位置

| 项 | 路径 |
|----|------|
| 设计规范 | `docs/DESIGN.md` |
| 组件库文档 | `docs/design-system.md` |
| 令牌字典 | `docs/tokens.md` |
| 本约束文件 | `docs/rules.md` |
| HTML 预览(唯一事实源) | `docs/preview v1.html` |
| Flet 组件库 | `flet_app/components/ui/`(待建) |
| Flet 令牌模块 | `flet_app/theme.py`(待建,集中定义 COL_*/SZ_*/RADIUS_*/SPACE_*) |
| 旧文档(待删) | `design/`(DESIGN.md/tokens.md/components.md,新设计定稿后删除) |
