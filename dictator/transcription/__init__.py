"""Transcription backends package."""

from .base import TranscriptionBackend
from .deepgram import DeepgramBackend
from .assemblyai import AssemblyAIBackend


def create_transcription_backend(backend: str = "deepgram") -> TranscriptionBackend:
    """Factory function to create appropriate transcription backend."""
    if backend.lower() == "assemblyai":
        return AssemblyAIBackend()
    elif backend.lower() == "deepgram":
        return DeepgramBackend()
    else:
        raise ValueError(f"Unknown transcription backend: {backend}")


__all__ = [
    "TranscriptionBackend",
    "DeepgramBackend",
    "AssemblyAIBackend",
    "create_transcription_backend",
]
