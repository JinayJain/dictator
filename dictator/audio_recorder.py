"""Cross-platform audio recording functionality using PyAudio."""

import io
import logging
import threading
import time
import wave
from pathlib import Path
from typing import Optional

import pyaudio

from .constants import CHANNELS, SAMPLE_RATE
from .exceptions import RecordingError

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Handles cross-platform audio recording using PyAudio."""

    def __init__(self, audio_file_path: Path):
        self.audio_file_path = audio_file_path
        self.audio_buffer = io.BytesIO()
        self.recording_thread: Optional[threading.Thread] = None
        self.is_recording = False
        self.audio_instance: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.chunk_size = 1024  # Number of frames per buffer

    def start_recording(self) -> None:
        """Start audio recording using PyAudio."""
        self._cleanup_existing_file()

        logger.info("Starting cross-platform audio recording...")

        try:
            # Initialize PyAudio
            self.audio_instance = pyaudio.PyAudio()

            # Configure audio stream
            self.stream = self.audio_instance.open(
                format=pyaudio.paInt16,  # 16-bit audio
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            logger.info("Audio stream opened successfully")

            # Reset buffer and start recording
            self.audio_buffer.seek(0)
            self.audio_buffer.truncate(0)
            self.is_recording = True

            self.recording_thread = threading.Thread(
                target=self._record_to_memory, daemon=True
            )
            self.recording_thread.start()

        except OSError as e:
            self._cleanup_audio_resources()
            raise RecordingError(f"Failed to initialize audio recording: {e}")
        except Exception as e:
            self._cleanup_audio_resources()
            raise RecordingError(f"Unexpected error starting recording: {e}")

    def _record_to_memory(self) -> None:
        """Record audio data to memory buffer in separate thread."""
        bytes_recorded = 0

        try:
            while self.is_recording and self.stream:
                try:
                    # Read audio data from stream
                    data = self.stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    if data:
                        self.audio_buffer.write(data)
                        bytes_recorded += len(data)

                except OSError as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error during recording: {e}")
                    break

        finally:
            logger.info(
                f"Recording thread finished, total bytes recorded: {bytes_recorded}"
            )

    def stop_recording(self) -> bytes:
        """Stop audio recording and return recorded data."""
        if not self.is_recording:
            logger.warning("No active recording to stop")
            return b""

        logger.info("Stopping audio recording...")

        # Stop the recording loop
        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)
            if self.recording_thread.is_alive():
                logger.warning("Recording thread did not finish within timeout")

        # Stop and close audio stream
        self._cleanup_audio_resources()

        # Get the recorded data
        audio_data = self.audio_buffer.getvalue()
        logger.info(f"Retrieved {len(audio_data)} bytes of audio data from memory")

        # Create WAV file from recorded data
        if audio_data:
            self._create_wav_file(audio_data)

        return audio_data

    def _create_wav_file(self, raw_audio_data: bytes) -> None:
        """Create WAV file from raw audio data."""
        try:
            with wave.open(str(self.audio_file_path), "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(raw_audio_data)

            logger.info(f"Created WAV file: {self.audio_file_path}")

        except Exception as e:
            logger.error(f"Error creating WAV file: {e}")
            raise RecordingError(f"Failed to create WAV file: {e}")

    def _cleanup_audio_resources(self) -> None:
        """Clean up PyAudio resources."""
        try:
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            if self.audio_instance:
                self.audio_instance.terminate()
                self.audio_instance = None

        except Exception as e:
            logger.error(f"Error cleaning up audio resources: {e}")

    def _cleanup_existing_file(self) -> None:
        """Remove existing audio file if it exists."""
        try:
            if self.audio_file_path.exists():
                self.audio_file_path.unlink()
        except OSError as e:
            logger.warning(f"Error removing existing audio file: {e}")

    def get_file_info(self) -> tuple[bool, int]:
        """Get audio file existence and size."""
        if not self.audio_file_path.exists():
            return False, 0

        try:
            size = self.audio_file_path.stat().st_size
            return True, size
        except OSError:
            return False, 0

    def get_memory_buffer_size(self) -> int:
        """Get current size of audio data in memory buffer."""
        return len(self.audio_buffer.getvalue())

    def __del__(self):
        """Ensure audio resources are cleaned up when object is destroyed."""
        self._cleanup_audio_resources()
