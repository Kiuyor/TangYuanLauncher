# 汤圆启动器 (TangYuan Launcher) · Rev.Ini 编辑器

CS:GO (Nosteam / RevLoader) 配置编辑器 + 启动器 — Flet 0.86.5 + Python 3.11 构建的暗色桌面应用。

## 功能

- **启动台主页**: 读取 CS:GO 目录头像 + `rev.ini` 昵称, 一键启动游戏 (Loader.exe, 自动提权, 轮询 csgo.exe 反馈); 服务器在线状态实时显示 (状态 API 真实查询)
- **深/浅/定时主题**: 标题栏一键切换深浅配色, 支持按时段自动切换 (如 19:00-07:00 深色, 跨午夜)
- **服务器直连**: 主页状态胶囊悬停展开分服面板 (在线状态/人数, 真实 API 查询), 点服务器行的「进入」即一次性 `+connect` 进服, 不改动常用设置; 平时启动跟随「自动进入服务器」配置
- **一键练枪**: 标题栏准星钮, 一键进入内置 aim_botz 本地练枪地图 (与进服启动互斥)
- **配置编辑**: 昵称 / 战队标签 / 界面语言 / 伪装段位 / 服役勋章等级 等 rev.ini 字段, 保存自动备份 (rev.ini.bak)
- **CFG 配置页**: 表单化编辑 s0up 预设 23 项 (灵敏度/准星/声音/性能), 范围校验标红不保存, 保存前自动备份
- **修改头像**: 本地选图 1:1 裁剪写入游戏头像 (64×64 dat + 启动器清晰版预览), 支持恢复出厂默认
- **启动命令**: 多行编辑启动参数 (Loader.ProcName) + 推荐参数 chips 一键添加 / 移除
- **修复工具**: 一键运行 CS:GO 内置维护脚本 (清缓存 / 修复 Steam 错误), 风险分级 (低/中/高) 显示

## 运行

```bat
run.bat
```

或直接 `.venv\Scripts\python.exe main.py`。依赖: Python 3.11 + `pip install flet==0.86.5`。

## 打包发布

Nuitka 目录版 + Inno Setup 安装器, 脚本与模板见 `packaging/` (build_nuitka.bat / installer.iss)。

## 数据

- 用户设置存于 `%APPDATA%\RevIniEditor` (settings.json)
- 配置编辑目标: CS:GO 安装目录下的 `rev.ini` (自动定位注册表 / 常见路径)
- 设计文档: `docs/` (preview v1.html 唯一事实源 + DESIGN/design-system/tokens/rules 四件套)

## 许可

本仓库(代码与素材)采用 **CC BY-NC-SA 4.0**(署名-非商业性使用-相同方式共享)许可, 详见 [LICENSE](LICENSE)。
