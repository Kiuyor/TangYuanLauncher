@echo off
rem Nuitka directory build - TangYuan Launcher v2.0.0
rem Usage: double-click or run from cmd
rem Output: build\nuitka\main.dist\  (copy engine + zip by make_dist.py)
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
  --windows-file-version=2.0.0.0 ^
  --windows-product-version=2.0.0.0 ^
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
echo [OK] build done: build\nuitka\main.dist\RevIniEditor.exe + engine + icon.ico
echo [OK] next: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
pause
endlocal
