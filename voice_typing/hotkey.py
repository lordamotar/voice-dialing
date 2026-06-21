import time
import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

class HotkeyListener:
    def __init__(self, hotkey_str: str, on_start: Callable[[], None], on_stop: Callable[[], None]):
        self.hotkey_str = hotkey_str
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_recording = False
        self.running = False
        self.thread = None

    def start(self):
        """Start the keyboard listener in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info(f"Слушатель горячих клавиш запущен для: {self.hotkey_str}")

    def stop(self):
        """Stop the keyboard listener."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Слушатель горячих клавиш остановлен.")

    def _listen_loop(self):
        """Loop to monitor hotkey press and release events."""
        # Check permissions and test the keyboard library first
        try:
            import keyboard
            # Run a dummy check to verify we have permissions (especially on Linux)
            keyboard.is_pressed("ctrl")
        except Exception as e:
            logger.error(f"Не удалось получить доступ к функциям клавиатуры: {e}")
            print(
                f"\n[ОШИБКА] Ошибка доступа к клавиатуре: {e}\n"
                "Если вы используете Linux, библиотека 'keyboard' требует прав суперпользователя (root) "
                "для глобального перехвата клавиш. Пожалуйста, запустите программу через: sudo uv run ...\n"
            )
            self.running = False
            return

        print(f"\n[ГОТОВО] Ожидание горячей клавиши '{self.hotkey_str}'...")
        print("-> Зажмите клавишу, чтобы начать говорить, и отпустите для завершения записи.")

        while self.running:
            try:
                # Check if configured hotkey combination is pressed
                import keyboard
                is_pressed = False
                try:
                    is_pressed = keyboard.is_pressed(self.hotkey_str)
                except ValueError as e:
                    logger.error(f"Некорректная горячая клавиша '{self.hotkey_str}': {e}")
                    print(
                        f"\n[ОШИБКА] Некорректный формат горячей клавиши '{self.hotkey_str}' в config.yaml.\n"
                        "Пожалуйста, проверьте имя клавиш (например: 'ctrl+space', 'left shift', 'caps lock')."
                    )
                    self.running = False
                    break

                if is_pressed:
                    if not self.is_recording:
                        self.is_recording = True
                        logger.info("Обнаружено нажатие горячей клавиши. Запуск записи...")
                        self.on_start()
                    
                    # Wait/block while the key is still held down
                    while self.running and keyboard.is_pressed(self.hotkey_str):
                        time.sleep(0.01)

                    # Key released
                    if self.is_recording:
                        self.is_recording = False
                        logger.info("Горячая клавиша отпущена. Остановка записи...")
                        self.on_stop()

                time.sleep(0.02)
            except Exception as e:
                logger.error(f"Ошибка в цикле опроса клавиатуры: {e}")
                time.sleep(0.5)
