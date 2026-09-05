# flet_app/main.py

> 最后核对: 2026-09-05 · 共 3042 行

## 一句话职责

全部视图装配与业务逻辑：主页启动台、编辑页四导航、修改头像页、主题三态、游戏
启动链——一个 `main(page)` 入口，闭包持有全部状态。

## 结构（按视图域，单文件内分节）

- **状态**：`st` 字典（view / theme_epoch / editor_epoch / home_epoch / cfg_dirty /
  tool_timeout / csgo_dir…）；epoch 计数是"主题换装了几次"的时钟，各视图记自己的
  构建时点。
- **主页**：`_rebuild_home()` 整组重建（主题换装/返回主页时）；启动钮/服务器状态
  轮询（server_epoch 停转纪律）。
- **编辑页**：页面工厂 `build_page` / `build_tools_page` / `build_cfg_page`（工厂
  便于换装重建）；`_rebuild_editor_surfaces()` 保留未保存修改（CFG `reload=not
  cfg_dirty`、rev.ini 从 model 回填）与当前导航页；`show_editor()` 开头的 epoch
  检查触发惰性重建。
- **主题**：`_apply_theme_mode` / `_save_period` / `_apply_scheme_change`（定时轮询
  60s）三路径 + `_redress_nonhome()`（2026-09-05 拷问定稿：编辑/头像页停留时切主题
  **就地即时换装**，经 show_editor/show_avatar 的 epoch 检查触发；原惰性策略"返回
  主页后应用"已废——人站在页面上等不到"下次进入"）。头像/编辑页以
  `view_switcher.content is avatar_view` 身份区分。
- **启动链**：目录缺失先 `_install_loader(d, None)` 静默就位 newloader →
  `_procname_patch`（+connect/+map 临时令牌，原子写）→ UAC：ShellExecuteW 后台线程，
  弹窗前"等待管理员确认…"提示、取消复位 + 红字 → 批准后统一轮询 csgo.exe。
- **其他**：`_procname_restore` 恢复原 ProcName；`on_nav_change` 切页确认丢弃语义；
  `show_home_error` epoch 防过期 Timer。

## 公开接口

`main(page)` — 唯一入口（根 main.py 经 ft.run 调用）。

## 关键实现决策

- **P1 holder 模式**：换装重建重绑闭包变量不会替换树上旧对象——status_bar 经
  `status_bar_holder.content` 换入（2026-09-05 审查）。
- 启动命令 `+exec auto.cfg` 检测容错（双空格/引号变体）。
- 写盘纪律：`_procname_patch/_restore/_cfg_add_exec` 均原子写。

## 坑与禁忌

- 本文件内**禁止 from-import theme**（冻结深色值）；worker 线程更新 UI 必须回
  `page.run_thread`（H1）。
- 无条件 `_rebuild_home()` 不能在编辑页调用（窗口停在编辑尺寸会状态脱节）——非主页
  换装走 `_redress_nonhome()`。
- `ft.app` 的 session 回调里构建页面，任何控件构造 kwargs 错误=启动即崩（ruff 不报，
  verify_tools 有构造冒烟）。

## 依赖与被依赖

- 依赖：components/ui、theme、app/{tools,locator,settings,ini_model,fields,
  cfg_fields,avatar}。
- 被依赖：根 `main.py`、`scripts/verify_tools`（导入冒烟）。

## 关联文档

- docs/DESIGN.md（页面规格与坑位表）、docs/design-system.md
- [flet_app/theme](theme.md) / [flet_app/components/ui](components/ui.md)
