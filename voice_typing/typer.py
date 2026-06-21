import os
import logging

logger = logging.getLogger(__name__)

class ActiveWindowTyper:
    def __init__(self, interval: float = 0.01):
        self.interval = interval
        # Import pyautogui locally to check if it's installed and warn if it fails
        try:
            import pyautogui
            # Disable pyautogui fail-safe pauses to speed up writing if needed,
            # but keep it default otherwise.
            pyautogui.PAUSE = 0.001
        except ImportError:
            logger.error("Библиотека 'pyautogui' не установлена.")

    def type_text(self, text: str):
        """Simulate keyboard typing of the text into the active window."""
        if not text:
            return

        # Ensure there is exactly one trailing space
        text_to_type = text
        if not text_to_type.endswith(" "):
            text_to_type += " "

        logger.info(f"Имитация ввода текста в активное окно: '{text_to_type}'")
        
        try:
            import keyboard
            import pyautogui
            import time
            
            # 1. Wait until modifier keys are physically released by the user (max 2 seconds timeout)
            start_wait = time.time()
            while time.time() - start_wait < 2.0:
                if not any(keyboard.is_pressed(key) for key in ["ctrl", "shift", "alt", "win"]):
                    break
                time.sleep(0.02)
            
            # 2. Programmatically force release of modifier keys to ensure clean OS key state
            for key in ["ctrl", "shift", "alt", "win"]:
                try:
                    pyautogui.keyUp(key)
                    keyboard.release(key)
                except Exception:
                    pass

            # 3. Direct Unicode writing via keyboard library (highly robust, layout-independent)
            try:
                keyboard.write(text_to_type)
                logger.info("Текст успешно введен через keyboard.write().")
                return
            except Exception as e:
                logger.warning(f"Сбой при вводе через keyboard.write(): {e}. Пробую pyautogui...")

            # 4. Fallback to direct key emulation via pyautogui
            pyautogui.write(text_to_type, interval=self.interval)
        except Exception as e:
            logger.error(f"Ошибка при симуляции ввода: {e}")
            print(
                f"\n[ОШИБКА] Не удалось имитировать ввод текста в окно.\n"
                f"Детали ошибки: {e}\n"
                "Примечание: На Linux убедитесь, что используется сессия X11 (а не Wayland), "
                "и установлены библиотеки xclip/xsel (команда: sudo apt-get install xclip)."
            )
