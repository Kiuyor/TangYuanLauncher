# 汤圆启动器 (TangYuan Launcher) · Rev.Ini 编辑器

CS:GO (Nosteam / RevLoader) 配置编辑器 + 启动器 — Flet 0.86.5 + Python 3.11 构建的暗色桌面应用。

## 功能

- **启动台主页**: 读取 CS:GO 目录 `platform/avatar.dat` 头像 + `rev.ini` 昵称, 一键启动游戏 (Loader.exe, 自动提权, 轮询 csgo.exe 反馈)
- **配置编辑**: 昵称 / 战队标签 / 界面语言 / 伪装段位 / 服役勋章等级 / 显示头像 等 rev.ini 字段, 保存自动备份 (rev.ini.bak)
- **启动命令**: 多行编辑启动参数 (Loader.ProcName) + 推荐参数 chips 一键添加 / 移除
- **自动进入服务器**: 填写 `IP:端口`, 启动游戏后自动追加 `+connect` 进服, 启动完成后恢复原文件
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
- 设计文档: `design/` (DESIGN.md / tokens.md)

## 许可

本仓库(代码与素材)采用 **CC BY-NC-SA 4.0**(署名-非商业性使用-相同方式共享)许可, 详见 [LICENSE](LICENSE)。
