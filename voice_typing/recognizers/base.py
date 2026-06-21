from abc import ABC, abstractmethod

class Recognizer(ABC):
    """Abstract base class representing a speech recognition engine."""

    @abstractmethod
    def accept_waveform(self, data: bytes) -> bool:
        """Feed a chunk of raw 16-bit mono 16kHz audio bytes to the recognizer.
        
        Returns:
            bool: True if a complete sentence/phrase boundary is detected, False otherwise.
        """
        pass

    @abstractmethod
    def get_partial_result(self) -> str:
        """Retrieve the current partial (intermediate) transcription.
        
        Returns:
            str: The raw transcribed text.
        """
        pass

    @abstractmethod
    def get_final_result(self) -> str:
        """Finalize and retrieve the complete transcription for the captured audio.
        
        Returns:
            str: The final transcribed text.
        """
        pass
