import os
import sys
import queue
import logging
import time
import threading
import argparse
from typing import Optional

from voice_typing.config import Config, ConfigError
from voice_typing.audio_capture import AudioCapture, AudioCaptureError
from voice_typing.recognizers import create_recognizer
from voice_typing.corrector import GrammarCorrector
from voice_typing.typer import ActiveWindowTyper
from voice_typing.hotkey import HotkeyListener

# Define log directory and make sure it exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("voice_typing")

class VoiceTypingApp:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.recognizer = None
        self.corrector: Optional[GrammarCorrector] = None
        self.typer: Optional[ActiveWindowTyper] = None
        self.hotkey_listener: Optional[HotkeyListener] = None

        self.session_active = False
        self.is_recording = False
        self.processing_thread: Optional[threading.Thread] = None

    def setup(self) -> bool:
        """Initialize all components of the application. Returns True if successful."""
        try:
            # 1. Load config
            self.config = Config(self.config_path)
            self._setup_logging()
            logger.info("Конфигурация успешно загружена.")
        except ConfigError as e:
            print(f"\n[ОШИБКА КОНФИГУРАЦИИ] {e}")
            return False
        except Exception as e:
            print(f"\n[ОШИБКА] Не удалось загрузить конфигурацию: {e}")
            return False

        # 2. Initialize Recognizer
        try:
            self.recognizer = create_recognizer(self.config)
        except FileNotFoundError as e:
            print(e)
            return False
        except Exception as e:
            logger.exception("Ошибка при создании распознавателя")
            print(
                f"\n[ОШИБКА РАСПОЗНАВАТЕЛЯ] Не удалось загрузить движок распознавания '{self.config.engine}':\n"
                f"Детали: {e}"
            )
            return False

        # 3. Initialize Audio Capture
        self.audio_capture = AudioCapture(
            sample_rate=16000, 
            block_size=4000,
            device_index=self.config.input_device_index
        )

        # 4. Initialize Grammar Corrector
        self.corrector = GrammarCorrector(
            enable=self.config.enable_grammar_correction,
            language=self.config.language
        )

        # 5. Initialize Keyboard Typer
        self.typer = ActiveWindowTyper(interval=self.config.typing_interval)

        # 6. Initialize Hotkey Listener
        self.hotkey_listener = HotkeyListener(
            hotkey_str=self.config.hotkey,
            on_start=self.on_start_recording,
            on_stop=self.on_stop_recording
        )

        return True

    def _setup_logging(self):
        """Set up file and stream logging configurations."""
        log_level = getattr(logging, self.config.log_level, logging.INFO)
        
        # Configure root logger for the package
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove any existing handlers
        root_logger.handlers = []
        
        # File Handler (detailed logs)
        log_file = os.path.join(LOG_DIR, "voice_typing.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s (%(threadName)s): %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Console Handler (only warnings/errors or clean info to keep console neat)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING)  # Only print warnings and above in console to avoid cluttering text entry
        root_logger.addHandler(console_handler)

    def on_start_recording(self):
        """Callback triggered when the hotkey is pressed."""
        if self.session_active or (self.processing_thread and self.processing_thread.is_alive()):
            logger.warning("Сессия записи уже активна. Пропускаю повторный старт.")
            return

        self.session_active = True
        self.is_recording = True
        
        if hasattr(self, "overlay") and self.overlay:
            self.overlay.show()
        
        try:
            self.audio_capture.start()
            self.processing_thread = threading.Thread(
                target=self._recording_and_typing_session,
                name="VoiceSessionThread"
            )
            self.processing_thread.start()
        except AudioCaptureError as e:
            print(f"\n[ОШИБКА ЗАПИСИ] {e}")
            self.is_recording = False
            self.session_active = False
            if hasattr(self, "overlay") and self.overlay:
                self.overlay.hide()

    def on_stop_recording(self):
        """Callback triggered when the hotkey is released."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        logger.info("Сигнал остановки записи получен.")
        
        if hasattr(self, "overlay") and self.overlay:
            self.overlay.hide()

    def _recording_and_typing_session(self):
        """Target for processing thread. Handles streaming audio data and typing result."""
        print("\n>>> Запись... (говорите) ", end="", flush=True)
        
        # 1. Audio stream feed loop
        try:
            while self.is_recording or not self.audio_capture.queue.empty():
                try:
                    # Wait for a chunk from queue
                    chunk = self.audio_capture.get_chunk(timeout=0.1)
                    
                    # Feed chunk to recognizer
                    is_final = self.recognizer.accept_waveform(chunk)
                    
                    # Feed back partial result to user console if Vosk is active
                    if self.config.engine == "vosk":
                        partial = self.recognizer.get_partial_result()
                        if partial:
                            print(f"\r>>> Распознано: {partial}", end="", flush=True)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Ошибка в цикле записи: {e}")
                    break
        finally:
            # 2. Stop capture stream (safe even if called multiple times)
            self.audio_capture.stop()
            
        print("\n>>> Обработка... ", end="", flush=True)
        
        # 3. Finalize speech recognition
        try:
            final_text = self.recognizer.get_final_result()
            print(f"\r>>> Распознано: {final_text}")
        except Exception as e:
            logger.error(f"Ошибка получения финального результата: {e}")
            final_text = ""
            print("\r>>> Ошибка распознавания речи.")

        # 4. Correct text and type if not empty
        if final_text:
            corrected_text = self.corrector.correct(final_text)
            if self.config.enable_grammar_correction and corrected_text != final_text:
                print(f">>> Исправлено:  {corrected_text}")
            
            # Simulate typing
            self.typer.type_text(corrected_text)
        else:
            print(">>> Текст пуст, ввод пропущен.")

        print(">>> Ожидание горячей клавиши...")
        self.session_active = False

    def _check_signals(self):
        """Periodically run a small callback to check for Ctrl+C interrupts."""
        if hasattr(self, "root") and self.root:
            try:
                self.root.after(100, self._check_signals)
            except Exception:
                pass

    def run(self):
        """Main application runner loop."""
        if not self.setup():
            print("\n[КРИТИЧЕСКАЯ ОШИБКА] Не удалось инициализировать приложение. Выход.")
            return

        # Start listening for the global hotkey
        self.hotkey_listener.start()

        # Setup visual overlay if enabled
        use_overlay = getattr(self.config, "enable_overlay", True)
        if use_overlay:
            try:
                import tkinter as tk
                from voice_typing.overlay import RecordingOverlay
                
                self.root = tk.Tk()
                self.overlay = RecordingOverlay(self.root, self.config.hotkey)
                
                # Start periodic signal checks to process KeyboardInterrupt (Ctrl+C)
                self._check_signals()
            except Exception as e:
                logger.warning(f"Не удалось инициализировать оверлей: {e}. Работа без оверлея.")
                use_overlay = False
                self.root = None
                self.overlay = None
        else:
            self.root = None
            self.overlay = None

        try:
            if use_overlay and self.root:
                try:
                    self.root.mainloop()
                except KeyboardInterrupt:
                    print("\nПолучен сигнал завершения (Ctrl+C). Выхожу...")
            else:
                # Main thread waits here while background thread works
                while self.hotkey_listener.running:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nПолучен сигнал завершения (Ctrl+C). Выхожу...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Close resources and servers on shutdown."""
        logger.info("Завершение работы приложения...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        if self.audio_capture:
            self.audio_capture.stop()

        if self.corrector:
            self.corrector.close()

        if hasattr(self, "root") and self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            
        print("[ИНФО] Работа завершена.")

def main():
    parser = argparse.ArgumentParser(description="Offline Voice Typing Tool for RU/KZ")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml", 
        help="Путь к файлу конфигурации (по умолчанию config.yaml)"
    )
    args = parser.parse_args()

    app = VoiceTypingApp(config_path=args.config)
    app.run()

if __name__ == "__main__":
    main()
