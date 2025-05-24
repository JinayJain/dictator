"""Cross-platform window detection utility for identifying focused applications."""

import logging
import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

from .constants import XDOTOOL_TIMEOUT
from .exceptions import WindowDetectionError

logger = logging.getLogger(__name__)


class WindowDetectionBackend(ABC):
    """Abstract base class for platform-specific window detection."""

    @abstractmethod
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
        pass


class LinuxWindowDetector(WindowDetectionBackend):
    """Linux window detection using xdotool and xprop."""

    def get_focused_window_info(self) -> dict[str, str]:
        """Get information about the currently focused window on Linux."""
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


class MacOSWindowDetector(WindowDetectionBackend):
    """macOS window detection using AppleScript."""

    def get_focused_window_info(self) -> dict[str, str]:
        """Get information about the currently focused window on macOS."""
        try:
            # Get the frontmost application name
            app_name = self._get_frontmost_app_name()

            # Get the frontmost window title
            window_title = self._get_frontmost_window_title()

            # Get process ID (simplified - just use app name as identifier)
            pid = self._get_frontmost_app_pid()

            logger.debug(
                f"Detected window - App: {app_name}, Title: {window_title}, PID: {pid}"
            )

            return {
                "class": app_name or "",
                "name": window_title or "",
                "pid": str(pid) if pid else "",
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get window information: {e}")
            raise WindowDetectionError(f"Unable to detect focused window: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in window detection: {e}")
            raise WindowDetectionError(f"Window detection failed: {e}")

    def _get_frontmost_app_name(self) -> Optional[str]:
        """Get the name of the frontmost application."""
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get name of first application process whose frontmost is true',
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=XDOTOOL_TIMEOUT,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    def _get_frontmost_window_title(self) -> Optional[str]:
        """Get the title of the frontmost window."""
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get title of front window of first application process whose frontmost is true',
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=XDOTOOL_TIMEOUT,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    def _get_frontmost_app_pid(self) -> Optional[int]:
        """Get the PID of the frontmost application."""
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get unix id of first application process whose frontmost is true',
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=XDOTOOL_TIMEOUT,
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            return None


class WindowsWindowDetector(WindowDetectionBackend):
    """Windows window detection using Win32 API."""

    def __init__(self):
        """Initialize Windows window detector."""
        try:
            import win32gui
            import win32process

            self._win32gui = win32gui
            self._win32process = win32process
        except ImportError:
            logger.warning("pywin32 not available, falling back to PowerShell")
            self._win32gui = None
            self._win32process = None

    def get_focused_window_info(self) -> dict[str, str]:
        """Get information about the currently focused window on Windows."""
        if self._win32gui and self._win32process:
            return self._get_window_info_win32()
        else:
            return self._get_window_info_powershell()

    def _get_window_info_win32(self) -> dict[str, str]:
        """Get window info using Win32 API."""
        try:
            # Get the foreground window handle
            hwnd = self._win32gui.GetForegroundWindow()

            # Get window title
            window_title = self._win32gui.GetWindowText(hwnd)

            # Get window class name
            window_class = self._win32gui.GetClassName(hwnd)

            # Get process ID
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)

            logger.debug(
                f"Detected window - Class: {window_class}, Title: {window_title}, PID: {pid}"
            )

            return {
                "class": window_class or "",
                "name": window_title or "",
                "pid": str(pid) if pid else "",
            }

        except Exception as e:
            logger.error(f"Failed to get window information via Win32: {e}")
            raise WindowDetectionError(f"Unable to detect focused window: {e}")

    def _get_window_info_powershell(self) -> dict[str, str]:
        """Get window info using PowerShell as fallback."""
        try:
            # PowerShell script to get active window info
            ps_script = """
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                using System.Text;
                public class Win32 {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                    [DllImport("user32.dll")]
                    public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
                    [DllImport("user32.dll")]
                    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
                }
"@
            $hwnd = [Win32]::GetForegroundWindow()
            $title = New-Object System.Text.StringBuilder 256
            $class = New-Object System.Text.StringBuilder 256
            [Win32]::GetWindowText($hwnd, $title, 256)
            [Win32]::GetClassName($hwnd, $class, 256)
            $pid = 0
            [Win32]::GetWindowThreadProcessId($hwnd, [ref]$pid)
            Write-Output "$($class.ToString())|$($title.ToString())|$pid"
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=True,
                timeout=XDOTOOL_TIMEOUT * 2,  # PowerShell might be slower
            )

            output = result.stdout.strip()
            if "|" in output:
                parts = output.split("|", 2)
                window_class = parts[0] if len(parts) > 0 else ""
                window_title = parts[1] if len(parts) > 1 else ""
                window_pid = parts[2] if len(parts) > 2 else ""

                logger.debug(
                    f"Detected window - Class: {window_class}, Title: {window_title}, PID: {window_pid}"
                )

                return {
                    "class": window_class,
                    "name": window_title,
                    "pid": window_pid,
                }

            raise WindowDetectionError("Invalid PowerShell output format")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get window information via PowerShell: {e}")
            raise WindowDetectionError(f"Unable to detect focused window: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in PowerShell window detection: {e}")
            raise WindowDetectionError(f"Window detection failed: {e}")


class WindowDetector:
    """Cross-platform window detector that chooses the appropriate backend."""

    def __init__(self):
        """Initialize the appropriate window detection backend for the current platform."""
        system = platform.system().lower()

        if system == "linux":
            self._backend = LinuxWindowDetector()
        elif system == "darwin":  # macOS
            self._backend = MacOSWindowDetector()
        elif system == "windows":
            self._backend = WindowsWindowDetector()
        else:
            logger.warning(f"Unsupported platform: {system}")
            self._backend = None

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
        if self._backend is None:
            logger.warning("Window detection not supported on this platform")
            return {"class": "", "name": "", "pid": ""}

        try:
            return self._backend.get_focused_window_info()
        except WindowDetectionError:
            # Re-raise WindowDetectionError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in window detection: {e}")
            raise WindowDetectionError(f"Window detection failed: {e}")

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
                "edge",
                "brave",
            ]

            for identifier in chrome_identifiers:
                if identifier in window_class or identifier in window_name:
                    logger.debug(f"Chrome-based browser detected: {window_class}")
                    return True

            return False

        except WindowDetectionError:
            logger.warning("Could not detect window information, assuming non-Chrome")
            return False
