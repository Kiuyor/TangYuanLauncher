@echo off
rem ============================================================
rem  TangYuan Launcher v2.3.1 release build pipeline (bundled game)
rem  1) game patches + chunk compression (prepare_chunks.py)
rem  2) copy 7z runtime (used by installer to extract)
rem  3) Nuitka build launcher (build_nuitka.bat)
rem  4) Inno Setup packaging (installer.iss)
rem  Output: dist\TangYuanLauncher-Setup-2.3.1.exe
rem ============================================================
setlocal
cd /d "%~dp0\.."
rem ISCC 定位: 本机自定义路径优先, 回退常见安装位置 (2026-08-30 审查)
set "ISCC=C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo [ERROR] ISCC.exe not found, install Inno Setup 6 or edit this script
  exit /b 1
)

echo [1/5] game patches + chunk compression (about 15-30 min)...
rem .venv = 活动虚拟环境 (run.bat 同款); .venv311 的 uv trampoline 已损坏
".venv\Scripts\python.exe" packaging\prepare_chunks.py D:\re-la\CSGO build\chunks
if errorlevel 1 ( echo [ERROR] chunk step failed & exit /b 1 )

echo [2/5] copy 7z runtime...
if not exist build\7z mkdir build\7z
set "SEVENZ_DIR=D:\7-Zip"
if not exist "%SEVENZ_DIR%\7z.exe" set "SEVENZ_DIR=C:\Program Files\7-Zip"
if not exist "%SEVENZ_DIR%\7z.exe" set "SEVENZ_DIR=C:\Program Files (x86)\7-Zip"
copy /y "%SEVENZ_DIR%\7z.exe" build\7z\ >nul || ( echo [ERROR] 7z.exe & exit /b 1 )
copy /y "%SEVENZ_DIR%\7z.dll" build\7z\ >nul || ( echo [ERROR] 7z.dll & exit /b 1 )

echo [3/5] Nuitka build launcher...
call packaging\build_nuitka.bat
if errorlevel 1 ( echo [ERROR] Nuitka failed & exit /b 1 )

echo [4/5] Inno Setup packaging...
"%ISCC%" packaging\installer.iss
if errorlevel 1 ( echo [ERROR] ISCC failed & exit /b 1 )

echo [5/5] done: dist\TangYuanLauncher-Setup-2.3.1.exe
endlocal
