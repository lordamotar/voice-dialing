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
        from ctypes import wintypes
        import time
        import pyautogui

        # Declare ctypes return and argument types for 64-bit safety on Windows
        HGLOBAL = wintypes.HANDLE
        HWND = wintypes.HWND
        UINT = wintypes.UINT
        HANDLE = wintypes.HANDLE
        LPVOID = wintypes.LPVOID
        SIZE_T = ctypes.c_size_t

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        OpenClipboard = user32.OpenClipboard
        OpenClipboard.argtypes = [HWND]
        OpenClipboard.restype = wintypes.BOOL

        CloseClipboard = user32.CloseClipboard
        CloseClipboard.argtypes = []
        CloseClipboard.restype = wintypes.BOOL

        EmptyClipboard = user32.EmptyClipboard
        EmptyClipboard.argtypes = []
        EmptyClipboard.restype = wintypes.BOOL

        GetClipboardData = user32.GetClipboardData
        GetClipboardData.argtypes = [UINT]
        GetClipboardData.restype = HANDLE

        SetClipboardData = user32.SetClipboardData
        SetClipboardData.argtypes = [UINT, HANDLE]
        SetClipboardData.restype = HANDLE

        GlobalAlloc = kernel32.GlobalAlloc
        GlobalAlloc.argtypes = [UINT, SIZE_T]
        GlobalAlloc.restype = HGLOBAL

        GlobalLock = kernel32.GlobalLock
        GlobalLock.argtypes = [HGLOBAL]
        GlobalLock.restype = LPVOID

        GlobalUnlock = kernel32.GlobalUnlock
        GlobalUnlock.argtypes = [HGLOBAL]
        GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        # 1. Save original clipboard text
        orig_text = None
        if OpenClipboard(None):
            try:
                h_data = GetClipboardData(CF_UNICODETEXT)
                if h_data:
                    p_mem = GlobalLock(h_data)
                    if p_mem:
                        orig_text = ctypes.wstring_at(p_mem)
                        GlobalUnlock(h_data)
            except Exception as e:
                logger.debug(f"Ошибка при сохранении буфера: {e}")
            finally:
                CloseClipboard()

        # 2. Set new text to clipboard
        success = False
        if OpenClipboard(None):
            try:
                EmptyClipboard()
                text_bytes = (text + '\0').encode('utf-16-le')
                text_len = len(text_bytes)
                h_global = GlobalAlloc(GMEM_MOVEABLE, text_len)
                if h_global:
                    p_mem = GlobalLock(h_global)
                    if p_mem:
                        ctypes.memmove(p_mem, text_bytes, text_len)
                        GlobalUnlock(h_global)
                        if SetClipboardData(CF_UNICODETEXT, h_global):
                            success = True
            except Exception as e:
                logger.debug(f"Ошибка при записи в буфер: {e}")
            finally:
                CloseClipboard()

        if not success:
            return False

        # 3. Simulate Ctrl+V paste action
        pyautogui.hotkey('ctrl', 'v')
        
        # 4. Restore original clipboard text after a tiny delay
        if orig_text is not None:
            time.sleep(0.12)  # Wait for paste to complete in active window
            if OpenClipboard(None):
                try:
                    EmptyClipboard()
                    text_bytes = (orig_text + '\0').encode('utf-16-le')
                    text_len = len(text_bytes)
                    h_global = GlobalAlloc(GMEM_MOVEABLE, text_len)
                    if h_global:
                        p_mem = GlobalLock(h_global)
                        if p_mem:
                            ctypes.memmove(p_mem, text_bytes, text_len)
                            GlobalUnlock(h_global)
                            SetClipboardData(CF_UNICODETEXT, h_global)
                except Exception as e:
                    logger.debug(f"Ошибка при восстановлении буфера: {e}")
                finally:
                    CloseClipboard()

        return True
