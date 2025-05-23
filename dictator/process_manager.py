"""Process management and lockfile operations."""

import logging
import os
from pathlib import Path
from typing import Optional

from .exceptions import RecordingError

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages process lifecycle and lockfile operations."""
    
    def __init__(self, lockfile_path: Path):
        self.lockfile_path = lockfile_path
    
    def is_running(self) -> bool:
        """Check if a process is currently running."""
        if not self.lockfile_path.exists():
            return False
        
        try:
            pid = self._read_pid()
            os.kill(pid, 0)  # Signal 0 checks if process exists
            return True
        except (ProcessLookupError, ValueError, OSError):
            self._cleanup_lockfile()
            return False
    
    def create_lockfile(self) -> None:
        """Create lockfile with current PID."""
        if self.is_running():
            raise RecordingError("Another recording process is already running")
        
        pid = os.getpid()
        try:
            with open(self.lockfile_path, "w") as f:
                f.write(str(pid))
            logger.info(f"Lockfile created with PID: {pid}")
        except OSError as e:
            raise RecordingError(f"Failed to create lockfile: {e}")
    
    def _read_pid(self) -> int:
        """Read PID from lockfile."""
        try:
            with open(self.lockfile_path, "r") as f:
                return int(f.read().strip())
        except (ValueError, OSError) as e:
            raise RecordingError(f"Invalid lockfile: {e}")
    
    def get_running_pid(self) -> Optional[int]:
        """Get PID of running process, if any."""
        if not self.is_running():
            return None
        return self._read_pid()
    
    def _cleanup_lockfile(self) -> None:
        """Remove lockfile if it exists."""
        try:
            if self.lockfile_path.exists():
                self.lockfile_path.unlink()
        except OSError as e:
            logger.error(f"Error removing lockfile: {e}")