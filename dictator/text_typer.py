"""Text typing functionality using PyAutoGUI."""

import logging

import pyautogui

logger = logging.getLogger(__name__)


class TextTyper:
    """Handles typing text using PyAutoGUI."""

    def __init__(self):
        """Initialize TextTyper with buffering for trailing newlines."""
        self._buffered_newlines = 0
        # Configure PyAutoGUI for cross-platform compatibility
        pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
        pyautogui.PAUSE = 0  # No automatic pause between PyAutoGUI calls

    @staticmethod
    def type_text(text: str) -> None:
        """Type text using PyAutoGUI."""
        if not text:
            logger.warning("No text to type")
            return

        preview = text[:50] + ("..." if len(text) > 50 else "")
        logger.info(f"Starting to type text: {preview}")

        try:
            # PyAutoGUI handles Unicode natively, no need for special handling
            pyautogui.typewrite(text, interval=0.003)  # 3ms delay between keystrokes
            logger.info("Text typed successfully")

        except pyautogui.FailSafeException:
            logger.error("PyAutoGUI fail-safe triggered (mouse moved to corner)")
        except Exception as e:
            logger.error(f"Error typing text with PyAutoGUI: {e}")

    def type_text_chunk(self, text_chunk: str) -> None:
        """Type a chunk of text immediately using PyAutoGUI.

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
            # PyAutoGUI handles all text types natively
            pyautogui.typewrite(text, interval=0.001)  # 1ms delay for streaming

        except pyautogui.FailSafeException:
            logger.error("PyAutoGUI fail-safe triggered while typing text part")
        except Exception as e:
            logger.error(f"Error typing text part with PyAutoGUI: {e}")

    @staticmethod
    def _type_newline() -> None:
        """Type a newline using Enter key."""
        try:
            pyautogui.press("enter")

        except pyautogui.FailSafeException:
            logger.error("PyAutoGUI fail-safe triggered while typing newline")
        except Exception as e:
            logger.error(f"Error typing newline with PyAutoGUI: {e}")
