import time
import sys

def test_pyautogui_direct():
    import pyautogui
    print("\n--- Тест 1: Прямой ввод через PyAutoGUI ---")
    print("У вас есть 3 секунды, чтобы переключить фокус на Блокнот...")
    time.sleep(3)
    text = "Проверка ввода PyAutoGUI"
    pyautogui.write(text, interval=0.01)
    print("Готово. Текст напечатался?")

def test_keyboard_direct():
    import keyboard
    print("\n--- Тест 2: Прямой Unicode-ввод через Keyboard ---")
    print("У вас есть 3 секунды, чтобы переключить фокус на Блокнот...")
    time.sleep(3)
    text = "Привет! Проверка прямой Unicode печати через библиотеку keyboard."
    keyboard.write(text)
    print("Готово. Текст напечатался?")

def test_clipboard_fast():
    import ctypes
    import pyautogui
    print("\n--- Тест 3: Буфер обмена с быстрой очисткой (120 мс) ---")
    print("У вас есть 3 секунды, чтобы переключить фокус на Блокнот...")
    time.sleep(3)
    text = "Проверка буфера 120мс"
    if run_clipboard_test(text, 0.12):
        print("Готово. Текст напечатался?")
    else:
        print("Ошибка записи в буфер.")

def test_clipboard_slow():
    import ctypes
    import pyautogui
    print("\n--- Тест 4: Буфер обмена с медленной очисткой (600 мс) ---")
    print("У вас есть 3 секунды, чтобы переключить фокус на Блокнот...")
    time.sleep(3)
    text = "Проверка буфера 600мс"
    if run_clipboard_test(text, 0.60):
        print("Готово. Текст напечатался?")
    else:
        print("Ошибка записи в буфер.")

def run_clipboard_test(text, delay):
    import ctypes
    from ctypes import wintypes
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

    # Save
    orig_text = None
    if OpenClipboard(None):
        try:
            h_data = GetClipboardData(CF_UNICODETEXT)
            if h_data:
                p_mem = GlobalLock(h_data)
                if p_mem:
                    orig_text = ctypes.wstring_at(p_mem)
                    GlobalUnlock(h_data)
        except Exception:
            pass
        finally:
            CloseClipboard()

    # Set
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
        except Exception:
            pass
        finally:
            CloseClipboard()

    if not success:
        return False

    # Paste
    pyautogui.hotkey('ctrl', 'v')
    
    # Restore
    if orig_text is not None:
        time.sleep(delay)
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
            except Exception:
                pass
            finally:
                CloseClipboard()
    return True

if __name__ == "__main__":
    print("=== ТЕСТ ВВОДА ТЕКСТА ДЛЯ ГОЛОСОВОГО НАБОРА ===")
    print("1 - PyAutoGUI (прямой ввод)")
    print("2 - Keyboard (Unicode ввод)")
    print("3 - Буфер обмена (120 мс задержка)")
    print("4 - Буфер обмена (600 мс задержка)")
    print("0 - Выход")
    
    try:
        val = input("Выберите тест: ")
        if val == '1':
            test_pyautogui_direct()
        elif val == '2':
            test_keyboard_direct()
        elif val == '3':
            test_clipboard_fast()
        elif val == '4':
            test_clipboard_slow()
        else:
            print("Выход.")
    except KeyboardInterrupt:
        print("\nВыход.")
