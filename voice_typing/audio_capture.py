import queue
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class AudioCaptureError(Exception):
    """Exception raised for errors during audio capture initialization or recording."""
    pass

class AudioCapture:
    def __init__(self, sample_rate: int = 16000, block_size: int = 4000, device_index: Optional[int] = None):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.device_index = device_index
        self.queue: queue.Queue = queue.Queue()
        self.is_recording = False
        
        self._sd_stream = None
        self._pa_instance = None
        self._pa_stream = None
        self._pa_thread = None
        self._backend = None  # 'sounddevice' or 'pyaudio'

    def start(self):
        """Start capturing audio in a separate thread/callback."""
        if self.is_recording:
            return

        self.queue = queue.Queue()
        self.is_recording = True
        
        # Try sounddevice first
        try:
            import sounddevice as sd
            
            # Verify devices are available
            devices = sd.query_devices()
            if not devices:
                raise AudioCaptureError("Устройства ввода звука не найдены.")
            
            def sd_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Статус sounddevice: {status}")
                if self.is_recording:
                    self.queue.put(bytes(indata))

            self._sd_stream = sd.RawInputStream(
                device=self.device_index,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=1,
                callback=sd_callback
            )
            self._sd_stream.start()
            self._backend = 'sounddevice'
            logger.info("Аудиозахват успешно запущен через sounddevice.")
            return
        except Exception as e:
            logger.warning(f"Не удалось запустить sounddevice: {e}. Пробую pyaudio в качестве fallback...")
            self._cleanup_sounddevice()

        # Fallback to PyAudio
        try:
            import pyaudio
            self._pa_instance = pyaudio.PyAudio()
            
            # Verify input device exists
            try:
                default_device = self._pa_instance.get_default_input_device_info()
                logger.debug(f"Используется устройство PyAudio по умолчанию: {default_device.get('name')}")
            except Exception:
                raise AudioCaptureError("Устройства ввода звука не найдены в PyAudio.")

            self._pa_stream = self._pa_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.block_size
            )
            
            self._pa_thread = threading.Thread(target=self._pyaudio_read_loop, daemon=True)
            self._pa_thread.start()
            self._backend = 'pyaudio'
            logger.info("Аудиозахват успешно запущен через pyaudio (fallback).")
        except Exception as e:
            self.is_recording = False
            self._cleanup_pyaudio()
            raise AudioCaptureError(
                "Не удалось инициализировать запись звука. Убедитесь, что микрофон подключен "
                f"и разрешен доступ к аудиоустройствам. Детали ошибки: {e}"
            )

    def _pyaudio_read_loop(self):
        """Background thread to read data from pyaudio stream."""
        while self.is_recording and self._pa_stream:
            try:
                # read without exception on overflow to keep stream alive
                data = self._pa_stream.read(self.block_size, exception_on_overflow=False)
                if data:
                    self.queue.put(data)
            except Exception as e:
                logger.error(f"Ошибка при чтении аудиопотока PyAudio: {e}")
                break

    def stop(self):
        """Stop capturing audio and clean up streams."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        logger.info("Остановка аудиозахвата...")
        
        if self._backend == 'sounddevice':
            self._cleanup_sounddevice()
        elif self._backend == 'pyaudio':
            self._cleanup_pyaudio()
            
        self._backend = None

    def get_chunk(self, timeout: Optional[float] = None) -> bytes:
        """Get an audio chunk from the queue. Raises queue.Empty if timeout occurs."""
        return self.queue.get(timeout=timeout)

    def _cleanup_sounddevice(self):
        if self._sd_stream:
            try:
                self._sd_stream.stop()
                self._sd_stream.close()
            except Exception as e:
                logger.debug(f"Ошибка при очистке sounddevice: {e}")
            self._sd_stream = None

    def _cleanup_pyaudio(self):
        if self._pa_stream:
            try:
                self._pa_stream.stop_stream()
                self._pa_stream.close()
            except Exception as e:
                logger.debug(f"Ошибка при закрытии потока PyAudio: {e}")
            self._pa_stream = None
            
        if self._pa_thread:
            try:
                self._pa_thread.join(timeout=1.0)
            except Exception:
                pass
            self._pa_thread = None

        if self._pa_instance:
            try:
                self._pa_instance.terminate()
            except Exception as e:
                logger.debug(f"Ошибка при завершении PyAudio: {e}")
            self._pa_instance = None
