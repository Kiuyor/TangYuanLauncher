# 汤圆启动器 (RevIniEditor)

CS:GO rev.ini 配置工具 —— 暗黑二次元启动器风格。

## 使用说明

1. **安装**: 运行 `TangYuanLauncher-Setup-1.0.0.exe`,一路"下一步"即可。安装后桌面自动创建快捷方式。
2. **首次使用**: 启动后点击「配置」→ 选择你的 CS:GO 安装目录(包含 `Loader.exe` 和 `rev.ini` 的文件夹),程序会自动读取配置。
   - 找不到 CS:GO 目录时,程序会提示手动指定。
3. **启动游戏**: 主页点击「启动游戏」,程序会启动 Loader 并轮询 csgo.exe 反馈状态。

## 常见问题

- **杀软弹窗**: 本程序为 Nuitka 编译的独立 exe,未购买商业数字签名。若杀软误报,请添加信任/白名单。程序不上传任何数据。
- **配置保存在哪**: `%APPDATA%\RevIniEditor\settings.json`(记录你指定的 CS:GO 目录),卸载不会删除此文件。
- **更新**: 下载新版本安装包覆盖安装即可,配置不会丢失。

## 系统要求

- Windows 10/11 (64 位)
- CS:GO (Steam 版)

## 技术信息

- Python 3.11 + Flet 0.86.5 (Flutter 桌面引擎)
- Nuitka 4.1 编译 (目录版, 无 PyInstaller 特征, 误报率低)
- 版本: 1.0.0 (独立于游戏版本)
