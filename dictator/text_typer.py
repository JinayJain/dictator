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
        logger.debug(f"Full text to type: {text}")

        try:
            result = subprocess.run(
                ["xdotool", "type", text, "--delay", "3"],
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
            if result.stdout:
                logger.debug(f"xdotool output: {result.stdout}")

        except subprocess.TimeoutExpired:
            logger.error("xdotool timed out")
        except FileNotFoundError:
            logger.error("xdotool not found. Please install xdotool.")
        except OSError as e:
            logger.error(f"Error running xdotool: {e}")
