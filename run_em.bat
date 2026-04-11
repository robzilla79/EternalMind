@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind

REM Stash any local changes before pulling so rebase doesn't fail
git stash --quiet
git pull --rebase --quiet
git stash pop --quiet 2>nul

echo.
echo OLLAMA_HOST=%OLLAMA_HOST%
python local_em.py
