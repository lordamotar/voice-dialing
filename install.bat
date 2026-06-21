@echo off
chcp 65001 >nul
echo ===================================================
echo  Установка зависимостей Voice Typing (RU/KZ)...
echo ===================================================

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ИНФО] Astral 'uv' не установлен. Устанавливаю 'uv'...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
) else (
    echo [ИНФО] Astral 'uv' уже установлен.
)

echo [ИНФО] Синхронизация зависимостей и установка Python...
uv sync

echo [ИНФО] Загрузка модели распознавания Vosk...
uv run python download_model.py

echo ===================================================
echo  Установка успешно завершена!
echo  Теперь вы можете настроить и запустить приложение:
echo  1. Для настроек: run_settings.bat
echo  2. Для запуска голосового ввода: run_app.bat
echo ===================================================
pause
