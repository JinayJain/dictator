# Dictator

Voice recording and transcription CLI tool that records audio using PulseAudio, transcribes it using Deepgram, and types the result using xdotool.

## Project Overview

This is a professional Python CLI application with a modular architecture:

- Records audio using `parec` (PulseAudio)
- Transcribes audio using Deepgram API
- Types transcribed text using `xdotool`
- Manages process lifecycle with PID lockfiles

## Architecture

The codebase follows professional Python standards with clear separation of concerns:

```
dictator/
├── __init__.py          # Package exports
├── constants.py         # Configuration constants
├── exceptions.py        # Custom exception hierarchy
├── process_manager.py   # Process lifecycle & lockfile management
├── audio_recorder.py    # PulseAudio recording
├── transcription/       # Transcription backends
│   ├── __init__.py      # Backend factory and exports
│   ├── base.py          # Abstract base class
│   ├── deepgram.py      # Deepgram API integration
│   └── assemblyai.py    # AssemblyAI API integration
├── text_typer.py       # xdotool text typing
└── app.py              # Main application orchestrator

main.py                  # CLI entry point
```

## Development Guidelines

### Dependencies

- Always use `uv` for dependencies like `uv add` or `uv remove`
- Environment variables loaded via `python-dotenv`
- Requires `DEEPGRAM_API_KEY` environment variable for Deepgram backend
- Requires `ASSEMBLYAI_API_KEY` environment variable for AssemblyAI backend

### System Dependencies

- `parec` (PulseAudio utilities) for audio recording
- `xdotool` for text typing automation
- Works on Linux systems with PulseAudio and X11

### Code Style

- Use type hints throughout (already implemented)
- Follow professional OOP patterns with focused classes
- Comprehensive logging at DEBUG level by default
- Custom exceptions for proper error handling
- Use `pathlib.Path` for file operations
- Constants defined in dedicated module

### Architecture Patterns

- **Single Responsibility**: Each class has one focused purpose
- **Dependency Injection**: Components passed to orchestrator
- **Error Handling**: Custom exception hierarchy with specific error types
- **Resource Management**: Proper cleanup in all error paths
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT

### Key Classes

- `DictatorApp`: Main orchestrator that coordinates all components
- `ProcessManager`: Handles PID files and process lifecycle
- `AudioRecorder`: Encapsulates PulseAudio recording logic
- `TranscriptionBackend`: Abstract base class for transcription services
- `DeepgramBackend`: Deepgram API integration
- `AssemblyAIBackend`: AssemblyAI API integration
- `TextTyper`: xdotool automation

### Commands

- `python main.py begin` - Start recording with default Deepgram backend
- `python main.py begin --backend assemblyai` - Start recording with AssemblyAI backend
- `python main.py end` - Stop recording and transcribe (sends SIGTERM to process)

### Configuration

All constants in `dictator/constants.py`:

- File paths for lockfile and audio file
- Audio settings (16kHz, mono, 16-bit)
- Timeout values for process termination
- Transcription backend selection via `--backend` CLI argument (defaults to "deepgram", can be "assemblyai")

### Error Handling

- `DictatorError`: Base exception class
- `RecordingError`: Issues with audio recording
- `TranscriptionError`: Issues with Deepgram API
- All exceptions logged with full context

### Logging

- DEBUG level enabled by default for troubleshooting
- Structured logging with timestamps
- Comprehensive logging in all operations for debugging transcription issues

## Important Notes for LLMs

1. **Modular Design**: When making changes, respect the module boundaries. Don't put transcription logic in the recorder, etc.

2. **Type Safety**: Maintain type hints and use proper return types

3. **Error Handling**: Always use custom exceptions rather than generic ones

4. **Resource Cleanup**: Ensure proper cleanup of processes, files, and lockfiles in all code paths

5. **Constants**: Put configuration values in `constants.py`, not hardcoded in methods

6. **Testing Strategy**: Each module can be unit tested independently due to clean separation

7. **Signal Handling**: The app uses signal handlers for graceful shutdown - be careful when modifying signal-related code

8. **Process Management**: The lockfile system prevents multiple instances - don't bypass these checks

9. **Audio Format**: Currently uses 16kHz WAV format optimized for Deepgram - changes may affect transcription quality

10. **Transcription Backends**: Supports both Deepgram (nova-3 model) and AssemblyAI backends - configure via `--backend` CLI argument

## Claude Memory

- Audio recording should always start ASAP as a priority
- Don't run the program on your own. I will run it.
- Apply formatting with `ruff format` after every change