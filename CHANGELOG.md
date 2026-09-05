# 更新日志

本项目的所有重要变更均记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

### 变更:2026-09-05 拷问定稿 (卡片等高 / UAC 反馈 / newloader 自动就位)

- **字段卡文本输入框对齐 48px 定稿**:昵称/战队标签/自动进服输入框由 flet 默认 ~63px 改 48px,并去掉 flet 因 max_length 自带的"0/32"字数计数器(不在设计事实源,且是与下拉卡不等高的元凶)— flet 0.86.5 的 TextField 无 counter_text 参数(首版实现误用导致启动即崩),改为引擎不设 maxLength、`input_dark` 在 on_change 内手动截断,长度上限语义不变,双列卡片完全等高
- **newloader 启动时自动就位**:点启动时目录缺失才从 assets 静默安装(md5 幂等,不覆盖原版 Loader.exe),修复工具页「安装优化 Loader (免残留)」手动工具移除;_install_loader 函数保留供启动链与回归测试
- **UAC 提权流程反馈补全**:ShellExecuteW 挪后台线程(期间 UI 不僵);弹窗前主页提示"系统将弹出管理员确认 (UAC)" + 按钮置"等待管理员确认…";批准进入统一轮询,取消则按钮复位 + 红字"管理员确认未通过"
- **新增 assets/Loader_opt23_nouac.exe**:newloader 的 asInvoker 等长清单补丁版(免 UAC 候选,manifest XML 解析已验证),待实机验证(启动/进服/退出清注册表)后再决定是否转正为默认资产

### 修复:全量代码审查 (2026-09-05, 1 项 P1 + 8 项 P3)

- **换装重建后编辑页状态栏整体失效 (P1)**:`_rebuild_editor_surfaces` 重绑 `status_bar` 变量不会替换 `_root` Column 已捕获的旧对象 — 手动/定时切主题后进入编辑页,底部状态栏(编码切换器/状态图标/保存反馈)永久不可见。改经 `status_bar_holder.content` 换入树(与 `title_bar.content` 换装同模式)
- **ServerMonitor 呼吸线程首拍误杀**:构建初期控件尚未挂 page 时第一拍即永久停转 — 引入 `_ever_attached` 区分"未挂载"(继续等待)与"已重建分离"(自停防泄漏)
- **ServerMonitor.set_status 静默不对称**:`self.update()` 无 try,状态 API 回包竞态(进编辑页 6s 窗口)在工作线程抛异常 — 与 `ServerPanel.set_servers` 对称包裹
- **写文件原子写统一**:`_procname_patch`/`_procname_restore`/`_cfg_add_exec`/`apply_values` 由直写(先截断)改为 tmp + `os.replace`,与 `ini_model.save`/settings/avatar 纪律一致
- **工具页执行超时值换装后丢失**:重建把输入框重置回 120 — 值持久到 `st["tool_timeout"]`
- **`+exec auto.cfg` 检测容错**:双空格/引号包裹变体不再误报"启动参数缺少 +exec"
- **清理**:删除 `RunButton._base_style` 死代码、`_sp_show` 重复 `visible=True`、名不副实的 `refresh_dir`(就地换 `page.update()`)
- **工具描述对齐**:"更新皮肤库"卡片文案 1695 → 6350 条记录(与 gen-8 生成器/打包链一致)
- **make_icon.py 路径迁移**:输出路径 D:\cs\ → D:\re-la\(D 盘迁移遗留)
- **修复工具卡片行距补齐 (用户反馈)**:双列网格行间竖距原为 0(两行卡片贴死) — 按事实源 tokens.md §4 `.tool-grid` gap=space-10 在行间插入 10px 垫片;仅动卡片接缝,页头/超时卡/风险告知间距不变
- **CFG 配置页同款间距补齐 (拷问定稿 B 档)**:组内双列卡片行距 0→10(与工具页/字段页同款垫片法,组标题 top18 分层节奏不动);顶部两条警示条(+exec 缺失/预设缺失)同时出现时也垫 10px — 原先同样贴死
- **编辑/头像页主题即时换装 (拷问定稿, 用户报告"配置页改深浅色页面不刷新")**:手动切深浅/定时、深色时段保存、定时轮询三条换装路径,在编辑/头像页停留时经 `_redress_nonhome()` 就地触发 epoch 重建并装回树(原惰性策略只在 show_* 进入时检查,人已站在页面上永远等不到) — 未保存修改/当前导航页/裁剪状态/窗口尺寸全保留;废弃"返回主页后应用"惰性文案
- **令牌接线专项 (拷问定稿)**:消除 theme 令牌与代码字面量的双份事实 — 窗口尺寸(`WIN_LAUNCHER/WIN_EDIT`,删本地 WIN_HOME/WIN_EDIT/WIN_MIN)、`W_SIDEBAR/H_BTN_BAR/H_TITLEBAR/H_STATUSBAR/S_DOT/FONT_16` 共 11 处接线;两处保真修正:导航栏底色 `COL_BG`→`COL_BG_SIDEBAR`、导航图标 24px→`FONT_20_IC`(20px) 对齐 HTML 事实源(实机截图目检过);规范令牌未消费清单留档 docs/module/flet_app/theme.md

