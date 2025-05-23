# Dictator

A command-line tool for transcribing speech to text using the Deepgram API.

## Setup

1. Install dependencies:
   ```bash
   uv add -r requirements.txt
   ```

2. Create a `.env` file in the project root with your Deepgram API key:
   ```
   DEEPGRAM_API_KEY=your_api_key_here
   ```
   
   You can use the provided `.env.example` file as a template:
   ```bash
   cp .env.example .env
   # Then edit .env with your actual API key
   ```

   You can get an API key by signing up at [Deepgram's website](https://deepgram.com).

## Usage

1. Start dictation:
   ```bash
   python main.py begin
   ```

2. End dictation and type the transcribed text:
   ```bash
   python main.py end
   ```

## Requirements

- Python 3.12 or higher
- A Deepgram API key
- xdotool (for Linux)