# Dictator

Voice recording and transcription CLI tool that records audio using PyAudio (cross-platform), transcribes it using multiple backend services (Deepgram, AssemblyAI), applies context-aware LLM post-processing, and types the result using cross-platform text typing.

## Project Overview

This is a professional Python CLI application with a modular architecture:

- Records audio using PyAudio (cross-platform) with memory buffering
- Transcribes audio using multiple backends (Deepgram, AssemblyAI)
- Applies context-aware LLM post-processing based on focused application
- Types text using cross-platform input simulation (pynput)
- Provides visual feedback through system tray integration
- Manages process lifecycle with PID lockfiles

## Architecture

The codebase follows professional Python standards with clear separation of concerns:

```
dictator/
├── __init__.py          # Package exports
├── constants.py         # Configuration constants
├── exceptions.py        # Custom exception hierarchy
├── process_manager.py   # Process lifecycle & lockfile management
├── audio_recorder.py    # Cross-platform PyAudio recording with memory buffering
├── transcription/       # Transcription backends
│   ├── __init__.py      # Backend factory and exports
│   ├── base.py          # Abstract base class
│   ├── deepgram.py      # Deepgram API integration
│   └── assemblyai.py    # AssemblyAI API integration
├── llm_processor.py     # LLM-based post-processing with streaming
├── prompt_manager.py    # Configurable prompt system for LLM processing
├── window_detector.py   # Cross-platform window detection for context awareness
├── text_typer.py        # Cross-platform text typing using pynput
├── system_tray.py       # System tray status integration
└── app.py               # Main application orchestrator

main.py                  # CLI entry point
prompts.yaml             # LLM prompt configuration
```

## Development Guidelines

### Dependencies

- Always use `uv` for dependencies like `uv add` or `uv remove`
- Environment variables loaded via `python-dotenv`
- Requires `DEEPGRAM_API_KEY` environment variable for Deepgram backend
- Requires `ASSEMBLYAI_API_KEY` environment variable for AssemblyAI backend
- Requires `GEMINI_API_KEY` environment variable for LLM post-processing (optional)

### System Dependencies

- PyAudio for cross-platform audio recording
- pynput for cross-platform text typing automation
- System tray support via pystray
- Window detection tools (xdotool/xprop on Linux, AppleScript on macOS, Win32 API on Windows)
- Works on Linux, macOS, and Windows

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

- `DictatorApp`: Main orchestrator that coordinates all components with lazy initialization
- `ProcessManager`: Handles PID files and process lifecycle
- `AudioRecorder`: Encapsulates cross-platform PyAudio recording with memory buffering
- `TranscriptionBackend`: Abstract base class for transcription services
- `DeepgramBackend`: Deepgram API integration
- `AssemblyAIBackend`: AssemblyAI API integration
- `LLMPostProcessor`: LLM-based post-processing with streaming support
- `PromptManager`: Configurable prompt system for different applications
- `WindowDetector`: Cross-platform window detection for context awareness
- `SystemTrayManager`: Visual status feedback via system tray
- `TextTyper`: Cross-platform text typing using pynput

### Commands

- `python main.py begin` - Start recording with default Deepgram backend
- `python main.py begin --backend assemblyai` - Start recording with AssemblyAI backend
- `python main.py end` - Stop recording and transcribe (sends SIGTERM to process)

### Configuration

All constants in `dictator/constants.py`:

- File paths for lockfile and audio file
- Audio settings (16kHz, mono, 16-bit)
- Timeout values for process termination and LLM processing
- Default LLM model configuration
- Window detection timeout settings
- Transcription backend selection via `--backend` CLI argument (defaults to "deepgram", can be "assemblyai")

### Error Handling

- `DictatorError`: Base exception class
- `RecordingError`: Issues with audio recording
- `TranscriptionError`: Issues with transcription APIs
- `LLMProcessingError`: Issues with LLM post-processing
- `WindowDetectionError`: Issues with window detection
- `PromptConfigError`: Issues with prompt configuration
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

6. **Signal Handling**: The app uses signal handlers for graceful shutdown - be careful when modifying signal-related code

7. **Process Management**: The lockfile system prevents multiple instances - don't bypass these checks

8. **Audio Format**: Currently uses 16kHz WAV format optimized for Deepgram - changes may affect transcription quality

9. **Transcription Backends**: Supports both Deepgram (nova-3 model) and AssemblyAI backends - configure via `--backend` CLI argument

10. **LLM Post-Processing**: Context-aware text formatting based on focused application using Gemini Pro

11. **System Tray Integration**: Visual feedback during recording, transcription, and processing phases

12. **Cross-Platform Window Detection**: Automatic application context detection for appropriate text formatting

13. **Streaming Processing**: Real-time text typing as LLM generates output for better user experience

## Claude Memory

- Audio recording should always start ASAP as a priority
- Don't run the program on your own. I will run it.
- Apply formatting with `ruff format` after every change
