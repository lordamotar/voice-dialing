@echo off
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo [ИНФО] Запуск Voice Typing...
uv run python main.py
pause
