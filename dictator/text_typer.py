"""Text typing functionality using xdotool."""

import logging
import subprocess

from .constants import XDOTOOL_TIMEOUT

logger = logging.getLogger(__name__)


class TextTyper:
    """Handles typing text using xdotool."""

    def __init__(self):
        """Initialize TextTyper with buffering for trailing newlines."""
        self._buffered_newlines = 0

    @staticmethod
    def type_text(text: str) -> None:
        """Type text using xdotool."""
        if not text:
            logger.warning("No text to type")
            return

        preview = text[:50] + ("..." if len(text) > 50 else "")
        logger.info(f"Starting to type text: {preview}")

        try:
            # Check if text contains non-ASCII characters
            try:
                text.encode("ascii")
                # ASCII text - use normal xdotool type
                result = subprocess.run(
                    ["xdotool", "type", "--delay", "3", "--", text],
                    capture_output=True,
                    text=True,
                    timeout=XDOTOOL_TIMEOUT,
                )

                if result.returncode == 0:
                    logger.info("Text typed successfully")
                else:
                    logger.error(
                        f"xdotool failed with return code: {result.returncode}"
                    )

                if result.stderr:
                    logger.error(f"xdotool error: {result.stderr}")

            except UnicodeEncodeError:
                # Contains Unicode - type each character using Unicode codes
                TextTyper._type_unicode_string(text)
                logger.info("Text typed successfully via Unicode codes")

        except subprocess.TimeoutExpired:
            logger.error("xdotool timed out")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error running xdotool: {e}")

    def type_text_chunk(self, text_chunk: str) -> None:
        """Type a chunk of text immediately using xdotool.

        This method types text chunks as they arrive for streaming scenarios.
        Uses minimal delay for real-time feel. Splits on newlines and types
        each part separately, using Return key for actual newlines.

        Buffers trailing newlines and only outputs them when the next chunk arrives,
        preventing final trailing newlines from being typed.

        Args:
            text_chunk: The chunk of text to type immediately
        """
        if not text_chunk:
            return

        # First, output any buffered newlines from the previous chunk
        for _ in range(self._buffered_newlines):
            TextTyper._type_newline()
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
                    TextTyper._type_text_part(line.rstrip())

                # Add newline if not the last line
                if i < len(lines) - 1:
                    TextTyper._type_newline()

        # Buffer the trailing newlines instead of typing them immediately
        self._buffered_newlines = trailing_newlines

    def flush_remaining_content(self) -> None:
        """Flush any remaining buffered content. Call this when streaming is complete."""
        # Don't output buffered newlines at the end - this is the whole point
        self._buffered_newlines = 0

    @staticmethod
    def _type_text_part(text: str) -> None:
        """Type a text part without newlines."""
        if not text:
            return

        try:
            # Check if text contains non-ASCII characters
            try:
                text.encode("ascii")
                # ASCII text - use normal xdotool type
                result = subprocess.run(
                    ["xdotool", "type", "--delay", "1", "--", text],
                    capture_output=True,
                    text=True,
                    timeout=XDOTOOL_TIMEOUT,
                )

                if result.returncode != 0:
                    logger.error(
                        f"xdotool failed with return code: {result.returncode}"
                    )

                if result.stderr:
                    logger.error(f"xdotool error: {result.stderr}")

            except UnicodeEncodeError:
                # Contains Unicode - type each character using Unicode codes
                TextTyper._type_unicode_string(text)

        except subprocess.TimeoutExpired:
            logger.error("xdotool timed out while typing text part")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error running xdotool for text part: {e}")

    @staticmethod
    def _type_newline() -> None:
        """Type a newline using Return key."""
        try:
            result = subprocess.run(
                ["xdotool", "key", "Return"],
                capture_output=True,
                text=True,
                timeout=XDOTOOL_TIMEOUT,
            )

            if result.returncode != 0:
                logger.error(f"xdotool failed to type newline: {result.returncode}")

            if result.stderr:
                logger.error(f"xdotool newline error: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("xdotool timed out while typing newline")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error running xdotool for newline: {e}")

    @staticmethod
    def _type_unicode_string(text: str) -> None:
        """Type text containing Unicode characters using xdotool key codes.

        Args:
            text: Text containing Unicode characters to type
        """
        try:
            for char in text:
                if ord(char) > 127:  # Non-ASCII character
                    # Use Unicode code point with xdotool key
                    unicode_code = f"U{ord(char):04x}"
                    result = subprocess.run(
                        ["xdotool", "key", unicode_code],
                        capture_output=True,
                        text=True,
                        timeout=XDOTOOL_TIMEOUT,
                    )

                    if result.returncode != 0:
                        logger.error(
                            f"xdotool failed to type Unicode character {char} (U+{ord(char):04X})"
                        )
                else:
                    # ASCII character - use regular type
                    result = subprocess.run(
                        ["xdotool", "type", "--delay", "1", "--", char],
                        capture_output=True,
                        text=True,
                        timeout=XDOTOOL_TIMEOUT,
                    )

                    if result.returncode != 0:
                        logger.error(f"xdotool failed to type ASCII character {char}")

        except subprocess.TimeoutExpired:
            logger.error("Unicode typing operation timed out")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error in Unicode typing operation: {e}")
