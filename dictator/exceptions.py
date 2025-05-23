"""Custom exceptions for the Dictator application."""


class DictatorError(Exception):
    """Base exception for Dictator application."""
    pass


class RecordingError(DictatorError):
    """Raised when recording operations fail."""
    pass


class TranscriptionError(DictatorError):
    """Raised when transcription operations fail."""
    pass