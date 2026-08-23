@echo off
rem ============================================================
rem  TangYuan Launcher v2.2.4 release build pipeline (bundled game)
rem  1) game patches + chunk compression (prepare_chunks.py)
rem  2) copy 7z runtime (used by installer to extract)
rem  3) Nuitka build launcher (build_nuitka.bat)
rem  4) Inno Setup packaging (installer.iss)
rem  Output: dist\TangYuanLauncher-Setup-2.2.4.exe
rem ============================================================
setlocal
cd /d "%~dp0\.."
set ISCC=C:\Users\75017\AppData\Local\Programs\Inno Setup 6\ISCC.exe

echo [1/5] game patches + chunk compression (about 15-30 min)...
".venv311\Scripts\python.exe" packaging\prepare_chunks.py D:\re-la\CSGO build\chunks
if errorlevel 1 ( echo [ERROR] chunk step failed & exit /b 1 )

echo [2/5] copy 7z runtime...
if not exist build\7z mkdir build\7z
copy /y D:\7-Zip\7z.exe build\7z\ >nul || ( echo [ERROR] 7z.exe & exit /b 1 )
copy /y D:\7-Zip\7z.dll build\7z\ >nul || ( echo [ERROR] 7z.dll & exit /b 1 )

echo [3/5] Nuitka build launcher...
call packaging\build_nuitka.bat
if errorlevel 1 ( echo [ERROR] Nuitka failed & exit /b 1 )

echo [4/5] Inno Setup packaging...
"%ISCC%" packaging\installer.iss
if errorlevel 1 ( echo [ERROR] ISCC failed & exit /b 1 )

echo [5/5] done: dist\TangYuanLauncher-Setup-2.2.4.exe
endlocal
