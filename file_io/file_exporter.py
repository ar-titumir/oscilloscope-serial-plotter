"""File export utilities: CSV, screenshot, and WAV."""

import csv
import os
from typing import TYPE_CHECKING

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QScreen

if TYPE_CHECKING:
    pass


def save_csv(data: np.ndarray, sample_rate: float, path: str) -> None:
    """Write time-domain data to a CSV file with time (s) and voltage (V) columns."""
    dt = 1.0 / sample_rate if sample_rate > 0 else 1.0
    times = np.arange(len(data)) * dt
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time (s)", "Voltage (V)"])
        for t, v in zip(times, data):
            writer.writerow([f"{t:.8f}", f"{v:.6f}"])


def save_fft_csv(freqs: np.ndarray, mags: np.ndarray, path: str) -> None:
    """Write FFT data to a CSV file with frequency (Hz) and magnitude (dBV) columns."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Frequency (Hz)", "Magnitude (dBV)"])
        for freq, mag in zip(freqs, mags):
            writer.writerow([f"{freq:.4f}", f"{mag:.4f}"])


def save_screenshot(widget: QWidget, path: str) -> bool:
    """Grab and save a screenshot of the given widget to path. Returns True on success."""
    screen: QScreen | None = widget.screen()
    if screen is None:
        return False
    pixmap = screen.grabWindow(int(widget.winId()))
    return pixmap.save(path)


def save_wav(data: np.ndarray, sample_rate: float, path: str) -> None:
    """Save normalised float32 WAV file from voltage data using soundfile."""
    try:
        import soundfile as sf  # type: ignore
    except ImportError as exc:
        raise ImportError("soundfile is required for WAV export. Install it via pip.") from exc

    max_val = float(np.max(np.abs(data)))
    if max_val == 0:
        normalized = data.astype(np.float32)
    else:
        normalized = (data / max_val).astype(np.float32)

    sf.write(path, normalized, int(sample_rate), subtype="FLOAT")
