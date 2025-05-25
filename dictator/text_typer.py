"""Text typing functionality using pynput."""

import logging

import time

from pynput.keyboard import Controller, Key

logger = logging.getLogger(__name__)


class TextTyper:
    """Handles typing text using pynput."""

    def __init__(self):
        """Initialize TextTyper with buffering for trailing newlines."""
        self._buffered_newlines = 0
        self._controller = Controller()

    def type_text(self, text: str) -> None:
        """Type text using pynput with Unicode support."""
        if not text:
            logger.warning("No text to type")
            return

        preview = text[:50] + ("..." if len(text) > 50 else "")
        logger.info(f"Starting to type text: {preview}")

        try:
            self._controller.type(text)
            logger.info("Text typed successfully")

        except Exception as e:
            # Handle Unicode characters that pynput can't type
            logger.warning(f"pynput failed to type text directly: {e}")
            logger.info(
                "Attempting character-by-character typing with Unicode fallback"
            )
            self._type_with_unicode_fallback(text)

    def _type_with_unicode_fallback(self, text: str) -> None:
        """Type text character by character, skipping problematic Unicode characters."""
        for char in text:
            try:
                self._controller.type(char)
                time.sleep(0.003)  # 3ms delay between characters
            except Exception as char_error:
                logger.warning(
                    f"Skipping untypable character '{char}' (ord={ord(char)}): {char_error}"
                )
                # Continue with next character instead of failing

    def type_text_chunk(self, text_chunk: str) -> None:
        """Type a chunk of text immediately using pynput.

        This method types text chunks as they arrive for streaming scenarios.
        Uses minimal delay for real-time feel. Splits on newlines and types
        each part separately, using Enter key for actual newlines.

        Buffers trailing newlines and only outputs them when the next chunk arrives,
        preventing final trailing newlines from being typed.

        Args:
            text_chunk: The chunk of text to type immediately
        """
        if not text_chunk:
            return

        # First, output any buffered newlines from the previous chunk
        for _ in range(self._buffered_newlines):
            self._type_newline()
        self._buffered_newlines = 0

        # Count trailing newlines in this chunk
        trailing_newlines = len(text_chunk) - len(text_chunk.rstrip("\n"))

        # Remove trailing newlines for processing
        content_chunk = text_chunk.rstrip("\n")

        if content_chunk:
            # Split on newlines to handle each part separately
            lines = content_chunk.split("\n")

            for i, line in enumerate(lines):
                # Type the text part (skip empty lines)
                if line.strip():
                    self._type_text_part(line.rstrip())

                # Add newline if not the last line
                if i < len(lines) - 1:
                    self._type_newline()

        # Buffer the trailing newlines instead of typing them immediately
        self._buffered_newlines = trailing_newlines

    def flush_remaining_content(self) -> None:
        """Flush any remaining buffered content. Call this when streaming is complete."""
        # Don't output buffered newlines at the end - this is the whole point
        self._buffered_newlines = 0

    def _type_text_part(self, text: str) -> None:
        """Type a text part without newlines."""
        if not text:
            return

        try:
            self._controller.type(text)
            time.sleep(0.001)  # 1ms delay for streaming

        except Exception as e:
            logger.warning(f"pynput failed to type text part directly: {e}")
            # Fall back to character-by-character typing
            for char in text:
                try:
                    self._controller.type(char)
                    time.sleep(0.001)
                except Exception as char_error:
                    logger.warning(
                        f"Skipping untypable character '{char}' (ord={ord(char)}): {char_error}"
                    )

    def _type_newline(self) -> None:
        """Type a newline using Enter key."""
        try:
            self._controller.press(Key.enter)
            self._controller.release(Key.enter)

        except Exception as e:
            logger.error(f"Error typing newline with pynput: {e}")
