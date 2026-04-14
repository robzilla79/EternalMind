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

python em_daemon.py

echo.
echo Daemon exited.
pause
