@echo off
set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..\..
set VENV_PYTHON=%REPO_ROOT%\runtime\.venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
  "%VENV_PYTHON%" -u "%SCRIPT_DIR%NativesPipeline.py"
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 -u "%SCRIPT_DIR%NativesPipeline.py"
) else (
  python -u "%SCRIPT_DIR%NativesPipeline.py"
)
