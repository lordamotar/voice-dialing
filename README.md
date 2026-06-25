# Offline Voice Typing (Офлайн-система голосового ввода для RU/KZ)

[Русская версия (Russian Version)](README.ru.md)

An open-source, cross-platform (Windows, Linux) desktop utility for **offline voice typing** and **speech-to-text** transcription. It listens to your voice and types the recognized text directly into any active application window by mimicking real keyboard typing.

This project is built for **offline speech recognition** utilizing **Vosk** and **faster-whisper** engines, features **automatic punctuation** via **LanguageTool**, and simulates global keyboard input.

---

## 🔍 SEO Keywords
* **offline voice typing**
* **speech-to-text**
* **voice input python**
* **speech recognition offline**
* **Vosk speech-to-text**
* **faster-whisper**
* **automatic punctuation**
* **grammar correction**
* **keyboard typing simulation**
* **Windows voice typing autostart**
* **Linux voice typing**
* **голосовой ввод офлайн**
* **распознавание речи**

---

## 🌟 Features

- **100% Offline & Private**: All **speech-to-text** recognition is executed locally on your machine. No cloud API calls, no internet telemetry, no external servers.
- **Dual Recognition Engines**:
  - **Vosk**: Ultra-lightweight and fast, optimized for standard CPU execution and low-end hardware.
  - **faster-whisper**: High-accuracy transcription powered by CTranslate2 engine. Supports GPU (CUDA) and CPU with `int8` quantization.
- **Push-to-Talk (Global Hotkey)**: Simple activation (e.g., `ctrl+space`). The app records while the hotkey is held down and transcribes upon release.
- **Smart Grammar Correction**: Runs a local LanguageTool engine to automatically insert capital letters, commas, periods, and fix grammatical mistakes (requires Java).
- **Multilingual Support**: High-performance models optimized for **Russian** (`ru`) and **Kazakh** (`kz`) languages.
- **Visual Island Overlay**: Non-intrusive floating indicator showing the current status (Recording, Processing) without stealing window focus.
- **System Tray Integration**: The application minimizes to the system tray (notification area near the clock) and runs silently in the background. Right-clicking the tray icon allows you to quickly open "Settings" or "Exit" the app.
- **System Autostart**: Easily configure the utility to launch silently on operating system boot (via the graphical settings panel).

---

## 💻 System Requirements

