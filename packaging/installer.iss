; 汤圆启动器 (RevIniEditor) — Inno Setup 安装脚本 v1.0.1
; 编译: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
; 注意: 本文件 UTF-8 编码, Inno 6 默认 Unicode 安装器, 中文安全

#define MyAppName "汤圆启动器"
#define MyAppNameEn "RevIniEditor"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "RevIniEditor"
#define MyAppExeName "RevIniEditor.exe"

[Setup]
AppId={{8F2C7E31-4D5B-4A6B-9C3E-1B2A4D5E6F70}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 卸载后删除配置目录(可选: %APPDATA%\RevIniEditor 由应用自行管理, 这里不删)
UninstallDisplayIcon={app}\{#MyAppExeName}
; 压缩设置
Compression=lzma2/max
SolidCompression=yes
; 输出
OutputDir=..\dist
OutputBaseFilename=TangYuanLauncher-Setup-{#MyAppVersion}
; 安装器图标(用应用图标)
SetupIconFile=assets\revini.ico
; 权限: 普通用户可装到 AppData, 管理员可装到 Program Files
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; 中文本地化
WizardStyle=modern
WizardResizable=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
; Nuitka 产物目录 (build\nuitka\main.dist\)
Source: "..\build\nuitka\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 应用自己的配置目录不删(用户数据), 如需完全清除改为:
; Type: filesandordirs; Name: "{userappdata}\RevIniEditor"
