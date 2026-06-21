import os
import shutil
import logging
import yaml
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "config.yaml"
TEMPLATE_CONFIG_NAME = "config.example.yaml"


class ConfigError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class Config:
    def __init__(self, config_path: str = DEFAULT_CONFIG_NAME):
        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        # Resolve path relative to the project root (assumed to be working directory)
        if not os.path.exists(self.config_path):
            if os.path.exists(TEMPLATE_CONFIG_NAME):
                logger.info(f"Конфигурационный файл {self.config_path} не найден. Копирую из шаблона {TEMPLATE_CONFIG_NAME}...")
                shutil.copy(TEMPLATE_CONFIG_NAME, self.config_path)
                print(f"[ИНФО] Создан конфигурационный файл по умолчанию: {self.config_path}. Пожалуйста, настройте его при необходимости.")
            else:
                raise ConfigError(
                    f"Конфигурационный файл '{self.config_path}' и шаблон '{TEMPLATE_CONFIG_NAME}' не найдены."
                )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config_data = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Ошибка при чтении {self.config_path}: {e}")

        self._validate_config()

    def _validate_config(self):
        # 1. Hotkey
        self.hotkey = self._config_data.get("hotkey", "ctrl+space")
        if not isinstance(self.hotkey, str) or not self.hotkey:
            raise ConfigError("Параметр 'hotkey' должен быть непустой строкой.")

        # 2. Language
        self.language = self._config_data.get("language", "ru").lower()
        if self.language not in ["ru", "kz"]:
            raise ConfigError(f"Неподдерживаемый язык '{self.language}'. Допустимые значения: ru, kz.")

        # 3. Engine
        self.engine = self._config_data.get("engine", "vosk").lower()
        if self.engine not in ["vosk", "faster-whisper"]:
            raise ConfigError(f"Неподдерживаемый движок '{self.engine}'. Допустимые значения: vosk, faster-whisper.")

        # 4. Device
        self.device = self._config_data.get("device", "auto").lower()
        if self.device not in ["auto", "cpu", "cuda"]:
            raise ConfigError(f"Неподдерживаемое устройство '{self.device}'. Допустимые значения: auto, cpu, cuda.")

        # 5. Vosk config
        vosk_data = self._config_data.get("vosk", {})
        if not isinstance(vosk_data, dict):
            raise ConfigError("Раздел 'vosk' в конфигурационном файле должен быть объектом (словарем).")
        self.vosk_model_path = vosk_data.get("model_path")
        
        # 6. Whisper config
        whisper_data = self._config_data.get("faster_whisper", {})
        if not isinstance(whisper_data, dict):
            raise ConfigError("Раздел 'faster_whisper' в конфигурационном файле должен быть объектом (словарем).")
        self.whisper_model_size = whisper_data.get("model_size", "small")
        self.whisper_compute_type_cpu = whisper_data.get("compute_type_cpu", "int8")
        self.whisper_compute_type_gpu = whisper_data.get("compute_type_gpu", "float16")

        # 7. Additional settings
        self.enable_grammar_correction = bool(self._config_data.get("enable_grammar_correction", True))
        
        try:
            self.typing_interval = float(self._config_data.get("typing_interval", 0.01))
        except (ValueError, TypeError):
            self.typing_interval = 0.01

        self.log_level = self._config_data.get("log_level", "INFO").upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.log_level = "INFO"
