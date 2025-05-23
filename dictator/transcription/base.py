"""Abstract base class for transcription backends."""

from abc import ABC, abstractmethod
from pathlib import Path


class TranscriptionBackend(ABC):
    """Abstract base class for transcription services."""

    @abstractmethod
    def transcribe_file(self, audio_file_path: Path) -> str:
        """Transcribe audio file and return transcript.

        Args:
            audio_file_path: Path to the audio file to transcribe

        Returns:
            Transcribed text as a string

        Raises:
            TranscriptionError: If transcription fails
        """
        pass
