@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET EM_SKIP_SYNC=1
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind

echo [1/4] Aborting any stuck git operations...
git rebase --abort 2>nul
git merge --abort 2>nul

echo [2/4] Stashing local changes...
git stash 2>nul

echo [3/4] Pulling latest from origin...
git pull origin main
if errorlevel 1 (
    echo WARNING: git pull failed - continuing with local version
    git rebase --abort 2>nul
)

echo [4/4] Restoring local changes...
git stash pop 2>nul

echo.
echo OLLAMA_HOST=%OLLAMA_HOST%
echo Starting Em...
echo.
python local_em.py --interactive
