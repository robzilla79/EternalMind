@echo off
title EternalMind — Local-Em

echo.
echo  =========================================
echo   EternalMind — Starting Local-Em
echo  =========================================
echo.

REM ── Check Python is available ──────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Make sure Python is in your PATH.
    pause
    exit /b 1
)

REM ── Paths ───────────────────────────────────────────────────────────────────
set EM_DIR=%~dp0
set LOCAL_EM=%EM_DIR%local_em.py
set LISTENER=%EM_DIR%tools\telegram_listener.py

REM ── Start Telegram Listener in its own window ───────────────────────────────
echo  [1/2] Starting Telegram listener...
start "Em — Telegram Listener" cmd /k "cd /d %EM_DIR% && python %LISTENER%"

REM ── Small delay so listener is up before Em's first cycle ──────────────────
timeout /t 2 /nobreak >nul

REM ── Start Local-Em heartbeat loop ───────────────────────────────────────────
echo  [2/2] Starting Local-Em heartbeat loop...
echo.

:loop
    python "%LOCAL_EM%"
    echo.
    echo  --- Cycle complete. Waiting 2 minutes before next cycle... ---
    echo.
    timeout /t 120 /nobreak >nul
goto loop
