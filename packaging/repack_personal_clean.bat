@echo off
cd /d D:\re-la\revini-editor
echo [1/2] prepare_chunks (incremental)...
".venv\Scripts\python.exe" packaging\prepare_chunks.py D:\re-la\CSGO build\chunks
if errorlevel 1 ( echo [ERROR] chunk step failed & exit /b 1 )
echo [2/2] ISCC...
"C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
if errorlevel 1 ( echo [ERROR] ISCC failed & exit /b 1 )
echo [done] dist\TangYuanLauncher-Setup-2.3.1.exe
