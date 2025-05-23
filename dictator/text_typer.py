"""Text typing functionality using xdotool."""

import logging
import subprocess

from .constants import XDOTOOL_TIMEOUT

logger = logging.getLogger(__name__)


class TextTyper:
    """Handles typing text using xdotool."""

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
                text.encode('ascii')
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
                    logger.error(f"xdotool failed with return code: {result.returncode}")

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

    @staticmethod
    def type_text_chunk(text_chunk: str) -> None:
        """Type a chunk of text immediately using xdotool.
        
        This method types text chunks as they arrive for streaming scenarios.
        Uses minimal delay for real-time feel. Converts newlines to spaces to avoid
        unwanted enter keypresses.
        
        Args:
            text_chunk: The chunk of text to type immediately
        """
        if not text_chunk:
            return

        # Replace newlines with spaces to avoid hitting enter
        sanitized_chunk = text_chunk.replace('\n', ' ').replace('\r', ' ')
        
        # Remove trailing spaces and newlines only (preserve internal spacing)
        sanitized_chunk = sanitized_chunk.rstrip(' \n\r\t')
        
        # Skip if chunk becomes empty after sanitization
        if not sanitized_chunk:
            return

        try:
            # Check if chunk contains non-ASCII characters
            try:
                sanitized_chunk.encode('ascii')
                # ASCII text - use normal xdotool type
                result = subprocess.run(
                    ["xdotool", "type", "--delay", "1", "--", sanitized_chunk],
                    capture_output=True,
                    text=True,
                    timeout=XDOTOOL_TIMEOUT,
                )

                if result.returncode != 0:
                    logger.error(f"xdotool failed with return code: {result.returncode}")

                if result.stderr:
                    logger.error(f"xdotool error: {result.stderr}")

            except UnicodeEncodeError:
                # Contains Unicode - type each character using Unicode codes
                TextTyper._type_unicode_string(sanitized_chunk)

        except subprocess.TimeoutExpired:
            logger.error("xdotool timed out while typing chunk")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error running xdotool for chunk: {e}")

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
                        logger.error(f"xdotool failed to type Unicode character {char} (U+{ord(char):04X})")
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
