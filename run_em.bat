@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET EM_SKIP_SYNC=1
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind

echo [1/2] Pulling latest from origin (hard reset)...
git fetch origin
git reset --hard origin/main

echo [2/2] Starting Em...
echo.
echo OLLAMA_HOST=%OLLAMA_HOST%
echo Starting Em...
echo.
python local_em.py