## [2.3.1] - 2026-08-30

### 变更:UI/UX 按定稿设计全面实装 (docs/preview v1.html 为唯一事实源)

- **Win11 圆角档位**(推翻 2.2.x 全矩形化):窗口走系统级 DWM 原生圆角 (`DwmSetWindowAttribute`, 失败自动回退矩形并在状态栏留档),卡片/面板/菜单 8px,按钮/输入框/标签/窗口控制钮/导航项 4px;头像/启动钮保持正圆、胶囊保留
- **自绘下拉框**:界面语言/段位/CFG 枚举下拉全部重构 — 收起态 = 输入框同款 236×48(值左对齐、箭头距右缘 8px),展开态 = 应用同款菜单(卡片底/圆角 8/浮层柔影/选中项品牌蓝底、箭头旋转 180° 变品牌蓝);原生 ft.Dropdown 引擎弹出层弃用
- **服务器直连改悬停面板**:主页状态胶囊悬停展开分服面板(逐行 状态点+名称+人数, 悬停行浮现「进入」钮,150ms 防误关),「进入」= 一次性 `+connect` 启动、不改常用设置;状态胶囊只显示主服(常用设置 ConnectServer 目标);删除主页服务器下拉与自定义 IP 录入弹窗(预设仍存 settings.json 兼容旧数据)
- **练枪入标题栏**:主页卡片回归四件套(头像 100 / 昵称 24px / 状态胶囊 / 启动钮 110),练枪改标题栏准星钮,启动按钮保持主页最大视觉元素
- **去 web coding 味**:删页头代码注释 kicker 与 rev.ini 键名标签;等宽字体收窄至真代码场景(启动命令/IP:端口/CFG 数值);版本徽章/在线人数改界面字体;字段卡输入框 48px 高 + 15px 字(CFG 数值 mono 13px、下拉 14px)
- **材质与状态**:配置/工具卡片圆角 8 + 柔影;主页内容区品牌氛围垫层(radial 极淡品牌蓝, 非发光);启动按钮「已启动」态补绿辉光;在线点呼吸动画(全页唯一循环)、启动中火箭抖动(有限 2 次非循环)、推荐项勾选弹跳
- **动效降级留档**:视图/分组/面板入场与 hover 位移(按钮上移 -2px、卡片右移 +4px)在 flet 0.86.5 实机反复破坏布局(内容区空白/控件叠错位),按 rules §4.6 就地降级为即时切换/仅变色;保留 opacity/rotate/scale 三类安全动效;6px 细滚动条实装(page.theme scrollbar_theme)

### 修复(含 2.3.0 存量)

- **主页标题栏裁掉「关闭」钮**:IconButton 默认最小 40×40,5 钮撑出 360px 窗宽 — 显式 28×28
- **浅色主题一族文字白字不可读**:`page.theme_mode` 未随换装,无显式颜色的 Text 恒按深色取默认色 — theme_mode 随方案切换
- **定时主题夜间启动崩溃隐患**:`theme.COL_BG`/`COL_CARD` 历史别名只存在于浅色覆盖表,切回深色残留浅色值(根容器/导航白底白字) — 补模块级深色别名
- **主题菜单/深色时段弹窗打不开**:`page.open()` 在 flet 0.86.5 不存在 — 改 `page.show_dialog()`
- **全部悬停效果失效**:on_hover 事件按字符串 `"true"` 比较,flet 0.86.5 传真布尔(2.3.0 起存量)— 统一 `_is_hovered()` 兼容两种取值

### 修复:发布前全量代码审查 (2026-08-30 二轮, P0-P3 共 15 项)

