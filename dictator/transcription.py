"""Audio transcription service using Deepgram."""

import logging
from pathlib import Path

from deepgram import DeepgramClient, FileSource, PrerecordedOptions

from .exceptions import TranscriptionError

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Handles audio transcription using Deepgram."""
    
    def __init__(self):
        self.client = DeepgramClient()
    
    def transcribe_file(self, audio_file_path: Path) -> str:
        """Transcribe audio file and return transcript."""
        logger.info(f"Starting transcription of: {audio_file_path}")
        
        exists, file_size = self._validate_audio_file(audio_file_path)
        if not exists:
            raise TranscriptionError(f"Audio file does not exist: {audio_file_path}")
        if file_size == 0:
            raise TranscriptionError("Audio file is empty")
        
        logger.debug(f"Audio file size: {file_size} bytes")
        
        try:
            options = PrerecordedOptions(
                model="nova-3",
                language="en-US",
                punctuate=True,
                smart_format=True,
            )
            
            custom_options = {"mip_opt_out": "true"}
            
            logger.debug("Reading audio file for transcription")
            with open(audio_file_path, "rb") as audio_file:
                payload: FileSource = {"buffer": audio_file}
                
                logger.info("Sending audio to Deepgram")
                response = self.client.listen.rest.v("1").transcribe_file(
                    payload, options, addons=custom_options
                )
                logger.debug("Received response from Deepgram")
            
            return self._extract_transcript(response)
            
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
    
    def _validate_audio_file(self, audio_file_path: Path) -> tuple[bool, int]:
        """Validate audio file exists and get size."""
        try:
            if not audio_file_path.exists():
                return False, 0
            size = audio_file_path.stat().st_size
            return True, size
        except OSError:
            return False, 0
    
    def _extract_transcript(self, response) -> str:
        """Extract transcript from Deepgram response."""
        if not (response.results and response.results.channels):
            logger.error("No transcription results or channels found")
            logger.debug(f"Response structure: {response}")
            return ""
        
        logger.debug(f"Response has {len(response.results.channels)} channels")
        
        channel = response.results.channels[0]
        if not channel.alternatives:
            logger.warning("No alternatives found in transcription response")
            return ""
        
        logger.debug(f"Channel 0 has {len(channel.alternatives)} alternatives")
        
        alternative = channel.alternatives[0]
        transcript = alternative.transcript
        confidence = getattr(alternative, "confidence", "unknown")
        
        logger.info(f"Transcription completed, confidence: {confidence}")
        logger.debug(f"Raw transcript: '{transcript}'")
        
        cleaned_transcript = transcript.strip()
        logger.debug(f"Cleaned transcript: '{cleaned_transcript}'")
        
        return cleaned_transcript