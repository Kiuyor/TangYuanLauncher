@echo off
setlocal
cd /d "%~dp0"

rem ============ Rev.Ini Editor launcher ============
rem Double-click      : normal mode
rem run.bat -h / --hot: hot reload (press r to restart after edits)
rem ================================================

rem Hermes desktop injects its own site-packages via PYTHONPATH;
rem clear it so this app uses ONLY its own .venv
set PYTHONPATH=

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] venv not found: .venv
    echo Create it: python -m venv .venv
    echo Then:      .venv\Scripts\pip install flet
    pause
    exit /b 1
)

if /i "%~1"=="-h" goto hot
if /i "%~1"=="--hot" goto hot

echo [START] Rev.Ini Editor
".venv\Scripts\python.exe" main.py
goto end

:hot
echo [START] Rev.Ini Editor (hot reload - press r to restart after edits)
".venv\Scripts\flet.exe" run main.py
goto end

:end
if errorlevel 1 (
    echo.
    echo [ERROR] abnormal exit, code %errorlevel%
    pause
)
endlocal
