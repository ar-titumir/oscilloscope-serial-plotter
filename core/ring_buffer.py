"""Thread-safe circular buffer backed by collections.deque."""

import threading
from collections import deque
import numpy as np


class RingBuffer:
    """Thread-safe circular buffer with fixed maximum length."""

    def __init__(self, maxlen: int = 1024) -> None:
        """Initialize buffer with given capacity."""
        self._buf: deque[float] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def resize(self, maxlen: int) -> None:
        """Resize the buffer, discarding oldest samples if needed."""
        with self._lock:
            data = list(self._buf)
            self._buf = deque(data[-maxlen:], maxlen=maxlen)

    def append(self, chunk: np.ndarray) -> None:
        """Append a numpy array chunk of samples to the buffer."""
        with self._lock:
            self._buf.extend(chunk.tolist())

    def get_data(self) -> np.ndarray:
        """Return a numpy array copy of the current buffer contents."""
        with self._lock:
            return np.array(self._buf, dtype=np.float32)

    def clear(self) -> None:
        """Clear all samples from the buffer."""
        with self._lock:
            self._buf.clear()

    def __len__(self) -> int:
        """Return current number of samples in buffer."""
        with self._lock:
            return len(self._buf)
