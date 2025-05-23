"""Audio recording functionality using PulseAudio."""

import fcntl
import io
import logging
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from .constants import AUDIO_FORMAT, CHANNELS, PROCESS_TERMINATE_TIMEOUT, SAMPLE_RATE
from .exceptions import RecordingError

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Handles audio recording using PulseAudio in memory."""

    def __init__(self, audio_file_path: Path):
        self.audio_file_path = audio_file_path  # Still used for final WAV file creation
        self.process: Optional[subprocess.Popen] = None
        self.audio_buffer = io.BytesIO()
        self.recording_thread: Optional[threading.Thread] = None
        self.is_recording = False
        self.block_size = 1024 * 16  # 16KB blocks for good balance

    def start_recording(self) -> None:
        """Start audio recording process to memory."""
        self._cleanup_existing_file()

        cmd = [
            "parec",
            "--record",
            f"--rate={SAMPLE_RATE}",
            "--channels=1",
            "--format=s16ne",  # 16-bit signed native endian (matches nerd-dictation)
            "--latency=10",  # Low latency like nerd-dictation
        ]

        logger.info("Starting audio recording to memory...")

        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            logger.info(f"Recording process started with PID: {self.process.pid}")

            # Make stdout non-blocking like nerd-dictation
            self._make_non_blocking(self.process.stdout)

            # Reset buffer and start recording thread
            self.audio_buffer.seek(0)
            self.audio_buffer.truncate(0)
            self.is_recording = True

            self.recording_thread = threading.Thread(
                target=self._record_to_memory, daemon=True
            )
            self.recording_thread.start()

        except FileNotFoundError:
            raise RecordingError(
                "parec command not found. Please install PulseAudio utilities."
            )
        except OSError as e:
            raise RecordingError(f"Failed to start recording: {e}")

    def _make_non_blocking(self, file_handle) -> None:
        """Make file handle non-blocking using fcntl."""
        flags = fcntl.fcntl(file_handle.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(file_handle, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _record_to_memory(self) -> None:
        """Record audio data to memory buffer in separate thread."""
        bytes_recorded = 0

        while self.is_recording and self.process:
            try:
                data = self.process.stdout.read(self.block_size)
                if data:
                    self.audio_buffer.write(data)
                    bytes_recorded += len(data)
                else:
                    # No data available, sleep briefly to avoid busy waiting
                    time.sleep(0.001)  # 1ms

            except BlockingIOError:
                # No data available right now, continue
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"Error reading audio data: {e}")
                break

        logger.info(
            f"Recording thread finished, total bytes recorded: {bytes_recorded}"
        )

    def stop_recording(self) -> bytes:
        """Stop audio recording process and return recorded data."""
        if not self.process:
            logger.warning("No recording process to stop")
            return b""

        logger.info(f"Stopping recording process (PID: {self.process.pid})")

        # Stop the recording loop
        self.is_recording = False

        try:
            # Send SIGINT first (more graceful than SIGTERM for audio recording)
            self.process.send_signal(signal.SIGINT)

            # Give the recording thread a moment to finish reading any remaining data
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)

            try:
                # Wait for process to terminate
                self.process.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                logger.info("Recording process terminated gracefully after SIGINT")
            except subprocess.TimeoutExpired:
                logger.warning("Process didn't respond to SIGINT, trying SIGTERM")
                self.process.terminate()

                try:
                    self.process.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                    logger.info("Recording process terminated after SIGTERM")
                except subprocess.TimeoutExpired:
                    logger.warning("Process didn't terminate gracefully, killing it")
                    self.process.kill()
                    self.process.wait()
                    logger.info("Recording process killed")

        except OSError as e:
            logger.error(f"Error stopping recording process: {e}")

        # Get the recorded data
        audio_data = self.audio_buffer.getvalue()
        logger.info(f"Retrieved {len(audio_data)} bytes of audio data from memory")

        # Create WAV file from raw audio data
        if audio_data:
            self._create_wav_file(audio_data)

        return audio_data

    def _create_wav_file(self, raw_audio_data: bytes) -> None:
        """Create WAV file from raw audio data."""
        import struct
        import wave

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
