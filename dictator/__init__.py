"""
Dictator: Voice recording and transcription tool.

A CLI tool that records audio using PulseAudio, transcribes it using Deepgram,
and types the result using xdotool.
"""

from .app import DictatorApp
from .exceptions import DictatorError, RecordingError, TranscriptionError

__version__ = "1.0.0"
__all__ = ["DictatorApp", "DictatorError", "RecordingError", "TranscriptionError"]