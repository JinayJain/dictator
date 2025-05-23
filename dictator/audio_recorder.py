"""Audio recording functionality using PulseAudio."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from .constants import AUDIO_FORMAT, CHANNELS, PROCESS_TERMINATE_TIMEOUT, SAMPLE_RATE
from .exceptions import RecordingError

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Handles audio recording using PulseAudio."""
    
    def __init__(self, audio_file_path: Path):
        self.audio_file_path = audio_file_path
        self.process: Optional[subprocess.Popen] = None
    
    def start_recording(self) -> None:
        """Start audio recording process."""
        self._cleanup_existing_file()
        
        cmd = [
            "parec",
            "--file-format=wav",
            f"--format={AUDIO_FORMAT}",
            f"--rate={SAMPLE_RATE}",
            f"--channels={CHANNELS}",
            str(self.audio_file_path),
        ]
        
        logger.info("Starting audio recording...")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        try:
            self.process = subprocess.Popen(cmd)
            logger.info(f"Recording process started with PID: {self.process.pid}")
        except FileNotFoundError:
            raise RecordingError("parec command not found. Please install PulseAudio utilities.")
        except OSError as e:
            raise RecordingError(f"Failed to start recording: {e}")
    
    def stop_recording(self) -> None:
        """Stop audio recording process."""
        if not self.process:
            logger.warning("No recording process to stop")
            return
        
        logger.info(f"Stopping recording process (PID: {self.process.pid})")
        
        try:
            self.process.terminate()
            logger.debug("Sent terminate signal")
            
            try:
                self.process.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                logger.info("Recording process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Process didn't terminate gracefully, killing it")
                self.process.kill()
                self.process.wait()
                logger.info("Recording process killed")
        except OSError as e:
            logger.error(f"Error stopping recording process: {e}")
    
    def _cleanup_existing_file(self) -> None:
        """Remove existing audio file if it exists."""
        try:
            if self.audio_file_path.exists():
                self.audio_file_path.unlink()
                logger.debug("Removed existing audio file")
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