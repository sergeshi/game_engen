@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  start "GAME ENGEN local server" cmd /k "cd /d "%~dp0" && py -m http.server 8000"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    start "GAME ENGEN local server" cmd /k "cd /d "%~dp0" && python -m http.server 8000"
  ) else (
    echo Python was not found. Install Python 3 or run: npx http-server -p 8000
    pause
    exit /b 1
  )
)
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:8000/index.html
endlocal
