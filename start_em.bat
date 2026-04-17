@echo off
title EternalMind — Local-Em

echo.
echo  =========================================
echo   EternalMind — Starting Local-Em
echo  =========================================
echo.

REM ── Ollama environment overrides ──────────────────────────────────────────────
set OLLAMA_HOST=http://127.0.0.1:11434
set OLLAMA_CONTEXT_LENGTH=65536
set OLLAMA_FLASH_ATTENTION=1

echo  Ollama context: %OLLAMA_CONTEXT_LENGTH%
echo  Flash attention: %OLLAMA_FLASH_ATTENTION%
echo.

REM ── Check Python is available ──────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Make sure Python is in your PATH.
    pause
    exit /b 1
)

REM ── Paths ─────────────────────────────────────────────────────────────────
set EM_DIR=%~dp0
set LOCAL_EM=%EM_DIR%local_em.py
set LISTENER=%EM_DIR%tools\telegram_listener.py

REM ── Rebuild local-em model with updated Modelfile ────────────────────────────
echo  [0/2] Rebuilding local-em model (picks up Modelfile changes)...
ollama create local-em -f "%EM_DIR%Modelfile.qwen3"
echo.

REM ── Start Telegram Listener in its own window ──────────────────────────────
echo  [1/2] Starting Telegram listener...
start "Em — Telegram Listener" cmd /k "cd /d %EM_DIR% && python %LISTENER%"

REM ── Small delay so listener is up before Em's first cycle ────────────────────
timeout /t 2 /nobreak >nul

REM ── Start Local-Em heartbeat loop ─────────────────────────────────────────────
echo  [2/2] Starting Local-Em heartbeat loop...
echo.

:loop
    python "%LOCAL_EM%"
    echo.
    echo  --- Cycle complete. Waiting 2 minutes before next cycle... ---
    echo.
    timeout /t 120 /nobreak >nul
goto loop
