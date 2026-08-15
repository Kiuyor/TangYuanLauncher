@echo off
rem ============================================================
rem  汤圆启动器 v2.2.2 发行版构建流水线 (内嵌游戏版)
rem  1) 游戏补丁 + 分块压缩 (prepare_chunks.py)
rem  2) 拷贝 7z 运行时 (安装器解压用)
rem  3) Nuitka 构建启动器 (build_nuitka.bat)
rem  4) Inno Setup 打包 (installer.iss)
rem  产物: dist\TangYuanLauncher-Setup-2.2.2.exe
rem ============================================================
setlocal
cd /d "%~dp0\.."
set ISCC=C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe

echo [1/5] 游戏补丁 + 分块压缩 (约 15-30 分钟)...
".venv311\Scripts\python.exe" packaging\prepare_chunks.py D:\re-la\CSGO build\chunks
if errorlevel 1 ( echo [ERROR] 分块失败 & exit /b 1 )

echo [2/5] 拷贝 7z 运行时...
if not exist build\7z mkdir build\7z
copy /y D:\7-Zip\7z.exe build\7z\ >nul || ( echo [ERROR] 7z.exe & exit /b 1 )
copy /y D:\7-Zip\7z.dll build\7z\ >nul || ( echo [ERROR] 7z.dll & exit /b 1 )

echo [3/5] Nuitka 构建启动器...
call packaging\build_nuitka.bat
if errorlevel 1 ( echo [ERROR] Nuitka 失败 & exit /b 1 )

echo [4/5] Inno Setup 打包...
"%ISCC%" packaging\installer.iss
if errorlevel 1 ( echo [ERROR] ISCC 失败 & exit /b 1 )

echo [5/5] 完成: dist\TangYuanLauncher-Setup-2.2.2.exe
endlocal