- **修改头像在分发版必报错 (P0)**:选图回调遗留调试日志写死 `C:\Users\75017\...` 临时路径,任何其它机器上首次调用即抛异常被兜底吞掉 — 删除全部调试代码
- **打包缺两个 assets (P1)**:`build_nuitka.bat` 未拷 `assets\maps\aim_botz.bsp` 与 `assets\default_avatar*.dat` — 分发版「恢复默认头像」必失败、更新包/外部目录用户「练枪启动」必失败;补拷贝与失败检查
- **发布流水线断链 (P1)**:两个打包 bat 指向已损坏的 `.venv311` — 改指活动 `.venv`;ISCC/7-Zip 增加常见路径回退
- **换装后 CFG 页保存语义错位 (P1)**:主题换装重建编辑页时保存按钮恒接 rev.ini 保存 — 停在 CFG 页点保存会静默丢 CFG 修改、误存 rev.ini;按当前导航页接线;换装重建同时补刷壳层底色(浅色编辑页残留深色背板)、保留未保存 CFG 编辑(不重读盘)
- **编辑页打开时保存深色时段视图被拽回主页 (P2)**:`_save_period` 无条件重建主页 — 与主题切换同规则改为仅主页即时重建、编辑页走惰性重建
- **编码选择器显示与实际保存编码脱钩 (P2)**:`enc_group` 返回裸 Container,`load_file` 回填 `selected` 是无声 no-op,UTF-8 文件显示 ANSI — EncGroup 类化并加 `selected` property(静默回填),重建时播种当前编码
- **导航切页取消后高亮与内容错位 (P2)**:确认丢弃"取消"后 rail 停在目标页且再点无响应 — 取消拨回、确认重指目标、弹窗前先 pop 防叠加
- **打包链版本号未随 2.3.1 (P2)**:installer.iss/Nuitka 产品版本/输出文件名同步 2.3.1
- **健壮性 (P3)**:DWM 圆角找窗改 EnumWindows 子串匹配(置脏标题 `* Tangyuan` 曾致 FindWindow 脱靶);切视图仅在窗口失焦时拉焦点(on_event FOCUS/BLUR 跟踪);启动按钮状态探测(tasklist)挪后台线程;工具运行回调对换装后废弃控件兜底;`RevIni.save` 改原子写(tmp+os.replace);`validate_image` 先查头部尺寸再解码;在线点呼吸线程随控件移除自停
- **深色时段保存致方案翻转时浅色白字 (三轮)**:`_save_period` 只换 theme.* 未同步 `page.theme_mode`(与 `_apply_theme_mode` 不同规)— 补 `_apply_page_theme()`
- **换装后进入修改头像页显示旧配色 (三轮)**:头像页表面只在启动时构建一次 — 收进 `_rebuild_avatar_surfaces()`,`show_avatar` 按 epoch 重建(裁剪中复用画布保进度);启动测量脚本窗口标题匹配同步 `Tangyuan`

## [2.3.0] - 2026-08-30

### 新增:深浅双主题定时切换 + 服务器直连 + 一键练枪启动

