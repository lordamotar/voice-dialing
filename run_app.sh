#!/bin/bash
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

if [ "$(uname)" == "Linux" ] && [ "$EUID" -ne 0 ]; then
    echo "Запуск от имени администратора (sudo) необходим для работы глобального перехвата клавиш в Linux."
    sudo env PATH="$PATH" uv run python main.py
else
    uv run python main.py
fi
