@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET EM_SKIP_SYNC=1
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind

echo [1/2] Syncing from origin (safe merge - no wipe)...
git fetch origin
git merge --ff-only origin/main || git reset --hard origin/main

echo [2/2] Starting Em...
echo.
echo OLLAMA_HOST=%OLLAMA_HOST%
echo Starting Em...
echo.
python local_em.py
