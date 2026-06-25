import os
import sys
import logging
import yaml
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Configure basic logging to console
logging.basicConfig(level=logging.INFO, format="[GUI] %(levelname)s - %(message)s")
logger = logging.getLogger("settings_gui")

CONFIG_PATH = "config.yaml"
TEMPLATE_PATH = "config.example.yaml"

# Colors for premium dark mode
COLOR_BG = "#121214"
COLOR_CARD = "#1E1E24"
COLOR_BORDER = "#2E2E38"
COLOR_INPUT = "#2A2A32"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"
COLOR_ACCENT = "#F43F5E"  # Coral-rose
COLOR_ACCENT_HOVER = "#FB7185"
COLOR_BUTTON_SECONDARY = "#2D2D35"
COLOR_BUTTON_SECONDARY_HOVER = "#3F3F46"

class HotkeyRecorder:
    def __init__(self, button, entry):
        self.button = button
        self.entry = entry
        self.is_recording = False
        self.pressed_keys = set()
        
    def start(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.button.config(text="Нажмите клавиши... (Esc - сброс)", bg="#4B5563", fg="#FFFFFF")
        self.button.focus_set()
        self.pressed_keys.clear()
        
        self.button.bind("<KeyPress>", self.on_key_press)
        self.button.bind("<KeyRelease>", self.on_key_release)
        self.button.bind("<FocusOut>", self.stop)

    def stop(self, event=None):
        if not self.is_recording:
            return
        self.is_recording = False
        self.button.config(text="Записать", bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT)
        self.button.unbind("<KeyPress>")
        self.button.unbind("<KeyRelease>")
        self.button.unbind("<FocusOut>")

    def on_key_press(self, event):
        if not self.is_recording:
            return "break"
            
        key = event.keysym.lower()
        
        # Escape resets recording
        if key == "escape":
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "")
            self.stop()
            return "break"
            
        # Map Tkinter key names to typical hotkey format library names
        mapped_key = None
        if key in ("control_l", "control_r"):
            mapped_key = "ctrl"
        elif key in ("shift_l", "shift_r"):
            mapped_key = "shift"
        elif key in ("alt_l", "alt_r"):
            mapped_key = "alt"
        elif key in ("win_l", "win_r", "command"):
            mapped_key = "windows"
        elif key == "space":
            mapped_key = "space"
        elif key == "capital":
            mapped_key = "capslock"
        elif len(key) == 1:
            mapped_key = key
        else:
            mapped_key = key

        if mapped_key:
            self.pressed_keys.add(mapped_key)
            
        # Format the hotkey string
        parts = []
        for mod in ["ctrl", "alt", "shift", "windows"]:
            if mod in self.pressed_keys:
                parts.append(mod)
        for k in sorted(list(self.pressed_keys)):
            if k not in ["ctrl", "alt", "shift", "windows"]:
                parts.append(k)
                
        if parts:
            hotkey_str = "+".join(parts)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, hotkey_str)
            
        # Stop recording once a non-modifier key is pressed
        has_non_modifier = any(k not in ["ctrl", "alt", "shift", "windows"] for k in self.pressed_keys)
        if has_non_modifier:
            self.stop()
            
        return "break"

    def on_key_release(self, event):
        return "break"


def get_microphones():
    mics = []
    # Try pyaudio first for correct string encoding (cp1251 on Russian Windows)
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    name = info.get('name')
                    if isinstance(name, bytes):
                        name = name.decode('cp1251', errors='replace')
                    mics.append((i, name))
            except Exception:
                pass
        p.terminate()
    except Exception:
        # Fallback to sounddevice
        try:
            import sounddevice as sd
            for i, d in enumerate(sd.query_devices()):
                if d.get('max_input_channels', 0) > 0:
                    name = d.get('name', f"Устройство {i}")
                    mics.append((i, name))
        except Exception:
            pass
    return mics


