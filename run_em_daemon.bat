@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET EM_SKIP_SYNC=0
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind

echo ===============================================
echo   EternalMind Daemon
echo   Persistent foreground/background architecture
echo   Ctrl+C for graceful shutdown
echo   Or write 'shutdown' to memory/interrupt.md
echo ===============================================
echo.

REM -- Launch Telegram listener in its own window --
echo [1/2] Starting Telegram listener...
start "Em -- Telegram Listener" cmd /k "cd /d C:\Users\RKSFAMILY\EternalMind && python tools\telegram_listener.py"

REM -- Small delay so listener is ready before first daemon cycle --
timeout /t 2 /nobreak >nul

REM -- Start the main daemon --
echo [2/2] Starting EternalMind daemon...
echo.

python em_daemon.py

echo.
echo Daemon exited.
pause
