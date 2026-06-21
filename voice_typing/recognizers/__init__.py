import logging
from voice_typing.config import Config
from voice_typing.recognizers.base import Recognizer
from voice_typing.recognizers.vosk_engine import VoskEngine
from voice_typing.recognizers.whisper_engine import WhisperEngine

logger = logging.getLogger(__name__)

def create_recognizer(config: Config) -> Recognizer:
    """Factory function that returns the configured Recognizer instance."""
    engine_name = config.engine.lower()
    
    if engine_name == "vosk":
        return VoskEngine(
            model_path=config.vosk_model_path,
            language=config.language
        )
    elif engine_name == "faster-whisper":
        return WhisperEngine(
            model_size=config.whisper_model_size,
            device=config.device,
            compute_type_cpu=config.whisper_compute_type_cpu,
            compute_type_gpu=config.whisper_compute_type_gpu,
            language=config.language
        )
    else:
        raise ValueError(f"Неизвестный движок распознавания: {engine_name}")
