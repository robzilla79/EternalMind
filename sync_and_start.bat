@echo off
REM ── EternalMind Startup with Cloud Sync ──────────────────────────────────
REM Run this instead of direct local_em.py to ensure sync runs first

setlocal

REM Load .env variables from environment
if exist ".env" (
    findstr /i "PERPLEXITY_API_KEY=" .env >nul 2>&1
    if errorlevel 1 (
        echo [WARN] PERPLEXITY_API_KEY not found in .env
        echo       Cloud sync will be skipped or may fail.
    )
)

echo ================================================================================
echo                    EternalMind — Cloud-Em Sync Startup
echo ================================================================================
echo.
echo Starting cloud sync before main loop...
echo.

REM Try to initialize sync (will fail gracefully if API key missing)
python -C "import sys; sys.path.insert(0, '.'); from tools.sync_cloud_em import sync_at_startup; sync_at_startup()" 2>nul

if errorlevel 1 (
    echo.
    echo [NOTICE] Sync may have failed — check .env and Perplexity app.
    echo         Continuing with local_em.py anyway...
    echo.
)

echo Starting main EternalMind loop...
echo ================================================================================

REM Run the actual Local-Em
python local_em.py

endlocal