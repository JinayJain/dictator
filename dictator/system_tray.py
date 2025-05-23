"""System tray manager for Dictator."""

import logging
import threading
from typing import Optional

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages system tray icon and states."""

    def __init__(self):
        self.icon: Optional[pystray.Icon] = None  # type: ignore
        self.tray_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the system tray icon."""
        if self._running:
            logger.warning("System tray already running")
            return

        logger.info("Starting system tray")

        # Create initial icon (idle state)
        icon_image = self._create_idle_icon()

        # Create tray icon with menu
        menu = pystray.Menu(
            pystray.MenuItem("Dictator", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Idle", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_callback),
        )

        self.icon = pystray.Icon(
            "dictator", icon_image, "Dictator - Voice Transcription", menu
        )

        # Run in separate thread
        self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self.tray_thread.start()
        self._running = True

        logger.info("System tray started")

    def stop(self) -> None:
        """Stop the system tray icon."""
        if not self._running:
            return

        logger.info("Stopping system tray")

        if self.icon:
            self.icon.stop()

        self._running = False
        logger.info("System tray stopped")

    def set_recording_state(self) -> None:
        """Update tray icon to show recording state."""
        if not self.icon:
            return

        icon_image = self._create_recording_icon()
        self.icon.icon = icon_image

        # Update menu
        menu = pystray.Menu(
            pystray.MenuItem("Dictator", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Recording...", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_callback),
        )
        self.icon.menu = menu

    def set_transcribing_state(self) -> None:
        """Update tray icon to show transcribing state."""
        if not self.icon:
            return

        icon_image = self._create_transcribing_icon()
        self.icon.icon = icon_image

        # Update menu
        menu = pystray.Menu(
            pystray.MenuItem("Dictator", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Transcribing...", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_callback),
        )
        self.icon.menu = menu

    def set_processing_state(self) -> None:
        """Update tray icon to show LLM processing/typing state."""
        if not self.icon:
            return

        icon_image = self._create_processing_icon()
        self.icon.icon = icon_image

        # Update menu
        menu = pystray.Menu(
            pystray.MenuItem("Dictator", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Processing & Typing...", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_callback),
        )
        self.icon.menu = menu

    def set_idle_state(self) -> None:
        """Update tray icon to show idle state."""
        if not self.icon:
            return

        icon_image = self._create_idle_icon()
        self.icon.icon = icon_image

        # Update menu
        menu = pystray.Menu(
            pystray.MenuItem("Dictator", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Idle", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_callback),
        )
        self.icon.menu = menu

    def _run_tray(self) -> None:
        """Run the tray icon (should be called in separate thread)."""
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Error running system tray: {e}")

    def _quit_callback(self, icon: pystray.Icon, item) -> None:
        """Handle quit menu item."""
        logger.info("Quit requested from system tray")
        self.stop()

    def _create_idle_icon(self) -> Image.Image:
        """Create icon for idle state (gray circle)."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw gray circle
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(128, 128, 128, 255),
            outline=(64, 64, 64, 255),
            width=2,
        )

        return image

    def _create_recording_icon(self) -> Image.Image:
        """Create icon for recording state (red circle)."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw red circle
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(220, 20, 20, 255),
            outline=(180, 0, 0, 255),
            width=2,
        )

        return image

    def _create_transcribing_icon(self) -> Image.Image:
        """Create icon for transcribing state (blue circle with pulse effect)."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw blue circle
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(20, 120, 220, 255),
            outline=(0, 80, 180, 255),
            width=2,
        )

        # Add inner circle for pulse effect
        inner_margin = 16
        draw.ellipse(
            [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
            fill=(100, 180, 255, 128),
        )

        return image

    def _create_processing_icon(self) -> Image.Image:
        """Create icon for LLM processing/typing state (green circle)."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw green circle
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(20, 200, 20, 255),
            outline=(0, 150, 0, 255),
            width=2,
        )

        return image