- **深/浅/定时三态主题**:`flet_app/theme.py` 新增浅色令牌集 (品牌蓝 #6495ED、矩形风不变, 浅灰蓝纸面+纯白卡片) 与 `set_scheme()` 整体换装;`main.py`/`components/ui.py` 全部颜色改为 `theme.X` 动态访问 (from-import 会冻结启动色值);主页标题栏新增主题按钮 (深/浅/定时菜单 + 深色时段设置, 默认 19:00-07:00 深色、支持跨午夜), 运行中每 60s 复核时段即时换装;主页换装整组重建, 编辑页/头像页惰性重建 (epoch 标记, 下次进入应用);设置存 settings.json (`theme_mode`/`theme_dark_start`/`theme_dark_end`, 旧安装自动兼容)
- **服务器选择直连**:主页新增服务器下拉 (跟随常用设置/预设/自定义 IP…), 预设存 settings.json `server_presets` (内置 十人竞技 43.241.51.48:27015=phoenix、躲猫猫 43.241.51.48:27016=zombie, 用户可增自定义项);在线状态按选中服务器显示 (状态 API `servers[]` 数组), 无 sid 映射时聚合显示;启动经既有 `_procname_patch` 临时追加 `+connect`, 启动后自动恢复
- **一键练枪启动**:主页新增「练枪启动」按钮 — 内置 `assets/maps/aim_botz.bsp` (40MB, VBSP 校验) 幂等拷入 `csgo/maps/` (已有同名不覆盖, AGENTS.md 铁律), 启动链临时追加 `+map aim_botz` 后照常恢复;与直连互斥;**不使用 practice.cfg** (直接加载地图);打包链 `prepare_chunks.py` 同步注入 (装完即玩)
- **服务器监控修正**:状态 API 已改为 `{"servers":[…]}` 数组结构, 旧实现解析顶层 `online/lastBeat` 字段导致监控恒显示离线 — 本次按新结构解析并接入服务器选择

### 变更:游戏源版本切换 1.35.7.7 → 1.35.4.2

- **游戏源替换**:`D:\re-la\CSGO` 内容由 1.35.7.7 Build 485 (ZerotechOne, 2017-05-02) 重打包整体替换为 1.35.4.2 Build 350 (flashtrak, 2016-07-15) 重打包;目录路径不变,`user_csgo_dir` 无需改动。旧版仍完整保留于 `D:\tangyuangame\game`
- **启动器修改已重新迁移到新版**(逐项文件校验):s0up 预设 13 文件入 `csgo\cfg\`;rev.ini 四行(`ProcName` 追加 `+exec auto.cfg`、`PlayerName`、`Language=schinese`、`SteamUser`);`newloader.exe`(MD5 = `assets\Loader_opt23.exe`,原版 `Loader.exe` 未动);`startgame.bat` timeout 10s→2s
- **客户端版本常量对齐**:`app/__init__.py` `VERSION` 1.35.7.7 → 1.35.4.2(与游戏 version-info.txt 一致;`ini_model` 生成默认 rev.ini 模板的 `GameVersion`/`game` 字段随之更新)。注:新版重打包自带 rev.ini 的 `GameVersion=1.35.7.0` 与其 version-info.txt(1.35.4.2)自相矛盾,系重打包自身标签,未改动
- **打包文档对齐**:`packaging/README_分发版.md`、`docs/design-system.md` 游戏版本号同步为 1.35.4.2。**下次打包将内嵌 1.35.4.2**;已分发的 2.2.4 安装包内仍是 1.35.7.7,重新出包前勿混淆
- **刻意不迁移**:皮肤库扩展 `items_730.bin`(扩展版为 1.35.7.7 制作,跨版本物品 schema 有风险,保持出厂版;需要时用启动器"皮肤库更新"工具套用);ZR 修复包(zip + anay 已删除,进 ZR 服报错时再取);autoexec.cfg 桥(v2.2.3 已废弃,由 `ProcName +exec auto.cfg` 承担)

## [2.2.4] - 2026-08-23

### 修复:第 12 轮深度审查 (CFG 配置页)

- **NaN 校验漏洞**:float 字段 (灵敏度/音量/亮度等) 输入 `nan`/`NaN` 会通过范围校验并写入 cfg, 导致游戏配置损坏——`app/cfg_fields.py` 加 `math.isfinite` 守卫
- **准星透明度精度丢失**:保存时全量写回所有字段, 透明度 scale 往返 round 丢精度 (200→199), 未修改的透明度被静默改写——scale 换算移到 UI 层, 未修改字段用文件原值写回
- **切页"丢弃"失效**:CFG 页改后切页确认"丢弃", 实际未清 dirty 未重建页面, 修改残留且关窗再弹未保存——`_switch` 离开 CFG 页时真实丢弃 (清 dirty + 重建)
- **`_cfg_add_exec` 破坏 CRLF**:一键添加启动参数时把 rev.ini ProcName 行从 CRLF 改成 LF (混行尾)——改字节级操作保留行尾
- **缺失命令追加位置**:`_GROUP_HEAD_RE` 非贪婪捕获只匹配 1 字符, 缺失命令永远追加到文件尾而非组标题后——正则改贪婪 + 按键所属组分组追加
- **死代码清理**:`_GROUP_HEAD_RE` 重复定义删除

## [2.2.3] - 2026-08-23

### 新增:CFG 配置页 + s0up 预设默认集合

- **CFG 配置页**(编辑页导航第 4 项):表单化编辑 s0up 预设——4 组 23 字段(鼠标/准星/声音/性能),范围校验标红不保存,保存前自动 `.bak` 备份,独立 dirty(返回/切页/关窗确认),数字字段等宽字体,卡片等高双列——`flet_app/main.py` + `app/cfg_fields.py`(新增)
- **准星透明度 0-100% 显示**:文件值 0-255 自动换算(255→100),玩家直觉——`app/cfg_fields.py`
- **s0up CFG 预设 V1.7 默认植入**:13 个预设文件 + autoexec.cfg 桥接(`exec auto.cfg`)进游戏目录,打包链同步注入(幂等 md5);`assets/s0up_preset/` 入库为单一事实源——`packaging/prepare_chunks.py` + `assets/`
- **启动器优化默认集合**:newloader.exe 植入游戏根目录(原版 Loader.exe 并存)
- **皮肤补全默认集合**:游戏源 items_730.bin 同步扩展版(原版备份 items_730_bak.bin,分块原有)
- **启动参数默认含 `+exec auto.cfg`**:预设启动即生效(CFG 页检测缺失时提示一键添加)——`app/fields.py`

### 变更:全 UI 矩形化 (2026-08-22 用户决策)

- 窗口/卡片/按钮/输入框/下拉/标签/chips/对话框全部直角(Flutter Windows 圆角窗口四角黑边问题无可靠解法,顺势统一矩形风格);头像/启动按钮正圆、状态胶囊/版本徽章保留
- 设计文档四件套同步(DESIGN.md 圆角表、design-system.md 组件映射、tokens.md 圆角令牌、preview v1.html :root)

### 修复

- **HIGH 设置按钮点击失效**:僵尸 main.py 进程并存(只杀 flet.exe 不杀 python)导致点击事件路由到旧实例;清干净进程重启即恢复——运维动作,代码无需改
- **CFG 保存无反馈**:状态栏新增临时提示(绿字 3 秒自动消失,连发不覆盖)+ 保存按钮「已保存」反馈——`flet_app/main.py`
- **CFG 页单卡撑满整行**:奇数卡片落单时直接 append 无宽度约束(准星透明度卡 648px 巨宽);单卡包 Row 约束宽度——`flet_app/main.py`
- **编码切换控件重做**:ft.SegmentedButton 选中/未选中无法分离样式(0.86.5 状态字典失效),自绘 enc_group(ghost 底 + 选中段 20% 主色浅底)——`flet_app/components/ui.py` + `flet_app/main.py`
- **s0up 预设生效机制**:autoexec 桥接被 config.cfg 覆盖,改启动参数 `+exec auto.cfg`(最后执行)——`app/fields.py`

## [2.2.2] - 2026-08-09

### 修复:第 8 轮深度审查 (deep-review round 8, 2 MEDIUM + 1 LOW)

- **MEDIUM `+connect` 多残留剥离不彻底**:`_strip_connect_arg` 只剥第一个 `+connect`,多个残留时第二个旧地址仍留在 ProcName(空值剥离模式清理不完整, v2.2.1 残留修复的多残留形态复发)。改为循环剥离全部 `+connect`(词边界检查保持)——`flet_app/main.py`
- **MEDIUM settings 写入崩溃**:`save_settings` 在 `os.makedirs` 失败(APPDATA 不可写/磁盘满/权限受限)时 except 分支引用未定义的 `tmp` → 抛未捕获 NameError,「指定目录」流程静默中断且设置丢失。`tmp` 定义移到 try 外,失败路径正确返回 False——`app/settings.py`
- **LOW 打包幂等误判**:`prepare_chunks.apply_patch` 幂等判定用裸子串 `marker in data`,`timeout /t 2` 会误匹配 `timeout /t 20 /nobreak`(未提速变体)或 banner/ECHO 文本 → 发行包静默漏提速。改为行首锚定 + 词边界正则(含 CRLF `\r`, 与 tools.py `_speedup_startgame` 已修实现对齐)——`packaging/prepare_chunks.py`

## [2.2.1] - 2026-08-09

### 修复:迟到批量结果甄别 + 打包/工具链增量 (deep-review round 7 补充)

- **HIGH 残留 +connect**(task-1 迟到发现):启动后 10s 窗口内退出应用,poll 线程的 `_procname_restore` 未执行 → `+connect` 永久残留 rev.ini,之后禁用自动进服仍连旧服。`_procname_patch` 支持空值=剥离模式(清理残留,返回 None 不进 restore 链),`on_launch_click` 在 ConnectServer 为空时也调用剥离——`flet_app/main.py`
- **HIGH select_dark 双重包装**(task-4 迟到发现):F4 迁移后 `select_dark` 内部 `ft.dropdown.Option(o)` 再包装 main.py rank/combo 分支传入的 Option 列表 → 下拉选项 key 全部变成 Option 对象字符串化,下拉全坏(界面语言下拉显示 `{key: schinese, text: 简体…}`)。改为 `isinstance` 透传已构建的 Option——`flet_app/components/ui.py`
- **LOW 组件库 avatar API 错误**:`ui.avatar()` 用 `ft.ImageFit.COVER` 但 flet 0.86.5 无此属性(仅 `BoxFit`) — 死代码分支, 但按组件库签名传 image_path 即崩; 改 `ft.BoxFit.COVER`——`flet_app/components/ui.py`
- **LOW 工具卡垂直 spacer**:`tool_card` 内部 `ft.Container(expand=True)` 在 ListView 无界高度下有 RenderFlex 风险, 删除(卡高自适应)——`flet_app/components/ui.py`
- **LOW 孤儿控件清理**:`dir_label`/`path_chip` 在 round-5 重构后未挂载但持续更新(dead code), 已删除定义与全部更新语句(顶栏无文件名显示是设计决策, 极简)——`flet_app/main.py`
- **LOW tooltip 残留**:`LaunchButton.set_state('idle')` 不传 tooltip 时红点留“游戏运行中”; idle 显式复位“启动游戏”——`flet_app/components/ui.py`
- **MEDIUM 卸载游戏数据残留**:`[UninstallDelete]` 无条目, 卸载后 `{app}\game` 14GB 解压产物永久残留; 新增 `Type: filesandordirs; Name: "{app}\game"`(用户配置 {userappdata} 仍保留)——`packaging/installer.iss`
- **LOW 构建脚本错误**:`build_nuitka.bat` ISCC 提示路径不存在(Program Files (x86)) 修为实际位置; `make_dist.py` 死引用注释改为实际流程——`packaging/build_nuitka.bat`
- **LOW 注释修正**:字段网格注释“控件 height=40”实际 Dropdown/TextField 均 64(双列等高实际成立)——`flet_app/main.py`
- **LOW 注册表清理权限错误误报**:`_clean_reg_leftover` OpenKey 拒绝时误报“注册表干净”; 区分 FileNotFoundError(干净) 与权限类错误(报失败)——`app/tools.py`

## [2.2.0] - 2026-08-09

### 新增:已装用户更新包 (UPDATE_ONLY)

- `installer.iss` 增加 `UPDATE_ONLY` 条件编译开关,一份脚本两用:完整包(`ISCC installer.iss`, 内嵌游戏 4 文件) / 更新包(`ISCC /DUPDATE_ONLY`, 单文件 ~66MB 无游戏分块)
- 更新包:不带 chunks/不智能选盘/不做空间校验/不写 `.installed_ok`,靠 AppId 升级检测沿用原安装目录,游戏 14GB 完全不动,秒装;已端到端验证(装 2.2.0 完整包 → 装更新包 → 目录沿用/昵称保留/游戏未动/exe 启动正常)
- 产物:`dist\TangYuanLauncher-Update-2.2.0.exe`(单文件, `DiskSpanning=no` 条件化避免误分卷)

### 修复:第 7 轮深度审查 (deep-review round 7, 3 MEDIUM + 2 LOW + 窗口/工具链域 9 项)

- **MEDIUM 交错 section 索引分歧**:`ini_model._refresh_tail` 修复交错重复 section(A→B→A)——原实现扫到其他 section 头即 break,tail 截断到首个同名块,remove 后 `set()` 把新键插进第一个块;现改为跟踪当前 section 归属扫到文件尾,与全量重算语义完全一致(500 轮差分 + 定向场景全过)——`app/ini_model.py`
- **MEDIUM 多显示器窗口跳回主屏**:进出编辑页不再强制用主屏中心重定位,保持当前窗口中心(副屏拖动位置不丢);`_settle_position` 启动 2s 后仅在窗口仍在默认角标时才居中,不撤销用户已拖动位置;`resize_state` busy 时请求排队重放,快速连点不丢切换——`flet_app/main.py`
- **MEDIUM model=None 空表单**:`enter_editor` 的 OSError 失败路径(rev.ini 被独占锁/IO 错)也走默认模板兜底,不再留 model=None 空表单导致保存抛未捕获 AttributeError——`flet_app/main.py`
- **MEDIUM 卸载字体注册清理失效**:`installer.iss` 卸载校验路径拼接缺反斜杠(`'{app}\fonts' + FontFile` → `...\fontsHarmonyOS...`),与注册值永不相等 → 卸载后 HKCU Fonts 残留 7 个悬空注册项;补反斜杠并验证——`packaging/installer.iss`
- **MEDIUM 组件化合规 (rules.md §1)**:字段行控件迁移到组件库 `ui.input_dark`/`ui.select_dark`(补 width/height/on_change/on_select/filled 参数);新增 `ui.page_head`/`ui.field_grid`/`ui.rec_panel`/`ui.launch_split` 消除页面内联伪组件;主页昵称改用 `ui.nickname(size=24)`;design-system.md 标注 Flet 原生豁免(#1/#2/#9/#10/#11/#27/#28)——`flet_app/main.py`/`flet_app/components/ui.py`/`docs/design-system.md`
- **LOW tokens.md 补 Flet 常量映射列**:字号/圆角/布局/收编色各表补 Flet 常量( FONT_*/RADIUS_*/WIN_*/H_*/S_*/COL_LAUNCH_*/SHADOW_* ),违反 rules §2.2/§3.2 的登记缺口闭合——`docs/tokens.md`
- **MEDIUM 启动提速假幂等假成功**:`_speedup_startgame` 正则加行首锚定(banner/ECHO 文本里的 `timeout /t 2` 字样不再假报"已是快速启动"跳过真实延迟行;re.sub count=1 只改真实命令行)——`app/tools.py`
- **MEDIUM settings 非原子写**:`save_settings` 改临时文件 + fsync + `os.replace` 原子替换,防磁盘满/杀软中断留截断 JSON 导致目录设置静默遗忘;`main.py` 检查 `set_user_csgo_dir` 返回值,失败明确提示——`app/settings.py`/`flet_app/main.py`
- **LOW 备份路径可见**:`_update_items`/`_speedup_startgame` 写入失败时消息附带 `.bak_<ts>` 备份路径,供手动还原——`app/tools.py`
- **LOW 持久化目录播种**:启动时 `find_csgo_dir()` 未命中回退 `get_user_csgo_dir()`,持久化目录的 rev.ini 缺失时工具页/启动不再误报"未定位"——`flet_app/main.py`
- **LOW 弱命中不遮蔽注册表**:`_is_game_subdir` 仅含 Loader.exe 的弱目录不再抢先 return,加入候选由 `_looks_like_csgo_dir`(要求 csgo.exe)裁决,不抢注册表里的完整安装——`app/locator.py`
- **MEDIUM 回归脚本盲区**:`verify_tools.py` 补 `_update_items`(备份/覆盖/同大小异内容/幂等)、`_backup_file`、`_clean_reg_leftover`、`run_tool` bat 路径(成功/缺脚本/超时杀树)覆盖——`scripts/verify_tools.py`

### 修复:第 6 轮深度审查 (deep-review round 6, 回归 + 打包污染)

- **HIGH 回归修复**:修复工具「运行」按钮改用组件库 `RunButton` 后,状态切换仍用旧式 `content` 字符串赋值,把按钮的图标+文字结构整体替换成纯字符串 → 图标丢失。改为 `set_busy()` 驱动——`flet_app/main.py`
- **MEDIUM 打包污染**:`prepare_chunks.py` 分块收集把补丁阶段生成的 `.bak_<ts>` 备份打进发行分块(玩家安装目录多出冗余备份,每轮重跑累积)。`collect_files` 排除 `.bak_` 文件——`packaging/prepare_chunks.py`
- **清理**:配置卡片 hover 由组件库自带,移除 `main.py` 中重复的手动 hover 覆盖(仅保留 LaunchSplit 内联卡的 hover)
- **修复卸载误删字体注册**:卸载时删除 HKCU 字体注册前验证注册值指向本安装目录(避免误删别人同名字体注册)——`packaging/installer.iss`
- **版本号同步**:`build_release.bat`/`README_分发版.md` 文案 2.0.0→2.1.0(分发文档指向不存在的旧版本产物)
- **修复 prepare_chunks Low 项**:startgame.bat 补丁去尾空格(双空格 `timeout /t 2  /nobreak`);整文件替换加 src md5 跟常量一致性断言(防 assets 更新后忘同步常量导致幂等判定失效);分块加增量指纹缓存(manifest.json, 未变块跳过重压省 15-30 分钟);SolidCompression 保留并注明风险评估(分块不进 Solid 流无重插盘)——`packaging/prepare_chunks.py`/`packaging/installer.iss`

### 修复:第 5 轮深度审查 (deep-review round 5, 2 HIGH + 5 MEDIUM + 3 LOW)

- **HIGH 启动命令回填**:修复「启动命令」textarea 加载后不显示文件真实值的问题(v2 重构把控件从 Column 改为 Row,`populate_all` 的类型检查失配导致回填失效,用户编辑/点 chips 后保存会覆盖原启动参数)——`flet_app/main.py`
- **HIGH 配置入口锁死**:修复第二次进编辑页后 `loading` 互斥不复位、第三次点「配置」被永久拦截的问题——`flet_app/main.py`
- **MEDIUM 质量门**:ruff 全库清零(未使用导入/别名冗余/排序/BLE001/RUF013)
- **MEDIUM 文档一致性**:HTML 事实源 `.config-card:hover` 旧色 `#2563eb` 修正为矢车菊蓝,`tokens.md` 补齐 4 个 rgba 令牌
- **MEDIUM 组件库合规**:`status_bar`/`tool_card`/`config_card` 改用组件库实现(补 `statusMsg`/`expand`/`desc_lines` 参数),`risk_tag` 兼容中文风险等级,`design-system.md` 同步
- **MEDIUM 字体注册**:`installer.iss` 中 JetBrainsMono 注册值名补空格(与 ttf 实际 full name 一致,修复注册无效导致的字体回退)
- **MEDIUM 索引不变量**:`ini_model._refresh_tail` 处理重复 section 头(修复 remove/set 后增量索引与全量重算分歧)
- **LOW 工具脚本**:`verify_docs_consistency.py` 仓库根探测 + rgba 提取正则修正

## [2.1.0] - 2026-08-09

### 重大变更:UI 全面重设计(矢车菊蓝纯色主题)

推翻旧天蓝/紫色渐变主题,采用矢车菊蓝 #6495ED 纯色体系(无渐变、无发光),HTML 预览稿为唯一事实源,新增设计系统三件套文档:

- **新主题**:矢车菊蓝纯色 + 深色底,视觉评估多轮确认
- **主页**:110px 圆形纯图标启动按钮(无文字)、服务器状态胶囊实时显示真实在线人数(接入官网 `cs.suchitems.top/api/status`,30s 轮询,离线隐藏人数不编造)
- **编辑页**:784×600、双列字段卡等高、加载器 3:2 分栏 + 竖排推荐启动项、修复工具 2×2 网格
- **字体**:HarmonyOS Sans SC(界面)+ JetBrains Mono(等宽)随安装包分发并自动注册,杜绝陌生机器回退默认字体的"一细一粗"渲染缺陷
- **组件库**:新增 `flet_app/theme.py`(令牌)+ `flet_app/components/ui.py`(组件),约束写入 `docs/rules.md`
- **文档体系**:`docs/design-system.md` / `docs/tokens.md` / `docs/rules.md` 三件套 + `DESIGN.md` 按 HTML 事实源修正

## [2.0.0] - 2026-08-07

### 新增:内嵌游戏版安装器(装完即玩)

面向陌生人公开分发的重大升级——安装包内置完整游戏(14 GB 原样零精简),双击安装即可开玩:

- **一键安装完整游戏**:游戏数据以 12 个 7z 分块预压缩内嵌(5.7 GB),安装时自动解压到游戏目录,无需手动下载/解压游戏
- **智能默认选盘**:自动选择剩余空间最大的非系统盘,目录 `tangyuangame`;安装向导中**可自由修改安装路径**(支持浏览选择)
- **真实解压进度**:使用 7z 真实进度窗口,全程可见,拒绝假进度条
- **开箱即中文**:游戏语言自动设为简体中文,随机玩家名 `TangYuan + 8 位数字`(已有昵称不覆盖)
- **更新秒装**:重复安装检测到已装标记后跳过整段解压,数秒完成
- **免管理员安装**:普通用户即可安装,无需右键管理员
- **磁盘空间自检**:目标盘与系统盘空间不足时明确提示,防中途失败
- 安装器为**多文件分卷**(exe + 3 个 bin,每个 ≤2 GB):受 Inno 单文件 4.2 GB 结构上限约束,分卷后反而适配网盘单文件限制

### 新增:扩展皮肤库

- 安装包内置**扩展版物品库**(items_730.bin 由 992 → 1695 个唯一物品 ID,新增 29%)
- 库存/商店皮肤数量大幅增加,Howl 系列皮肤可用
- 替换幂等,原版自动备份

### 改进

- **游戏目录自动定位**:启动器支持「exe 同级 game\」目录探测(便携放置即识别)
- **进服更顺**:配置页「自动进入服务器」字段提至「常用设置」第一位
- **任务栏图标**:安装包补齐窗口图标文件,任务栏/Alt+Tab 显示汤圆图标
- **启动提速**:startgame.bat 等待 10 秒 → 2 秒(打包时固化,安装即生效)

### 修复

- **打包版修复工具资源缺失**: assets(Loader_opt23.exe/items_730.bin)现由构建脚本复制进发行包,
  修复「安装优化 Loader」「更新皮肤库」在发行版必然报错的问题(deep-review 4轮 HIGH)
- **自动进服恢复保护**: 启动窗口期(≤10s)内用户保存配置不再被 ProcName 恢复覆盖
  (restore 前比对当前行, 非 patch 写入形态则跳过; deep-review 4轮 LOW)
- **rank/combo 非法值提示**: 原值不在选项时显示 error_text 暴露真实值, 不再静默显示默认项
  (deep-review 4轮 MEDIUM)
- **+connect 剥离词边界**: 不再误剥 +connectivity 类参数(deep-review 4轮 LOW)
- **窗口定位竞态**: 启动 2s 内已进编辑页时, 延迟定位改用当前窗口尺寸计算中心(deep-review 4轮 MEDIUM)
- **防连点双加载**: 「配置」按钮快速连点不再触发重复文件加载(deep-review 4轮 LOW)
- ini_model 新建 section 空行分隔与索引不变量修复(差分测试 300 轮全过)
- 新增 section 后删除键导致的索引不一致修复
- procname 定位误匹配注释/值中的字面文本加固
- 修复工具幂等判断统一升级为 MD5 内容比较(防同大小不同内容误判)

### 打包流水线

- 新增 `packaging/prepare_chunks.py`:游戏补丁(提速/中文/皮肤库)+ 分块压缩 + 契约生成,全部幂等可重复执行
- 新增 `packaging/build_release.bat`:一键发行(分块 → Nuitka 构建 → Inno 打包)
- 版本号体系:启动器 2.0.0(游戏/配置版本仍为 1.35.7.7,互不混淆)

## [1.0.1] - 初始版本

- Rev.Ini 编辑器核心:Flet 桌面应用,暗色主题,无边框圆角窗口
- rev.ini 常用配置图形化编辑(启动参数、联机、玩家信息等)
- **nosteam 工具箱**(修复工具三件套):清理 RevEMU 注册表残留 / 安装优化 Loader(newloader.exe 并存方案,原件不覆盖)/ 更新扩展皮肤库
- 启动提速工具:startgame.bat 等待 10 秒 → 2 秒(需手动执行一次)
- 游戏目录自动定位:注册表 → 常见路径 → 手动指定
