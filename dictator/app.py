"""Main application class for Dictator."""

import logging
import os
import signal
import sys

from .audio_recorder import AudioRecorder
from .constants import AUDIO_FILE_PATH, LOCKFILE_PATH
from .exceptions import DictatorError, TranscriptionError
from .process_manager import ProcessManager
from .text_typer import TextTyper
from .transcription import TranscriptionService

logger = logging.getLogger(__name__)


class DictatorApp:
    """Main application class for Dictator."""
    
    def __init__(self):
        self.process_manager = ProcessManager(LOCKFILE_PATH)
        self.recorder = AudioRecorder(AUDIO_FILE_PATH)
        self.transcription_service = TranscriptionService()
        self.text_typer = TextTyper()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal: {signum}")
        self._cleanup_and_exit()
    
    def begin_recording(self) -> None:
        """Start recording session."""
        logger.info("Starting begin command")
        
        try:
            self.process_manager.create_lockfile()
            self.recorder.start_recording()
            
            logger.info("Recording started. Use 'end' command to stop and transcribe.")
            
            # Keep running until signal received
            logger.debug("Entering main loop, waiting for signals")
            while True:
                signal.pause()
                
        except DictatorError as e:
            logger.error(f"Recording error: {e}")
            self._cleanup_and_exit()
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt")
            self._cleanup_and_exit()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self._cleanup_and_exit()
    
    def end_recording(self) -> None:
        """Stop recording and transcribe."""
        logger.info("Starting end command")
        
        pid = self.process_manager.get_running_pid()
        if not pid:
            logger.warning("No running recording process found")
            return
        
        try:
            logger.info(f"Sending stop signal to process {pid}")
            os.kill(pid, signal.SIGTERM)
            logger.info("Stop signal sent successfully")
        except ProcessLookupError:
            logger.warning(f"Process {pid} no longer exists")
        except PermissionError:
            logger.error(f"No permission to signal process {pid}")
        except OSError as e:
            logger.error(f"Error sending signal: {e}")
    
    def _cleanup_and_exit(self) -> None:
        """Cleanup resources and exit."""
        logger.info("Starting cleanup")
        
        # Stop recording
        self.recorder.stop_recording()
        
        # Process transcription
        exists, file_size = self.recorder.get_file_info()
        if exists and file_size > 0:
            try:
                logger.info("Starting transcription...")
                transcript = self.transcription_service.transcribe_file(AUDIO_FILE_PATH)
                
                if transcript:
                    logger.info(f"Transcription successful, length: {len(transcript)} chars")
                    self.text_typer.type_text(transcript)
                else:
                    logger.warning("No transcript generated")
                    
            except TranscriptionError as e:
                logger.error(f"Transcription failed: {e}")
        elif exists:
            logger.warning("Audio file is empty")
        else:
            logger.warning("No audio file found")
        
        # Cleanup
        self.process_manager._cleanup_lockfile()
        
        logger.info("Cleanup completed, exiting")
        sys.exit(0)