def create_section(parent, title_text):
    # Modern card-like container with a border and title label
    container = tk.Frame(parent, bg=COLOR_CARD, bd=0)
    container.pack(fill="x", padx=15, pady=8)
    
    # Outer frame for border effect
    border_frame = tk.Frame(container, bg=COLOR_BORDER, bd=1)
    border_frame.pack(fill="both", expand=True)
    
    inner = tk.Frame(border_frame, bg=COLOR_CARD, padx=12, pady=10)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    
    title_label = tk.Label(inner, text=title_text, bg=COLOR_CARD, fg=COLOR_ACCENT, font=("Segoe UI", 10, "bold"), anchor="w")
    title_label.pack(fill="x", pady=(0, 6))
    
    grid_frame = tk.Frame(inner, bg=COLOR_CARD)
    grid_frame.pack(fill="both", expand=True)
    grid_frame.columnconfigure(0, weight=1)
    grid_frame.columnconfigure(1, weight=2)
    
    return grid_frame


import platform

def check_autostart_enabled() -> bool:
    system = platform.system()
    if system == "Windows":
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        vbs_path = os.path.join(startup_dir, "VoiceTyping.vbs")
        return os.path.exists(vbs_path)
    elif system == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_path = os.path.join(autostart_dir, "voice_typing.desktop")
        return os.path.exists(desktop_path)
    return False


def toggle_autostart(enable: bool):
    system = platform.system()
    if system == "Windows":
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        batch_path = os.path.join(startup_dir, "VoiceTyping.bat")
        vbs_path = os.path.join(startup_dir, "VoiceTyping.vbs")
        
        if enable:
            if not os.path.exists(startup_dir):
                try:
                    os.makedirs(startup_dir, exist_ok=True)
                except Exception:
                    pass
            
            try:
                if getattr(sys, "frozen", False):
                    # For compiled EXE, run it directly without batch helper
                    exe_path = sys.executable
                    vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run chr(34) & "{exe_path}" & chr(34), 0, False\nSet WshShell = Nothing\n'
                    with open(vbs_path, "w", encoding="utf-8") as f:
                        f.write(vbs_content)
                    # Clean up old batch file if it existed
                    if os.path.exists(batch_path):
                        try:
                            os.remove(batch_path)
                        except Exception:
                            pass
                    logger.info("Автозагрузка включена в Windows (запуск EXE напрямую).")
                else:
                    # For python development run, use batch helper to run uv/python
                    project_dir = os.path.abspath(os.path.dirname(__file__))
                    batch_content = f'@echo off\ncd /d "{project_dir}"\nuv run python main.py\n'
                    with open(batch_path, "w", encoding="cp866") as f:
                        f.write(batch_content)
                        
                    vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run chr(34) & "{batch_path}" & chr(34), 0\nSet WshShell = Nothing\n'
                    with open(vbs_path, "w", encoding="utf-8") as f:
                        f.write(vbs_content)
                    logger.info("Автозагрузка включена в Windows (созданы файлы в папке Startup).")
            except Exception as e:
                logger.error(f"Не удалось настроить автозагрузку в Windows: {e}")
        else:
            try:
                if os.path.exists(batch_path):
                    os.remove(batch_path)
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)
                logger.info("Автозагрузка отключена в Windows (удалены файлы из папки Startup).")
            except Exception as e:
                logger.error(f"Не удалось удалить файлы автозагрузки в Windows: {e}")
                
    elif system == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_path = os.path.join(autostart_dir, "voice_typing.desktop")
        
        if enable:
            try:
                os.makedirs(autostart_dir, exist_ok=True)
                project_dir = os.path.abspath(os.path.dirname(__file__))
                desktop_content = f"""[Desktop Entry]
Type=Application
Exec=sh -c "cd {project_dir} && uv run python main.py"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Voice Typing
Comment=Offline Voice Typing RU/KZ
"""
                with open(desktop_path, "w", encoding="utf-8") as f:
                    f.write(desktop_content)
                os.chmod(desktop_path, 0o755)
                logger.info("Автозагрузка включена в Linux (создан .desktop файл).")
            except Exception as e:
                logger.error(f"Не удалось настроить автозагрузку в Linux: {e}")
        else:
            try:
                if os.path.exists(desktop_path):
                    os.remove(desktop_path)
                logger.info("Автозагрузка отключена в Linux (удален .desktop файл).")
            except Exception as e:
                logger.error(f"Не удалось удалить файл автозагрузки в Linux: {e}")


class SettingsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Панель настроек голосового ввода")
        self.root.geometry("540x720")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)
        
        # Apply dark mode style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Style comboboxes
        self.style.configure('TCombobox',
                             background=COLOR_INPUT,
                             fieldbackground=COLOR_INPUT,
                             foreground=COLOR_TEXT,
                             bordercolor=COLOR_BORDER,
                             lightcolor=COLOR_BORDER,
                             darkcolor=COLOR_BORDER,
                             arrowcolor=COLOR_TEXT_MUTED)
        
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', COLOR_INPUT), ('disabled', COLOR_CARD)],
                       foreground=[('readonly', COLOR_TEXT), ('disabled', COLOR_TEXT_MUTED)],
                       bordercolor=[('readonly', COLOR_BORDER), ('disabled', COLOR_CARD)])

        self.root.option_add('*TCombobox*Listbox.background', COLOR_INPUT)
        self.root.option_add('*TCombobox*Listbox.foreground', COLOR_TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
        
        self.mics = get_microphones()
        self.load_config()
        self.build_ui()
        self.update_engine_fields()

    def load_config(self):
        self.config_data = {}
        path_to_load = CONFIG_PATH if os.path.exists(CONFIG_PATH) else TEMPLATE_PATH
        
        if os.path.exists(path_to_load):
            try:
                with open(path_to_load, "r", encoding="utf-8") as f:
                    self.config_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Не удалось прочитать {path_to_load}: {e}")
                
        # Fill default values if missing
        self.hotkey_val = self.config_data.get("hotkey", "ctrl+space")
        self.language_val = self.config_data.get("language", "ru")
        self.engine_val = self.config_data.get("engine", "vosk")
        self.device_val = self.config_data.get("device", "auto")
        
        vosk_sec = self.config_data.get("vosk", {})
        self.vosk_model_path_val = vosk_sec.get("model_path", "models/vosk-model-small-ru-0.22")
        
        whisper_sec = self.config_data.get("faster_whisper", {})
        self.whisper_model_size_val = whisper_sec.get("model_size", "small")
        self.whisper_cpu_compute_val = whisper_sec.get("compute_type_cpu", "int8")
        self.whisper_gpu_compute_val = whisper_sec.get("compute_type_gpu", "float16")
        
        self.grammar_val = bool(self.config_data.get("enable_grammar_correction", True))
        self.overlay_val = bool(self.config_data.get("enable_overlay", True))
        self.input_device_index_val = self.config_data.get("input_device_index")
        self.typing_interval_val = float(self.config_data.get("typing_interval", 0.01))
        self.log_level_val = self.config_data.get("log_level", "INFO").upper()
        self.autostart_val = check_autostart_enabled()

    def build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self.root, bg=COLOR_BG, pady=12)
        header.pack(fill="x")
        
        title = tk.Label(header, text="ГОЛОСОВОЙ ВВОД", bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 16, "bold"))
        title.pack()
        subtitle = tk.Label(header, text="Панель параметров offline-распознавания речи", bg=COLOR_BG, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9))
        subtitle.pack()
        
        divider = tk.Frame(self.root, bg=COLOR_BORDER, height=1)
        divider.pack(fill="x", padx=15, pady=(0, 5))

        # 2. Main Scrollable or Pack Container
        main_container = tk.Frame(self.root, bg=COLOR_BG)
        main_container.pack(fill="both", expand=True)

        # SECTION 1: Recognition Engine
        grid_engine = create_section(main_container, "Движок распознавания речи")
        
        # Engine radio buttons
        tk.Label(grid_engine, text="Движок:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.engine_var = tk.StringVar(value=self.engine_val)
        
        radio_frame = tk.Frame(grid_engine, bg=COLOR_CARD)
        radio_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        r_vosk = tk.Radiobutton(
            radio_frame, text="Vosk (легкий, оффлайн)", variable=self.engine_var, value="vosk",
            bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_INPUT, activebackground=COLOR_CARD,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9), command=self.update_engine_fields
        )
        r_vosk.pack(side="left", padx=(0, 15))
        
        r_whisper = tk.Radiobutton(
            radio_frame, text="Faster-Whisper (качество)", variable=self.engine_var, value="faster-whisper",
            bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_INPUT, activebackground=COLOR_CARD,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9), command=self.update_engine_fields
        )
        r_whisper.pack(side="left")

        # Device select
        tk.Label(grid_engine, text="Устройство запуска (Device):", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.device_combo = ttk.Combobox(grid_engine, values=["auto", "cpu", "cuda"], state="readonly", width=25)
        self.device_combo.set(self.device_val)
        self.device_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Model size select
        tk.Label(grid_engine, text="Размер модели Whisper:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=5)
        self.model_size_combo = ttk.Combobox(grid_engine, values=["tiny", "base", "small", "medium"], state="readonly", width=25)
        self.model_size_combo.set(self.whisper_model_size_val)
        self.model_size_combo.grid(row=2, column=1, sticky="w", pady=5)

        # Advanced computes (grouped horizontally to save space)
        tk.Label(grid_engine, text="Тип вычислений CPU / GPU:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=5)
        compute_frame = tk.Frame(grid_engine, bg=COLOR_CARD)
        compute_frame.grid(row=3, column=1, sticky="w", pady=5)
        
        self.cpu_compute_combo = ttk.Combobox(compute_frame, values=["int8", "float32"], state="readonly", width=7)
        self.cpu_compute_combo.set(self.whisper_cpu_compute_val)
        self.cpu_compute_combo.pack(side="left")
        
        tk.Label(compute_frame, text=" / ", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(side="left", padx=2)
        
        self.gpu_compute_combo = ttk.Combobox(compute_frame, values=["float16", "float32"], state="readonly", width=8)
        self.gpu_compute_combo.set(self.whisper_gpu_compute_val)
        self.gpu_compute_combo.pack(side="left")

        # SECTION 2: Microphone & Language
        grid_device = create_section(main_container, "Аудиовход и Язык")
        
        # Audio Input dropdown
        tk.Label(grid_device, text="Микрофон:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        
        self.mic_options = ["По умолчанию"]
        selected_index = 0
        
        for idx, name in self.mics:
            option_str = f"{idx}: {name[:45]}..." if len(name) > 45 else f"{idx}: {name}"
            self.mic_options.append(option_str)
            if self.input_device_index_val is not None and self.input_device_index_val == idx:
                selected_index = len(self.mic_options) - 1
                
        # If the configured index is not in active list (e.g. unplugged)
        if self.input_device_index_val is not None and selected_index == 0:
            unplugged_str = f"{self.input_device_index_val}: [Устройство не подключено]"
            self.mic_options.append(unplugged_str)
            selected_index = len(self.mic_options) - 1

        self.mic_combo = ttk.Combobox(grid_device, values=self.mic_options, state="readonly", width=42)
        self.mic_combo.current(selected_index)
        self.mic_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Language dropdown
        tk.Label(grid_device, text="Язык по умолчанию:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.lang_combo = ttk.Combobox(grid_device, values=["ru", "kz"], state="readonly", width=25)
        self.lang_combo.set(self.language_val)
        self.lang_combo.grid(row=1, column=1, sticky="w", pady=5)

        # SECTION 3: Interface and Input Behavior
        grid_behavior = create_section(main_container, "Параметры ввода и интерфейса")
        
        # Hotkey setting
        tk.Label(grid_behavior, text="Горячая клавиша:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        
        hotkey_frame = tk.Frame(grid_behavior, bg=COLOR_CARD)
        hotkey_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        self.hotkey_entry = tk.Entry(hotkey_frame, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=1, relief="solid", highlightthickness=0, width=18, font=("Segoe UI", 9))
        self.hotkey_entry.insert(0, self.hotkey_val)
        self.hotkey_entry.pack(side="left", padx=(0, 6), ipady=3)
        
        btn_record = tk.Button(
            hotkey_frame, text="Записать", bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT,
            relief="flat", bd=0, activebackground=COLOR_BUTTON_SECONDARY_HOVER,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9, "bold"), padx=10, cursor="hand2"
        )
        btn_record.pack(side="left", ipady=2)
        
        self.recorder = HotkeyRecorder(btn_record, self.hotkey_entry)
        btn_record.config(command=self.recorder.start)
        self.bind_hover(btn_record, COLOR_BUTTON_SECONDARY_HOVER, COLOR_BUTTON_SECONDARY)

        # Typing delay
        tk.Label(grid_behavior, text="Интервал ввода (сек):", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.typing_entry = tk.Entry(grid_behavior, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=1, relief="solid", highlightthickness=0, width=28, font=("Segoe UI", 9))
        self.typing_entry.insert(0, str(self.typing_interval_val))
        self.typing_entry.grid(row=1, column=1, sticky="w", pady=5, ipady=3)

        # Checkboxes (Overlay + Grammar)
        chk_frame = tk.Frame(grid_behavior, bg=COLOR_CARD)
        chk_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 3))
        
        self.overlay_var = tk.BooleanVar(value=self.overlay_val)
        chk_overlay = tk.Checkbutton(
            chk_frame, text="Показывать индикатор записи (оверлей)", variable=self.overlay_var,
            bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_INPUT, activebackground=COLOR_CARD,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9)
        )
        chk_overlay.pack(anchor="w", pady=2)
        
        self.grammar_var = tk.BooleanVar(value=self.grammar_val)
        chk_grammar = tk.Checkbutton(
            chk_frame, text="Включить коррекцию текста (нужна Java)", variable=self.grammar_var,
            bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_INPUT, activebackground=COLOR_CARD,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9)
        )
        chk_grammar.pack(anchor="w", pady=2)

        self.autostart_var = tk.BooleanVar(value=self.autostart_val)
        chk_autostart = tk.Checkbutton(
            chk_frame, text="Запускать вместе с системой (Автозагрузка)", variable=self.autostart_var,
            bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_INPUT, activebackground=COLOR_CARD,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 9)
        )
        chk_autostart.pack(anchor="w", pady=2)

        # SECTION 4: Advanced settings
        grid_adv = create_section(main_container, "Дополнительно")
        
        # Log level
        tk.Label(grid_adv, text="Логирование:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.log_combo = ttk.Combobox(grid_adv, values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly", width=25)
        self.log_combo.set(self.log_level_val)
        self.log_combo.grid(row=0, column=1, sticky="w", pady=5)
        
        # Vosk path
        tk.Label(grid_adv, text="Путь к модели Vosk:", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.vosk_path_entry = tk.Entry(grid_adv, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=1, relief="solid", highlightthickness=0, width=32, font=("Segoe UI", 9))
        self.vosk_path_entry.insert(0, self.vosk_model_path_val)
        self.vosk_path_entry.grid(row=1, column=1, sticky="w", pady=5, ipady=3)

        # 3. Action Buttons (Save/Cancel) at the bottom
        actions = tk.Frame(self.root, bg=COLOR_BG, pady=10)
        actions.pack(fill="x", side="bottom")
        
        btn_cancel = tk.Button(
            actions, text="Отмена", bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT,
            relief="flat", bd=0, activebackground=COLOR_BUTTON_SECONDARY_HOVER,
            activeforeground=COLOR_TEXT, font=("Segoe UI", 10, "bold"), width=12, height=2, cursor="hand2",
            command=self.root.destroy
        )
        btn_cancel.pack(side="right", padx=(10, 20))
        self.bind_hover(btn_cancel, COLOR_BUTTON_SECONDARY_HOVER, COLOR_BUTTON_SECONDARY)
        
        btn_save = tk.Button(
            actions, text="Сохранить", bg=COLOR_ACCENT, fg="#FFFFFF",
            relief="flat", bd=0, activebackground=COLOR_ACCENT_HOVER,
            activeforeground="#FFFFFF", font=("Segoe UI", 10, "bold"), width=16, height=2, cursor="hand2",
            command=self.save_settings
        )
        btn_save.pack(side="right")
        self.bind_hover(btn_save, COLOR_ACCENT_HOVER, COLOR_ACCENT)

    def bind_hover(self, widget, hover_bg, normal_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def update_engine_fields(self):
        engine = self.engine_var.get()
        if engine == "vosk":
            self.device_combo.config(state="disabled")
            self.model_size_combo.config(state="disabled")
            self.cpu_compute_combo.config(state="disabled")
            self.gpu_compute_combo.config(state="disabled")
            self.vosk_path_entry.config(state="normal", bg=COLOR_INPUT, fg=COLOR_TEXT)
        else:
            self.device_combo.config(state="readonly")
            self.model_size_combo.config(state="readonly")
            self.cpu_compute_combo.config(state="readonly")
            self.gpu_compute_combo.config(state="readonly")
            self.vosk_path_entry.config(state="disabled", bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)

    def save_settings(self):
        # 1. Validation
        hotkey = self.hotkey_entry.get().strip()
        if not hotkey:
            messagebox.showerror("Ошибка валидации", "Поле 'Горячая клавиша' не может быть пустым.")
            return

        try:
            typing_interval = float(self.typing_entry.get().strip())
            if typing_interval < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка валидации", "Интервал ввода должен быть положительным числом.")
            return

        vosk_path = self.vosk_path_entry.get().strip().replace('\\', '/')
        if self.engine_var.get() == "vosk" and not vosk_path:
            messagebox.showerror("Ошибка валидации", "Путь к модели Vosk не может быть пустым при выборе этого движка.")
            return

        # 2. Extract selected input device index
        selected_mic = self.mic_combo.get()
        input_device_index = None
        if selected_mic != "По умолчанию" and ":" in selected_mic:
            try:
                input_device_index = int(selected_mic.split(":")[0])
            except ValueError:
                input_device_index = None

        # 3. Build values dictionary
        values = {
            "hotkey": hotkey,
            "language": self.lang_combo.get(),
            "engine": self.engine_var.get(),
            "device": self.device_combo.get(),
            "vosk_model_path": vosk_path,
            "whisper_model_size": self.model_size_combo.get(),
            "whisper_compute_type_cpu": self.cpu_compute_combo.get(),
            "whisper_compute_type_gpu": self.gpu_compute_combo.get(),
            "enable_grammar_correction": self.grammar_var.get(),
            "enable_overlay": self.overlay_var.get(),
            "input_device_index": input_device_index,
            "typing_interval": typing_interval,
            "log_level": self.log_combo.get()
        }

        # 4. Save YAML preserving format and Russian comments
        yaml_content = f"""# Настройки горячих клавиш и языка ввода
hotkey: "{values['hotkey']}"                 # Сочетание клавиш для записи (Push-to-Talk)
language: "{values['language']}"                       # Язык по умолчанию: ru | kz

# Выбор движка распознавания
engine: "{values['engine']}"                       # vosk | faster-whisper
device: "{values['device']}"                       # auto | cpu | cuda (актуально только для faster-whisper)

# Конфигурация для Vosk
vosk:
  model_path: "{values['vosk_model_path']}"

# Конфигурация для faster-whisper
faster_whisper:
  model_size: "{values['whisper_model_size']}"                # tiny | base | small | medium — размер модели
  compute_type_cpu: "{values['whisper_compute_type_cpu']}"           # тип вычислений для CPU (рекомендуется int8)
  compute_type_gpu: "{values['whisper_compute_type_gpu']}"        # тип вычислений для GPU (float16/float32)

# Дополнительные параметры
enable_grammar_correction: {str(values['enable_grammar_correction']).lower()}      # Включить коррекцию пунктуации и грамматики (требуется Java)
enable_overlay: {str(values['enable_overlay']).lower()}                 # Показывать красивый графический оверлей во время записи
input_device_index: {values['input_device_index'] if values['input_device_index'] is not None else 'null'}             # Индекс устройства ввода звука (null - по умолчанию)
typing_interval: {values['typing_interval']}                # Задержка между нажатиями клавиш при эмуляции ввода (в секундах)
log_level: "{values['log_level']}"                    # Уровень логирования: DEBUG | INFO | WARNING | ERROR
"""
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            logger.info("Конфигурация успешно сохранена в config.yaml")
            try:
                toggle_autostart(self.autostart_var.get())
            except Exception as ae:
                logger.error(f"Не удалось изменить автозагрузку: {ae}")
            messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            self.root.destroy()
        except Exception as e:
            logger.error(f"Не удалось записать конфигурацию: {e}")
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить настройки в файл: {e}")


def main():
    root = tk.Tk()
    app = SettingsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
