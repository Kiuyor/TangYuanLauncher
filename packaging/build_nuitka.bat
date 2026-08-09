@echo off
rem Nuitka directory build - TangYuan Launcher v2.2.1
rem Usage: double-click or run from cmd
rem Output: build\nuitka\main.dist\  (引擎拷贝见下方 xcopy; 游戏分块压缩见 prepare_chunks.py)
setlocal
cd /d "%~dp0\.."
set "PYTHONPATH="
set "FLET_ENGINE=%USERPROFILE%\.flet\client\flet-desktop-full-0.86.5\flet"

".venv311\Scripts\python.exe" -m nuitka --standalone ^
  --output-filename=RevIniEditor.exe ^
  --output-dir=build\nuitka ^
  --windows-console-mode=disable ^
  --windows-icon-from-ico=packaging\assets\revini.ico ^
  --windows-product-name="TangYuanLauncher" ^
  --windows-company-name="RevIniEditor" ^
  --windows-file-description="CS:GO rev.ini config tool" ^
  --windows-file-version=2.2.1.0 ^
  --windows-product-version=2.2.1.0 ^
  --include-package=flet ^
  --include-package=flet_desktop ^
  --include-package-data=flet ^
  --include-package-data=flet_desktop ^
  --nofollow-import-to=flet_cli ^
  --nofollow-import-to=cookiecutter ^
  --nofollow-import-to=pytest ^
  --nofollow-import-to=flet_web ^
  --enable-plugin=no-qt ^
  main.py

if errorlevel 1 (
  echo [ERROR] Nuitka build failed, exit %errorlevel%
  pause
  exit /b 1
)

rem Post-build: copy Flutter engine (Nuitka include-data-dir skips binaries)
if exist "build\nuitka\main.dist\engine" rmdir /s /q "build\nuitka\main.dist\engine"
xcopy /e /i /q "%FLET_ENGINE%" "build\nuitka\main.dist\engine\" >nul
if not exist "build\nuitka\main.dist\engine\flet.exe" (
  echo [ERROR] engine copy failed
  pause
  exit /b 1
)
rem Window icon: launcher main.py looks for icon.ico beside the exe (taskbar/Alt+Tab)
copy /y "packaging\assets\revini.ico" "build\nuitka\main.dist\icon.ico" >nul
if not exist "build\nuitka\main.dist\icon.ico" (
  echo [ERROR] icon copy failed
  pause
  exit /b 1
)
rem Built-in repair-tool assets: app\tools.py resolves ASSETS_DIR next to the exe in
rem packaged builds (app package is embedded, __file__ unreliable) - ship them here
mkdir "build\nuitka\main.dist\assets" >nul 2>nul
copy /y "assets\Loader_opt23.exe" "build\nuitka\main.dist\assets\" >nul
copy /y "assets\items_730.bin" "build\nuitka\main.dist\assets\" >nul
if not exist "build\nuitka\main.dist\assets\Loader_opt23.exe" (
  echo [ERROR] assets copy failed
  pause
  exit /b 1
)
echo [OK] build done: build\nuitka\main.dist\RevIniEditor.exe + engine + icon.ico + assets
echo [OK] next: "C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
pause
endlocal
