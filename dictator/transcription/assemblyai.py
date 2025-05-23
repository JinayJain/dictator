"""Audio transcription service using AssemblyAI."""

import logging
import os
from pathlib import Path

try:
    import assemblyai as aai
except ImportError:
    aai = None

from ..exceptions import TranscriptionError
from .base import TranscriptionBackend

logger = logging.getLogger(__name__)


class AssemblyAIBackend(TranscriptionBackend):
    """Handles audio transcription using AssemblyAI."""

    def __init__(self):
        if aai is None:
            raise TranscriptionError(
                "AssemblyAI package not installed. Run: uv add assemblyai"
            )

        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        self.transcriber = aai.Transcriber(config=config)

    def transcribe_file(self, audio_file_path: Path) -> str:
        """Transcribe audio file and return transcript."""
        logger.info(f"Starting AssemblyAI transcription of: {audio_file_path}")

        exists, file_size = self._validate_audio_file(audio_file_path)
        if not exists:
            raise TranscriptionError(f"Audio file does not exist: {audio_file_path}")
        if file_size == 0:
            raise TranscriptionError("Audio file is empty")


        try:
            logger.info("Sending audio to AssemblyAI")
            transcript = self.transcriber.transcribe(str(audio_file_path))

            if transcript.error:
                raise TranscriptionError(
                    f"AssemblyAI transcription failed: {transcript.error}"
                )

            result = transcript.text or ""
            logger.info(
                f"AssemblyAI transcription completed, length: {len(result)} chars"
            )

            cleaned_transcript = result.strip()

            return cleaned_transcript

        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"AssemblyAI transcription failed: {e}")

    def _validate_audio_file(self, audio_file_path: Path) -> tuple[bool, int]:
        """Validate audio file exists and get size."""
        try:
            if not audio_file_path.exists():
                return False, 0
            size = audio_file_path.stat().st_size
            return True, size
        except OSError:
            return False, 0
