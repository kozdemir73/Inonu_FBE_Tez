@echo off
setlocal
cd /d "%~dp0"
set "BUNDLED_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%~dp0tez_yonetim_gui.py"
  exit /b %ERRORLEVEL%
)
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py "%~dp0tez_yonetim_gui.py"
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%~dp0tez_yonetim_gui.py"
  exit /b %ERRORLEVEL%
)
echo Python bulunamadi. Lutfen Python 3 kurun veya tez_yonetim_gui.py dosyasini Python ile calistirin.
pause
