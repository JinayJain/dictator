"""Constants for the Dictator application."""

from pathlib import Path

# File paths
LOCKFILE_PATH = Path("/tmp/dictator.pid")
AUDIO_FILE_PATH = Path("/tmp/dictator_recording.wav")

# Audio settings
SAMPLE_RATE = 16000
AUDIO_FORMAT = "s16le"
CHANNELS = 1

# Timeouts
PROCESS_TERMINATE_TIMEOUT = 5
XDOTOOL_TIMEOUT = 30