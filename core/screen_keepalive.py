"""Cross-platform utility to prevent display sleep while the scope is running."""

import ctypes
import sys


class ScreenKeepAlive:
    """Prevents the OS display from sleeping/locking while enabled."""

    # Windows SetThreadExecutionState flags
    _ES_CONTINUOUS = 0x80000000
    _ES_SYSTEM_REQUIRED = 0x00000001
    _ES_DISPLAY_REQUIRED = 0x00000002

    def __init__(self) -> None:
        """Initialize platform detection and active state."""
        self._active = False
        self._platform = sys.platform

    def enable(self) -> None:
        """Request the display stay awake. Safe to call repeatedly."""
        if self._active:
            return

        if self._platform.startswith("win"):
            ctypes.windll.kernel32.SetThreadExecutionState(
                self._ES_CONTINUOUS
                | self._ES_SYSTEM_REQUIRED
                | self._ES_DISPLAY_REQUIRED
            )

        self._active = True

    def disable(self) -> None:
        """Release the display-awake request, allowing normal sleep again."""
        if not self._active:
            return

        if self._platform.startswith("win"):
            ctypes.windll.kernel32.SetThreadExecutionState(self._ES_CONTINUOUS)

        self._active = False

    @property
    def is_active(self) -> bool:
        """Return True if a keep-awake request is currently active."""
        return self._active
