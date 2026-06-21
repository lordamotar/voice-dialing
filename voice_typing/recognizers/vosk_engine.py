import os
import json
import logging
from voice_typing.recognizers.base import Recognizer

logger = logging.getLogger(__name__)

class VoskEngine(Recognizer):
    def __init__(self, model_path: str, language: str):
        if not model_path:
            raise ValueError("Путь к модели Vosk не указан в конфигурации.")

        # Smart replacement of language templates if used
        self.model_path = model_path.replace("{lang}", language).replace("{language}", language)
        self.language = language

        logger.info(f"Инициализация Vosk с моделью из '{self.model_path}'...")
        if not os.path.exists(self.model_path) or not os.path.isdir(self.model_path):
            raise FileNotFoundError(
                f"\n[ОШИБКА] Папка модели Vosk '{self.model_path}' не найдена!\n"
                f"Для работы распознавания на языке '{self.language}' вам необходимо:\n"
                f"  1. Скачать модель с официального сайта: https://alphacephei.com/vosk/models\n"
                f"     - Для русского: 'vosk-model-small-ru-0.22'\n"
                f"     - Для казахского: 'vosk-model-small-kz-0.22'\n"
                f"  2. Распаковать скачанный архив.\n"
                f"  3. Переместить распакованную папку в директорию '{self.model_path}' или настроить "
                f"путь в config.yaml -> vosk.model_path."
            )

        # Basic check to see if files exist inside
        model_contents = os.listdir(self.model_path)
        if not any(item in model_contents for item in ['am', 'graph', 'conf', 'ivector']):
            raise RuntimeError(
                f"\n[ОШИБКА] Папка '{self.model_path}' не похожа на корректную модель Vosk.\n"
                f"Убедитесь, что вы распаковали содержимое архива внутрь этой папки, "
                f"а не вложили ещё одну подпапку."
            )

        # Import vosk here to avoid loading errors if not installed
        try:
            from vosk import Model, KaldiRecognizer
        except ImportError:
            raise ImportError(
                "Библиотека 'vosk' не установлена. Запустите 'uv sync' для установки зависимостей."
            )

        try:
            self.model = Model(self.model_path)
        except Exception as e:
            raise RuntimeError(
                f"Не удалось загрузить модель Vosk из '{self.model_path}': {e}.\n"
                f"Возможно, файлы модели повреждены."
            )

        self.rec = KaldiRecognizer(self.model, 16000)
        logger.info("Модель Vosk успешно загружена.")

    def accept_waveform(self, data: bytes) -> bool:
        return self.rec.AcceptWaveform(data)

    def get_partial_result(self) -> str:
        res = self.rec.PartialResult()
        try:
            data = json.loads(res)
            return data.get("partial", "")
        except Exception as e:
            logger.error(f"Ошибка парсинга PartialResult: {e}")
            return ""

    def get_final_result(self) -> str:
        res = self.rec.FinalResult()
        try:
            data = json.loads(res)
            return data.get("text", "")
        except Exception as e:
            logger.error(f"Ошибка парсинга FinalResult: {e}")
            return ""