- **Python**: Versions `3.9` up to `3.12`.
- **Java (JRE/JDK)**: Required only for the grammar correction module (`language-tool-python`). You can download Java from the [official Oracle website](https://www.oracle.com/java/technologies/downloads/) or install OpenJDK. The application will function without Java, but text correction will be skipped.
- **Linux limitations**:
  - Requires **X11** display server (Wayland is currently not supported for global keyboard hooks).
  - Requires superuser (`sudo`) privileges for the `keyboard` library to intercept global hotkeys.
  - Requires utility tools `xclip` and `xsel` (Install via `sudo apt-get install xclip xsel`).
- **NVIDIA GPU (Optional for Whisper CUDA)**: Requires NVIDIA drivers, CUDA Toolkit (11.x or 12.x), and cuDNN installed on your system.

---

## 🚀 One-Click Installation

The project uses the modern, lightning-fast Python package manager **`uv`**.

### Windows
1. Double-click the **`install.bat`** file in the root folder.
2. The script will automatically install `uv` (if missing), fetch the required Python environment, download dependencies, and fetch the default Russian speech model.

### Linux / macOS
1. Open terminal and run:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
2. The script will set up the package manager, compile dependencies, and download the default model.

---

## ⚙️ Configuration & GUI Settings

You can customize all options using the built-in **Graphical Settings Panel** (GUI Dashboard):

### Launching the settings panel
- **Windows**: Double-click **`run_settings.bat`**
- **Linux / macOS**: Run `./run_settings.sh` in terminal

The panel provides an elegant dark-themed interface to configure:
1. **Engine Selection**: Toggle between **Vosk** and **Whisper**.
2. **Device Configurations**: Force CPU execution or GPU (CUDA) acceleration.
3. **Microphone Dropdown**: Dynamically scans and lists all plugged-in audio inputs with correct localized names.
4. **General parameters**: Edit activation hotkeys (with a button to record combinations), adjust typing interval speeds, toggle the visual overlay status, and turn grammar correction on or off.
5. **Autostart Toggle**: Check "Запускать вместе с системой (Автозагрузка)" to automatically start the app on OS boot (silently in the background on Windows).

Alternatively, you can manually edit **`config.yaml`** (created automatically from `config.example.yaml` on first launch):
```yaml
hotkey: "ctrl+space"                 # Recording trigger shortcut
language: "ru"                       # Default language: ru | kz
engine: "vosk"                       # vosk | faster-whisper
device: "auto"                       # auto | cpu | cuda (for whisper only)
vosk:
  model_path: "models/vosk-model-small-ru-0.22"
faster_whisper:
  model_size: "small"                # tiny | base | small | medium
  compute_type_cpu: "int8"           # CPU compute type
  compute_type_gpu: "float16"        # GPU compute type
enable_grammar_correction: true      # Enable LanguageTool grammar correction
enable_overlay: true                 # Show visual island widget on recording
input_device_index: null             # Audio input device index (null for default)
typing_interval: 0.01                # Typing emulation delay between keys (seconds)
log_level: "INFO"                    # Log level: DEBUG | INFO | WARNING | ERROR
```

---

## 🏃 Starting the Application

Once configured, run the speech-to-text runner:
- **Windows**: 
  - To run in background mode (with no console window on the taskbar): double-click **`run_silent.vbs`** (recommended).
  - To run with console visible: double-click **`run_app.bat`**
- **Linux / macOS**: Run `./run_app.sh`

### How to use:
1. The terminal will display: `[ГОТОВО] Ожидание горячей клавиши 'ctrl+space'...`
2. Hold down the hotkey combination (default: `Ctrl + Space`).
3. Speak into your microphone.
4. Release the hotkey. The application will translate your speech into text, fix spelling errors, and simulate keyboard typing directly into the active text field.

---

## 🏋️ Hardware Recommendations

| Scenario | Engine | Recommended Parameters |
| :--- | :--- | :--- |
| **Low-end laptop / office PC** (no GPU) | `vosk` | `engine: "vosk"`, model `vosk-model-small-ru-0.22` |
| **Mid-range desktop** (average CPU, no GPU) | `faster-whisper` | `engine: "faster-whisper"`, `model_size: "tiny"` or `"base"`, `device: "cpu"`, `compute_type_cpu: "int8"` |
| **High-end / Gaming PC** (NVIDIA GPU with CUDA) | `faster-whisper` | `engine: "faster-whisper"`, `model_size: "small"` or `"medium"`, `device: "cuda"`, `compute_type_gpu: "float16"` |

---

## 🛠️ Troubleshooting

### 1. Java not found / LanguageTool fails
- **Symptom**: Console logs show a Java error. Text is typed, but punctuation and capitals are not corrected.
- **Solution**: Install Java JRE/JDK (version 8+) and add the `java` executable path to your system's Environment Variables (PATH).

### 2. CUDA is unavailable
- **Symptom**: When `device: auto` is selected, the application prints a warning and falls back to CPU mode.
- **Solution**: Ensure you have an NVIDIA graphic card, and install the compatible NVIDIA Drivers, CUDA Toolkit (12.x/11.x), and corresponding cuDNN libraries.

### 3. Wayland display server issues (Linux)
- **Symptom**: Hotkeys or keyboard simulation do not work.
- **Solution**: The `keyboard` and `pyautogui` modules require X11. Switch your Linux session from Wayland to **X11** on the login screen.

---

## 💝 Support & Donations (Благодарность)

If you find this project useful, you can support the development by donating to:

* **USDT (TON Network)**: 
  `UQAgs40InZVUGmKJWdM4VKCn18jMru9I_BYWHGp7TdfJBc1T`
* **Bank Card**: 
  `4002890039798909`

---

## 📄 License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
