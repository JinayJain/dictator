"""Constants for the Dictator application."""

from pathlib import Path

# File paths
LOCKFILE_PATH = Path("/tmp/dictator.pid")
AUDIO_FILE_PATH = Path("/tmp/dictator_recording.wav")

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1

# Timeouts
PROCESS_TERMINATE_TIMEOUT = 5

# LLM Post-processing
DEFAULT_LLM_MODEL = "gemini/gemini-2.0-flash"
LLM_PROCESSING_TIMEOUT = 30
