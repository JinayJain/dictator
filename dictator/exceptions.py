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


class WindowDetectionError(DictatorError):
    """Raised when window detection operations fail."""
    pass


class LLMProcessingError(DictatorError):
    """Raised when LLM post-processing operations fail."""
    pass


class PromptConfigError(DictatorError):
    """Raised when prompt configuration is invalid."""
    pass