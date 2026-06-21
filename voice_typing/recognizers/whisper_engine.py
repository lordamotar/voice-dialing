import logging
import numpy as np
from voice_typing.recognizers.base import Recognizer

logger = logging.getLogger(__name__)

class WhisperEngine(Recognizer):
    def __init__(self, model_size: str, device: str, compute_type_cpu: str, compute_type_gpu: str, language: str):
        self.model_size = model_size
        self.configured_device = device
        self.compute_type_cpu = compute_type_cpu
        self.compute_type_gpu = compute_type_gpu
        self.language = language
        
        # Map language codes (e.g., 'kz' maps to 'kk' in Whisper)
        self.whisper_lang = "kk" if language == "kz" else language

        # Buffer to accumulate raw PCM 16-bit 16kHz mono audio bytes
        self.audio_buffer = bytearray()

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "Библиотека 'faster-whisper' не установлена. Запустите 'uv sync' для установки зависимостей."
            )

        self.model = None
        self.active_device = None
        
        # Determine device and load model
        if device == "cuda":
            try:
                logger.info(f"Загрузка модели Whisper '{model_size}' на CUDA (GPU) с compute_type='{compute_type_gpu}'...")
                self.model = WhisperModel(model_size, device="cuda", compute_type=compute_type_gpu)
                self.active_device = "cuda"
            except Exception as e:
                raise RuntimeError(f"Не удалось инициализировать CUDA: {e}. Проверьте установку CUDA toolkit.")
        elif device == "cpu":
            logger.info(f"Загрузка модели Whisper '{model_size}' на CPU с compute_type='{compute_type_cpu}'...")
            self.model = WhisperModel(model_size, device="cpu", compute_type=compute_type_cpu)
            self.active_device = "cpu"
        else:  # auto
            # Try GPU first, fall back to CPU if it fails
            try:
                logger.info(f"Пытаюсь загрузить модель Whisper '{model_size}' на CUDA (GPU)...")
                self.model = WhisperModel(model_size, device="cuda", compute_type=compute_type_gpu)
                self.active_device = "cuda"
                logger.info("Успешно инициализирована CUDA.")
            except Exception as e:
                logger.warning(
                    f"CUDA недоступна или произошла ошибка при загрузке: {e}.\n"
                    f"Выполняю откат на CPU с compute_type='{compute_type_cpu}'..."
                )
                try:
                    self.model = WhisperModel(model_size, device="cpu", compute_type=compute_type_cpu)
                    self.active_device = "cpu"
                except Exception as e_cpu:
                    raise RuntimeError(
                        f"Не удалось запустить Whisper даже на CPU. Ошибка: {e_cpu}"
                    )

        logger.info(f"Модель Whisper загружена на устройстве: {self.active_device.upper()}")

    def accept_waveform(self, data: bytes) -> bool:
        """Accumulate audio chunks in the bytearray buffer."""
        self.audio_buffer.extend(data)
        return False  # Whisper runs batch transcription at the end

    def get_partial_result(self) -> str:
        """Whisper is a batch model, so partial transcription is not performant on every chunk."""
        return ""

    def get_final_result(self) -> str:
        """Process the accumulated audio buffer and return the transcription."""
        if not self.audio_buffer:
            logger.debug("Буфер аудио пуст, транскрипция пропущена.")
            return ""

        logger.info(f"Начало транскрипции Whisper ({len(self.audio_buffer)} байт)...")
        try:
            # Convert raw 16-bit PCM bytes to float32 NumPy array normalized to [-1.0, 1.0]
            audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16)
            audio_float = audio_data.astype(np.float32) / 32768.0

            # Transcribe
            # beam_size=5 is default for faster-whisper, language is explicitly set to avoid auto-detect errors
            segments, info = self.model.transcribe(
                audio_float,
                language=self.whisper_lang,
                beam_size=5
            )
            
            # Combine all transcribed segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            transcribed_text = "".join(text_segments).strip()
            logger.info(f"Распознано: '{transcribed_text}'")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Ошибка во время распознавания Whisper: {e}")
            return ""
        finally:
            # Clear buffer for next recording session
            self.audio_buffer.clear()
