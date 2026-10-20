@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py main.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python main.py
  ) else (
    echo Python 3 was not found. Install Python 3.10 or newer.
    pause
    exit /b 1
  )
)
if errorlevel 1 pause
endlocal
