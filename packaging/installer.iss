; 汤圆启动器 (TangYuanLauncher) — Inno Setup 安装脚本 v2.0.0 (内嵌游戏版)
; 编译: "C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
; 注意: 本文件 UTF-8 编码, Inno 6 默认 Unicode 安装器, 中文安全

#define MyAppName "汤圆启动器"
#define MyAppNameEn "TangYuanLauncher"
#define MyAppVersion "2.0.0"
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
UninstallDisplayIcon={app}\{#MyAppExeName}
; 压缩设置 (游戏分块已在 chunks.iss 里 nocompression, 不会被二次压缩)
Compression=lzma2/max
SolidCompression=yes
; 单文件安装器有 ~4.2GB 上限 (Inno/Windows 结构限制), 5.9G 内嵌游戏必须分卷
DiskSpanning=yes
DiskSliceSize=2147483647
; 输出
OutputDir=..\dist
OutputBaseFilename=TangYuanLauncher-Setup-{#MyAppVersion}
; 安装器图标(用应用图标)
SetupIconFile=assets\revini.ico
; 权限: 普通用户可装(智能默认盘为数据盘根, 无需管理员); 游戏启动时才弹 UAC (Loader 需要)
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; 中文本地化
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Messages]
; 目录页说明文案覆盖 (含「建议路径不含空格」提示)
SelectDirDesc=选择安装目录(建议路径不含空格)。游戏解压需要约 16 GB 空闲空间。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
; Nuitka 产物目录 (build\nuitka\main.dist\)
Source: "..\build\nuitka\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 解压器运行时 (7z.exe 依赖同目录 7z.dll)
Source: "..\build\7z\7z.exe"; DestDir: "{app}\7z"; Flags: ignoreversion
Source: "..\build\7z\7z.dll"; DestDir: "{app}\7z"; Flags: ignoreversion
; 游戏分块契约 (由 prepare_chunks.py 生成: #define ChunkCount + Source 行, 不带 [Files] 头)
#include "..\build\chunks.iss"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 应用自己的配置目录不删(用户数据), 如需完全清除: Type: filesandordirs; Name: "{userappdata}\RevIniEditor"

[Code]
const
  MARKER = 'game\.installed_ok';
  NAME_PREFIX = 'TangYuan';
  NAME_OLD = 'PlayerName = CSGO:PLAYER';
  NEED_TARGET_BYTES = 17179869184;   { 16 GB: 游戏 14G + 启动器 + 余量 }
  NEED_SYSTEM_BYTES = 2147483648;    { 2 GB: 解压临时目录位于系统盘, 单分块约 1.2G 需要 }

function GetDiskFreeSpaceEx(lpDirectoryName: string; var lpFreeBytesAvailableToCaller: Int64;
  var lpTotalNumberOfBytes: Int64; var lpTotalNumberOfFreeBytes: Int64): Boolean;
  external 'GetDiskFreeSpaceExW@kernel32.dll stdcall';
function GetDriveType(lpRootPathName: string): Longword;
  external 'GetDriveTypeW@kernel32.dll stdcall';

function DriveFreeBytes(DriveRoot: string): Int64;
var
  Free, Total, TotalFree: Int64;
begin
  Result := 0;
  if GetDiskFreeSpaceEx(DriveRoot, Free, Total, TotalFree) then
    Result := Free;
end;

function PickBestDefaultDir: String;
var
  SysDrive, Drive, Root, BestRoot: String;
  I: Integer;
  BestFree, Free: Int64;
begin
  SysDrive := GetEnv('SystemDrive');
  if Length(SysDrive) < 2 then
    SysDrive := 'C:';
  BestFree := -1;
  BestRoot := '';
  for I := Ord('C') to Ord('Z') do
  begin
    Drive := Chr(I) + ':';
    Root := Drive + '\';
    if UpperCase(Drive) = UpperCase(SysDrive) then
      Continue;
    if GetDriveType(Root) <> 3 then   { DRIVE_FIXED }
      Continue;
    Free := DriveFreeBytes(Root);
    if Free > BestFree then
    begin
      BestFree := Free;
      BestRoot := Root;
    end;
  end;
  if BestRoot = '' then
    Result := SysDrive + '\' + '{#MyAppNameEn}'
  else
    Result := BestRoot + 'tangyuangame';
end;

procedure InitializeWizard;
begin
  { 仅当用户没传 /DIR、也没手改(仍等于默认值)时才智能覆盖, 保留命令行与用户选择优先权 }
  if CompareText(WizardForm.DirEdit.Text, ExpandConstant('{autopf}\{#MyAppNameEn}')) = 0 then
    WizardForm.DirEdit.Text := PickBestDefaultDir;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Dir, Root: String;
  Free: Int64;
begin
  Result := True;
  if CurPageID <> wpSelectDir then
    Exit;
  Dir := WizardForm.DirEdit.Text;
  { 空格仅提示, 不阻止 }
  if Pos(' ', Dir) > 0 then
    MsgBox('提示: 安装路径包含空格。建议改为不含空格的路径(游戏组件对空格路径兼容性不佳)。' + #13#10 + '当前: ' + Dir, mbInformation, MB_OK);
  { 目标盘空间: 必须 >= 16 GB }
  if (Length(Dir) >= 3) and (Dir[2] = ':') then
    Root := Copy(Dir, 1, 3)
  else
    Root := Dir;
  Free := DriveFreeBytes(Root);
  if Free < NEED_TARGET_BYTES then
  begin
    MsgBox('目标磁盘剩余空间不足。安装需要至少 16 GB 空闲(游戏 14 GB + 解压临时空间)。' + #13#10 + #13#10 +
      '当前可用: ' + IntToStr(Free div (1024 * 1024 * 1024)) + ' GB' + #13#10 +
      '请选择空间更大的磁盘。', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  { 系统盘空间: 解压临时目录位于系统盘, 单分块约 1.2G }
  Free := DriveFreeBytes(GetEnv('SystemDrive') + '\');
  if Free < NEED_SYSTEM_BYTES then
  begin
    MsgBox('系统盘剩余空间不足(解压临时文件位于系统盘)。至少需要 2 GB。' + #13#10 + #13#10 +
      '当前可用: ' + IntToStr(Free div (1024 * 1024 * 1024)) + ' GB', mbError, MB_OK);
    Result := False;
    Exit;
  end;
end;

procedure ExtractGameChunks;
var
  I: Integer;
  ChunkName, TmpFile, OutDir, Params: String;
  ResultCode: Integer;
begin
  OutDir := ExpandConstant('{app}\game');
  if not DirExists(OutDir) then
    ForceDirectories(OutDir);
  for I := 0 to {#ChunkCount} - 1 do
  begin
    ChunkName := 'game.part' + Format('%.2d', [I]) + '.7z';
    TmpFile := ExpandConstant('{tmp}\') + ChunkName;
    ExtractTemporaryFile(ChunkName);
    Params := 'x -y "' + TmpFile + '" -o"' + OutDir + '"';
    if not Exec(ExpandConstant('{app}\7z\7z.exe'), Params, '', SW_SHOWNORMAL,
                ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
    begin
      MsgBox('游戏解压失败(分块 ' + ChunkName + ', 7z 退出码 ' + IntToStr(ResultCode) + ')。' + #13#10 +
        '请检查磁盘空间后重新运行安装程序(已解压部分会被覆盖修复)。', mbError, MB_OK);
      Abort;
    end;
    DeleteFile(TmpFile);
  end;
  SaveStringToFile(ExpandConstant('{app}\') + MARKER, 'ok', False);
end;

procedure ApplyRandomName;
var
  S, NewName: String;
  Raw: AnsiString;
  N: Longint;
begin
  { LoadStringFromFile 第二参是 var AnsiString (从 Compil32.exe 二进制签名挖出) }
  if not LoadStringFromFile(ExpandConstant('{app}\game\rev.ini'), Raw) then
    Exit;
  S := Raw;   { AnsiString -> String (rev.ini 为 ASCII, 无损) }
  { 已含随机昵称(重装/二次安装保持), 不重复生成 }
  if Pos('PlayerName = ' + NAME_PREFIX, S) > 0 then
    Exit;
  { Random 自动按时间播种(实测跨进程值不同), 8 位数字空间 1 亿, 撞名可忽略 }
  N := Random(100000000);
  NewName := NAME_PREFIX + Format('%.8d', [N]);
  if StringChangeEx(S, NAME_OLD, 'PlayerName = ' + NewName, True) > 0 then
  begin
    Raw := S;   { String -> AnsiString }
    SaveStringToFile(ExpandConstant('{app}\game\rev.ini'), Raw, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { 完整性标记存在 => 更新覆盖安装, 跳过游戏解压; 缺失 => 解压(含中断自愈) }
    if not FileExists(ExpandConstant('{app}\') + MARKER) then
      ExtractGameChunks;
    ApplyRandomName;
  end;
end;
