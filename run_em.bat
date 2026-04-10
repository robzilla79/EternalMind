@echo off
SET OLLAMA_HOST=http://127.0.0.1:11434
SET PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%
cd C:\Users\RKSFAMILY\EternalMind
git pull --rebase
echo.
echo OLLAMA_HOST=%OLLAMA_HOST%
python local_em.py
echo.
echo -- Em finished. Press any key to close. --
pause
