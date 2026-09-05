# revini-editor（汤圆启动器）

CS:GO 配置编辑器，Flet 桌面应用，面向陌生人公开分发"装完即玩"。

## 文档体系（唯一事实源）
- `docs/preview v1.html` = 设计唯一事实源；四件套 `docs/{DESIGN,design-system,tokens,rules}.md`
- 只准用 `flet_app/components/ui.py` 里已有的组件，禁止新建组件文件，禁止硬编码颜色
- 字体：HarmonyOS Sans SC + JetBrains Mono（用户级 HKCU 已装 + 随包 ttf）；设计字重限 400/500/700

## 铁律
- UI 形状 = Win11 圆角档位（v2.3.1 定稿，**推翻旧「全矩形化」铁律**）：窗口 DWM 原生圆角 / 卡片·面板·弹窗·菜单 8px / 按钮·输入·chips·标签 4px；仅头像、启动钮正圆，状态胶囊/版本徽章胶囊保留
- 不覆盖原件，新方案与旧文件并存（newloader.exe 的教训）
- 重启 flet 调试前必须连杀所有 `python main.py` 僵尸实例，否则点击失效
- 外部可能并发改 HTML：编辑 `docs/preview v1.html` 前先重读 + md5 核对
- 模块文档纪律（2026-09-05）：模块公开接口/行为/坑位变更，当轮同步 `docs/module/<module>.md` 并更新文头「最后核对」日期（索引与依赖图在 `docs/module/README.md`）

## 布局参考
- CFG 配置页 = 导航第 4 项，表单化（s0up 预设 auto/crosshair.cfg）
