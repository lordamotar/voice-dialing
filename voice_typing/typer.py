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
            # GetAsyncKeyState VK Codes:
            # 0x10: VK_SHIFT, 0x11: VK_CONTROL, 0x12: VK_MENU (ALT)
            # 0xA0: VK_LSHIFT, 0xA1: VK_RSHIFT
            # 0xA2: VK_LCONTROL, 0xA3: VK_RCONTROL
            # 0xA4: VK_LMENU (LALT), 0xA5: VK_RMENU (RALT)
            # 0x5B: VK_LWIN, 0x5C: VK_RWIN
            get_async_key_state = ctypes.windll.user32.GetAsyncKeyState
            for vk in [0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C]:
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

def force_release_modifiers_win():
    """Send simulated KEYUP events for all modifiers via Windows API to clear logical key states."""
    if platform.system() == "Windows":
        try:
            import ctypes
            keybd_event = ctypes.windll.user32.keybd_event
            # VK Codes: LSHIFT(0xA0), RSHIFT(0xA1), LCTRL(0xA2), RCTRL(0xA3), LALT(0xA4), RALT(0xA5), LWIN(0x5B), RWIN(0x5C)
            # KEYEVENTF_KEYUP = 0x0002
            for vk in [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C]:
                keybd_event(vk, 0, 0x0002, 0)
        except Exception as e:
            logger.debug(f"Ошибка force_release_modifiers_win: {e}")

def type_unicode_win(text: str):
    """Simulate keyboard input by sending Unicode events directly via Win32 SendInput.
    This method bypasses scan code/virtual key mapping, which completely prevents 
    triggering modifier shortcuts (like Ctrl+L) even if physical modifier keys are held.
    """
    import ctypes
    from ctypes import wintypes
    
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]
        
    SendInput = ctypes.windll.user32.SendInput
    INPUT_KEYBOARD = 1
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    
    for char in text:
        # Encode as UTF-16 Little Endian to support surrogate pairs (e.g. emojis)
        utf16_units = char.encode('utf-16-le')
        for i in range(0, len(utf16_units), 2):
            val = int.from_bytes(utf16_units[i:i+2], byteorder='little')
            
            # Key down
            inp_down = INPUT()
            inp_down.type = INPUT_KEYBOARD
            inp_down.union.ki.wVk = 0
            inp_down.union.ki.wScan = val
            inp_down.union.ki.dwFlags = KEYEVENTF_UNICODE
            
            # Key up
            inp_up = INPUT()
            inp_up.type = INPUT_KEYBOARD
            inp_up.union.ki.wVk = 0
            inp_up.union.ki.wScan = val
            inp_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            
            events = (INPUT * 2)(inp_down, inp_up)
            SendInput(2, events, ctypes.sizeof(INPUT))
            
            # Tiny sleep to let the target window process input messages properly
            time.sleep(0.001)

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
            if platform.system() == "Windows":
                force_release_modifiers_win()
            
            try:
                import keyboard
                import pyautogui
                for key in ["ctrl", "shift", "alt", "win"]:
                    try:
                        pyautogui.keyUp(key)
                        keyboard.release(key)
                    except Exception:
                        pass
            except Exception:
                pass

            # 3. Direct Win32 SendInput Unicode typing (highest reliability, ignores modifier state)
            if platform.system() == "Windows":
                try:
                    type_unicode_win(text_to_type)
                    logger.info("Текст успешно введен через Direct Win32 SendInput Unicode.")
                    return
                except Exception as e:
                    logger.warning(f"Сбой при вводе через Direct Win32 Unicode: {e}. Пробую стандартные методы...")

            # 4. Standard Python libraries fallback
            import keyboard
            try:
                keyboard.write(text_to_type)
                logger.info("Текст успешно введен через keyboard.write().")
                return
            except Exception as e:
                logger.warning(f"Сбой при вводе через keyboard.write(): {e}. Пробую pyautogui...")

            # 5. Last fallback via pyautogui
            import pyautogui
            pyautogui.write(text_to_type, interval=self.interval)
        except Exception as e:
            logger.error(f"Ошибка при симуляции ввода: {e}")
            print(
                f"\n[ОШИБКА] Не удалось имитировать ввод текста в окно.\n"
                f"Детали ошибки: {e}\n"
                "Примечание: На Linux убедитесь, что используется сессия X11 (а не Wayland), "
                "и установлены библиотеки xclip/xsel (команда: sudo apt-get install xclip)."
            )
