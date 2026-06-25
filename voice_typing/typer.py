import os
import logging
import platform
import time

logger = logging.getLogger(__name__)

def is_modifier_pressed() -> bool:
    """Check if any modifier keys (Ctrl, Shift, Alt, Win) are physically pressed."""
    if platform.system() == "Windows":
        try:
            import ctypes
            # GetAsyncKeyState: 0x11 (VK_CONTROL), 0x10 (VK_SHIFT), 0x12 (VK_MENU/ALT), 0x5B (VK_LWIN), 0x5C (VK_RWIN)
            # If the high-order bit is 1 (0x8000), the key is down.
            get_async_key_state = ctypes.windll.user32.GetAsyncKeyState
            for vk in [0x11, 0x10, 0x12, 0x5B, 0x5C]:
                if get_async_key_state(vk) & 0x8000:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Ошибка GetAsyncKeyState: {e}")
            
    # Fallback using keyboard library
    try:
        import keyboard
        return any(keyboard.is_pressed(key) for key in ["ctrl", "shift", "alt", "windows"])
    except Exception:
        return False

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
            
            # 1. Wait until modifier keys are physically released by the user (max 2 seconds timeout)
            start_wait = time.time()
            released = False
            while time.time() - start_wait < 2.0:
                if not is_modifier_pressed():
                    released = True
                    break
                time.sleep(0.01)
            
            if released:
                # Small pause to let the OS process the key release event and settle keyboard state
                time.sleep(0.05)
            else:
                logger.warning("Превышено время ожидания отпускания клавиш-модификаторов. Ввод может вызвать горячие клавиши.")
            
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
