#!/usr/bin/env python3
"""
Dictator CLI entry point.

A CLI tool that records audio using PulseAudio, transcribes it using Deepgram,
and types the result using xdotool.
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from dictator import DictatorApp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point."""
    logger.info("Dictator CLI starting")

    parser = argparse.ArgumentParser(
        description="Dictator: Voice recording and transcription tool"
    )
    parser.add_argument(
        "command",
        choices=["begin", "end"],
        help="Command to execute: 'begin' to start recording, 'end' to stop",
    )
    parser.add_argument(
        "--backend",
        choices=["deepgram", "assemblyai"],
        default="deepgram",
        help="Transcription backend to use (default: deepgram)",
    )

    args = parser.parse_args()
    logger.info(f"Executing command: {args.command} with backend: {args.backend}")

    app = DictatorApp(backend=args.backend)

    try:
        if args.command == "begin":
            app.begin_recording()
        elif args.command == "end":
            app.end_recording()
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

    logger.info("Dictator CLI finished")


if __name__ == "__main__":
    main()
