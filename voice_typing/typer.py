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
            import pyautogui
            import keyboard
            import time
            
            # Wait a brief moment to allow the user to physically release key combination
            time.sleep(0.15)
            
            # Programmatically force release of modifier keys
            for key in ["ctrl", "shift", "alt", "win"]:
                try:
                    pyautogui.keyUp(key)
                    keyboard.release(key)
                except Exception:
                    pass

            # Try clipboard copy & paste (highly robust for Unicode and layout independent)
            if self._write_via_clipboard(text_to_type):
                logger.info("Текст успешно введен через буфер обмена (Paste).")
                return

            # Fallback to direct key emulation if clipboard fails
            logger.warning("Не удалось скопировать в буфер обмена. Использую прямую эмуляцию клавиш.")
            pyautogui.write(text_to_type, interval=self.interval)
        except Exception as e:
            logger.error(f"Ошибка при симуляции ввода: {e}")
            print(
                f"\n[ОШИБКА] Не удалось имитировать ввод текста в окно.\n"
                f"Детали ошибки: {e}\n"
                "Примечание: На Linux убедитесь, что используется сессия X11 (а не Wayland), "
                "и установлены библиотеки xclip/xsel (команда: sudo apt-get install xclip)."
            )

    def _write_via_clipboard(self, text: str) -> bool:
        """Paste text into active window using the clipboard, preserving user's original clipboard content."""
        if os.name != 'nt':
            return False

        import ctypes
        import time
        import pyautogui

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        # 1. Save original clipboard text
        orig_text = None
        if ctypes.windll.user32.OpenClipboard(None):
            try:
                h_data = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                if h_data:
                    p_mem = ctypes.windll.kernel32.GlobalLock(h_data)
                    if p_mem:
                        orig_text = ctypes.wstring_at(p_mem)
                        ctypes.windll.kernel32.GlobalUnlock(h_data)
            except Exception:
                pass
            finally:
                ctypes.windll.user32.CloseClipboard()

        # 2. Set new text to clipboard
        success = False
        if ctypes.windll.user32.OpenClipboard(None):
            try:
                ctypes.windll.user32.EmptyClipboard()
                text_bytes = (text + '\0').encode('utf-16-le')
                text_len = len(text_bytes)
                h_global = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, text_len)
                if h_global:
                    p_mem = ctypes.windll.kernel32.GlobalLock(h_global)
                    if p_mem:
                        ctypes.memmove(p_mem, text_bytes, text_len)
                        ctypes.windll.kernel32.GlobalUnlock(h_global)
                        if ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_global):
                            success = True
            except Exception:
                pass
            finally:
                ctypes.windll.user32.CloseClipboard()

        if not success:
            return False

        # 3. Simulate Ctrl+V paste action
        pyautogui.hotkey('ctrl', 'v')
        
        # 4. Restore original clipboard text after a tiny delay
        if orig_text is not None:
            time.sleep(0.12)  # Wait for paste to complete in active window
            if ctypes.windll.user32.OpenClipboard(None):
                try:
                    ctypes.windll.user32.EmptyClipboard()
                    text_bytes = (orig_text + '\0').encode('utf-16-le')
                    text_len = len(text_bytes)
                    h_global = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, text_len)
                    if h_global:
                        p_mem = ctypes.windll.kernel32.GlobalLock(h_global)
                        if p_mem:
                            ctypes.memmove(p_mem, text_bytes, text_len)
                            ctypes.windll.kernel32.GlobalUnlock(h_global)
                            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_global)
                except Exception:
                    pass
                finally:
                    ctypes.windll.user32.CloseClipboard()

        return True
