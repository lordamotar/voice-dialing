@echo off
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo [ИНФО] Запуск настроек Voice Typing...
uv run python settings_gui.py
