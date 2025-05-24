# Dictator

A professional voice recording and transcription CLI tool that records audio using PyAudio (cross-platform), transcribes it using multiple backend services (Deepgram, AssemblyAI), and intelligently post-processes the text with LLM-based context-aware formatting before typing it using xdotool.

## Demo

https://github.com/user-attachments/assets/16fb20ff-84d7-4cb8-92b0-2cca199d8687

https://github.com/user-attachments/assets/8d9ebae4-d7c1-446c-be1e-a7b753d348e4



## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file in the project root with your API keys:

   ```
   # Required for Deepgram backend (default)
   DEEPGRAM_API_KEY=your_deepgram_api_key_here

   # Required for AssemblyAI backend (optional)
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

   # Required for LLM post-processing (optional)
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   You can use the provided `.env.example` file as a template:

   ```bash
   cp .env.example .env
   # Then edit .env with your actual API keys
   ```

   **API Key Sources:**

   - Deepgram: [deepgram.com](https://deepgram.com)
   - AssemblyAI: [assemblyai.com](https://assemblyai.com)
   - Gemini: [Google AI Studio](https://aistudio.google.com)

## Usage

### Basic Commands

1. **Start dictation** (using default Deepgram backend):

   ```bash
   uv run main.py begin
   ```

2. **Start dictation with specific backend**:

   ```bash
   uv run main.py begin --backend assemblyai
   ```

3. **End dictation and type the transcribed text**:
   ```bash
   uv run main.py end
   ```

### LLM Post-Processing

When `GEMINI_API_KEY` is configured, Dictator automatically applies context-aware text processing based on the focused application:

- **Chat Apps** (Discord, Slack): Super casual with lowercase and texting slang
- **Web Browsers** (Chrome, Firefox): Casual and informal for web interactions
- **Code Editors** (VSCode, vim): Formatted as proper code comments
- **Office Apps** (LibreOffice, Email): Professional and formal tone
- **Everything Else**: No processing (original transcript)

### Customizing Prompts

Edit `prompts.yaml` to customize LLM processing for different applications:

```yaml
prompts:
  your_custom_prompt:
    name: "Custom Style"
    description: "Your custom processing style"
    template: |
      Your custom prompt here...

      Original text: {transcript}

      Output only the processed text.

applications:
  your_app_group:
    patterns: ["your-app", "another-app"]
    prompt: "your_custom_prompt"
```

## Hotkey Setup with sxhkd

For convenient voice dictation, you can set up global hotkeys using `sxhkd`. This allows you to start/stop dictation from anywhere on your system.

### Install sxhkd

```bash
# Ubuntu/Debian
sudo apt install sxhkd

# Arch Linux
sudo pacman -S sxhkd

# Fedora
sudo dnf install sxhkd
```

### Configure Hotkeys

Add these bindings to your `~/.config/sxhkd/sxhkdrc` file:

```bash
# Start dictation with Scroll Lock key
Scroll_Lock
    cd $DICTATOR_DIR ; uv run main.py begin --backend deepgram

# Stop dictation on Scroll Lock key release
@Scroll_Lock
    cd $DICTATOR_DIR ; uv run main.py end
```

### Environment Setup

Set the `DICTATOR_DIR` environment variable to point to your dictator installation. Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export DICTATOR_DIR="/path/to/dictator"
```

**Note**: Replace `/path/to/dictator` with the actual path to your dictator installation.

### Start sxhkd

Add sxhkd to your window manager startup or run it manually:

```bash
# Start sxhkd (run this once per session)
sxhkd &

# Or add to your ~/.xinitrc or window manager config
```

Alternatively, you can set up sxhkd as a systemd user service for automatic startup.

### Usage

1. Press and hold `Scroll Lock` to start recording
2. Speak your message while holding the key
3. Release `Scroll Lock` to stop recording and type the transcribed text

The text will be automatically typed at your current cursor position.

## Features

- **Multi-Backend Transcription**: Support for Deepgram and AssemblyAI APIs
- **Context-Aware LLM Processing**: Automatically formats text based on the focused application
- **System Tray Integration**: Visual status indicators during recording and transcription
- **Memory-Based Recording**: Prevents end-of-recording word loss with in-memory audio buffering
- **Professional Architecture**: Modular design with proper error handling and logging
- **Configurable Prompts**: Easy customization via YAML configuration file

## Requirements

### System Dependencies

- **Cross-platform** (Linux, macOS, Windows)
- **Python 3.12** or higher
- **PyAudio** for audio recording (included in dependencies)
- **xdotool** for text automation (Linux/X11 only)

### Install System Dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install xdotool
```

**macOS:**
```bash
# PyAudio included in dependencies, no additional system deps needed
# Note: Text typing functionality requires alternative to xdotool
```

**Windows:**
```bash
# PyAudio included in dependencies, no additional system deps needed
# Note: Text typing functionality requires alternative to xdotool
```

### API Keys (Optional)

- **Deepgram API key** (required for Deepgram backend)
- **AssemblyAI API key** (required for AssemblyAI backend)
- **Gemini API key** (optional, for LLM post-processing)

## Architecture

```
dictator/
├── app.py                  # Main application orchestrator
├── audio_recorder.py       # Cross-platform PyAudio recording with memory buffering
├── transcription/          # Transcription backend implementations
│   ├── deepgram.py        # Deepgram API integration
│   └── assemblyai.py      # AssemblyAI API integration
├── llm_processor.py       # LLM-based post-processing
├── prompt_manager.py      # Configurable prompt system
├── window_detector.py     # Application context detection
├── text_typer.py         # xdotool text automation
├── system_tray.py        # System tray status integration
└── process_manager.py    # Process lifecycle management

prompts.yaml              # LLM prompt configuration
```
