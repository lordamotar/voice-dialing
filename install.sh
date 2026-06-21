#!/bin/bash
set -e

echo "==================================================="
echo " Установка зависимостей Voice Typing (RU/KZ)..."
echo "==================================================="

if ! command -v uv &> /dev/null; then
    echo "[ИНФО] Astral 'uv' не найден. Устанавливаю 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "[ИНФО] Astral 'uv' уже установлен."
fi

echo "[ИНФО] Синхронизация зависимостей и установка Python..."
uv sync

echo "[ИНФО] Загрузка модели распознавания Vosk..."
uv run python download_model.py

if [ "$(uname)" == "Linux" ]; then
    echo ""
    echo "==================================================="
    echo " ВАЖНОЕ ПРИМЕЧАНИЕ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ LINUX:"
    echo "1. Библиотека 'keyboard' требует root-прав на Linux."
    echo "   Запуск голосового ввода: sudo uv run python main.py"
    echo "2. Установите xclip и xsel для симуляции ввода:"
    echo "   sudo apt-get install xclip xsel"
    echo "3. Убедитесь, что вы работаете в сессии X11 (Wayland не поддерживается)."
    echo "==================================================="
fi

echo ""
echo "Установка успешно завершена!"
echo "Вы можете запустить панель настроек: ./run_settings.sh"
echo "Или запустить голосовой ввод: ./run_app.sh"
echo "==================================================="
echo ""
