"""Window detection utility for identifying focused applications."""

import logging
import subprocess
from typing import Optional

from .constants import XDOTOOL_TIMEOUT
from .exceptions import WindowDetectionError

logger = logging.getLogger(__name__)


class WindowDetector:
    """Utility class for detecting the currently focused application window."""

    def get_focused_window_info(self) -> dict[str, str]:
        """Get information about the currently focused window.

        Returns:
            Dictionary containing window information with keys:
            - 'class': Window class name
            - 'name': Window title/name
            - 'pid': Process ID of the window

        Raises:
            WindowDetectionError: If unable to detect window information
        """
        try:
            # Get the focused window ID
            window_id = self._get_focused_window_id()

            # Get window class
            window_class = self._get_window_property(window_id, "WM_CLASS")

            # Get window name/title
            window_name = self._get_window_property(window_id, "WM_NAME")

            # Get process ID
            window_pid = self._get_window_property(window_id, "_NET_WM_PID")

            logger.debug(
                f"Detected window - Class: {window_class}, Name: {window_name}, PID: {window_pid}"
            )

            return {
                "class": window_class or "",
                "name": window_name or "",
                "pid": window_pid or "",
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get window information: {e}")
            raise WindowDetectionError(f"Unable to detect focused window: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in window detection: {e}")
            raise WindowDetectionError(f"Window detection failed: {e}")

    def _get_focused_window_id(self) -> str:
        """Get the ID of the currently focused window."""
        result = subprocess.run(
            ["xdotool", "getwindowfocus"],
            capture_output=True,
            text=True,
            check=True,
            timeout=XDOTOOL_TIMEOUT,
        )
        return result.stdout.strip()

    def _get_window_property(self, window_id: str, property_name: str) -> Optional[str]:
        """Get a specific property of a window."""
        try:
            result = subprocess.run(
                ["xdotool", "getwindowname", window_id]
                if property_name == "WM_NAME"
                else ["xprop", "-id", window_id, property_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=XDOTOOL_TIMEOUT,
            )

            if property_name == "WM_NAME":
                return result.stdout.strip()
            else:
                # Parse xprop output
                output = result.stdout.strip()
                if "=" in output:
                    value = output.split("=", 1)[1].strip()
                    # Clean up quoted strings and extract first class name for WM_CLASS
                    if property_name == "WM_CLASS" and value:
                        # WM_CLASS returns something like '"Google-chrome", "Google-chrome"'
                        value = (
                            value.strip('"').split('"')[0] if '"' in value else value
                        )
                    elif property_name == "_NET_WM_PID":
                        # PID is just a number
                        value = value.strip()
                    return value

        except subprocess.CalledProcessError:
            # Property might not exist for this window
            pass
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout getting window property {property_name}")

        return None

    def is_chrome_focused(self) -> bool:
        """Check if Chrome (or Chromium-based browser) is the focused window.

        Returns:
            True if Chrome/Chromium is focused, False otherwise
        """
        try:
            window_info = self.get_focused_window_info()
            window_class = window_info.get("class", "").lower()
            window_name = window_info.get("name", "").lower()

            # Check for common Chrome/Chromium identifiers
            chrome_identifiers = [
                "google-chrome",
                "chromium",
                "chrome",
                "google chrome",
                "brave-browser",
                "microsoft-edge",
            ]

            for identifier in chrome_identifiers:
                if identifier in window_class or identifier in window_name:
                    logger.debug(f"Chrome-based browser detected: {window_class}")
                    return True

            return False

        except WindowDetectionError:
            logger.warning("Could not detect window information, assuming non-Chrome")
            return False
