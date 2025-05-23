"""Main application class for Dictator."""

import logging
import os
import signal
import sys
import time

from .audio_recorder import AudioRecorder
from .constants import AUDIO_FILE_PATH, LOCKFILE_PATH
from .exceptions import DictatorError, TranscriptionError
from .process_manager import ProcessManager

logger = logging.getLogger(__name__)


class DictatorApp:
    """Main application class for Dictator."""
    
    def __init__(self, backend: str = "deepgram"):
        # Store backend for lazy initialization
        self.backend = backend
        
        # Essential components for recording startup
        self.process_manager = ProcessManager(LOCKFILE_PATH)
        self.recorder = AudioRecorder(AUDIO_FILE_PATH)
        
        # Components that will be lazily initialized
        self.transcription_service = None
        self._transcription_initialized = False
        self.text_typer = None
        self._text_typer_initialized = False
        self.system_tray = None
        self._system_tray_initialized = False
        self.llm_processor = None
        self._llm_processor_initialized = False
        
        self._setup_signal_handlers()
    
    def _get_transcription_service(self):
        """Lazily initialize and return the transcription service if not already done."""
        if not self._transcription_initialized:
            try:
                from .transcription import create_transcription_backend
                self.transcription_service = create_transcription_backend(self.backend)
            except Exception as e:
                logger.error(f"Failed to initialize transcription service: {e}")
                raise
            finally:
                self._transcription_initialized = True
        
        return self.transcription_service
    
    def _get_text_typer(self):
        """Lazily initialize and return the text typer if not already done."""
        if not self._text_typer_initialized:
            try:
                from .text_typer import TextTyper
                self.text_typer = TextTyper()
            except Exception as e:
                logger.error(f"Failed to initialize text typer: {e}")
                raise
            finally:
                self._text_typer_initialized = True
        
        return self.text_typer
    
    def _get_system_tray(self):
        """Lazily initialize and return the system tray if not already done."""
        if not self._system_tray_initialized:
            try:
                from .system_tray import SystemTrayManager
                self.system_tray = SystemTrayManager()
            except Exception as e:
                logger.error(f"Failed to initialize system tray: {e}")
                raise
            finally:
                self._system_tray_initialized = True
        
        return self.system_tray
    
    def _get_llm_processor(self):
        """Lazily initialize and return the LLM processor if not already done."""
        if not self._llm_processor_initialized:
            try:
                from .llm_processor import LLMPostProcessor
                self.llm_processor = LLMPostProcessor()
                logger.info("LLM post-processing enabled")
            except Exception as e:
                logger.info(f"LLM post-processing disabled: {e}")
                self.llm_processor = None
            finally:
                self._llm_processor_initialized = True
        
        return self.llm_processor
    
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
            # Start recording ASAP - only essential components
            self.process_manager.create_lockfile()
            self.recorder.start_recording()
            logger.info("Recording started. Use 'end' command to stop and transcribe.")
            
            # Now that recording is started, initialize system tray in background
            try:
                system_tray = self._get_system_tray()
                system_tray.start()
                system_tray.set_recording_state()
            except Exception as e:
                logger.warning(f"System tray initialization failed, continuing without it: {e}")
            
            # Keep running until signal received
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
        
        # Stop recording and get audio data from memory
        audio_data = self.recorder.stop_recording()
        
        # Log memory buffer info
        memory_size = len(audio_data)
        
        # Check if WAV file was created
        exists, file_size = self.recorder.get_file_info()
        
        if exists and file_size > 0:
            try:
                # Update tray to transcribing state (if available)
                if self._system_tray_initialized and self.system_tray:
                    self.system_tray.set_transcribing_state()
                
                logger.info(f"Starting transcription of {file_size} byte WAV file...")
                transcription_service = self._get_transcription_service()
                transcript = transcription_service.transcribe_file(AUDIO_FILE_PATH)
                
                if transcript:
                    logger.info(f"Transcription successful, length: {len(transcript)} chars")
                    
                    # Apply LLM post-processing if available, with streaming
                    text_typer = self._get_text_typer()
                    llm_processor = self._get_llm_processor()
                    if llm_processor and llm_processor.is_enabled():
                        # Update tray to processing state
                        if self._system_tray_initialized and self.system_tray:
                            self.system_tray.set_processing_state()
                        
                        # Use streaming processing that types as it generates
                        llm_processor.process_transcript_streaming(
                            transcript, 
                            text_typer.type_text_chunk
                        )
                    else:
                        # No LLM processing, type original transcript
                        text_typer.type_text(transcript)
                else:
                    logger.warning("No transcript generated")
                    
            except TranscriptionError as e:
                logger.error(f"Transcription failed: {e}")
        elif memory_size > 0:
            logger.warning(f"Had {memory_size} bytes in memory but WAV file creation failed")
        else:
            logger.warning("No audio data recorded")
        
        # Cleanup
        self.process_manager._cleanup_lockfile()
        if self._system_tray_initialized and self.system_tray:
            self.system_tray.stop()
        
        logger.info("Cleanup completed, exiting")
        sys.exit(0)