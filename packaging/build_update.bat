@echo off
cd /d D:\re-la\revini-editor
"C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe" /DUPDATE_ONLY packaging\installer.iss
if errorlevel 1 ( echo [ERROR] ISCC failed & exit /b 1 )
echo [done] dist\TangYuanLauncher-Update-2.3.1.exe