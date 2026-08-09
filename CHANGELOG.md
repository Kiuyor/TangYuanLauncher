# 更新日志

本项目的所有重要变更均记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

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
