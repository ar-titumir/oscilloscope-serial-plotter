"""Digital signal processing utilities for oscilloscope measurements."""

import numpy as np
from numpy.fft import rfft, rfftfreq


# Available FFT window functions
WINDOWS = {
    "Hanning": np.hanning,
    "Hamming": np.hamming,
    "Blackman": np.blackman,
    "Rectangular": lambda n: np.ones(n),
}


def compute_fft(
    data: np.ndarray,
    sample_rate: float,
    window: str = "Hanning",
) -> tuple[np.ndarray, np.ndarray]:
    """Return (frequencies_hz, magnitudes_dbv) arrays for the input signal."""
    n = len(data)
    if n < 4:
        return np.array([0.0]), np.array([-120.0])

    win_fn = WINDOWS.get(window, np.hanning)
    win = win_fn(n).astype(np.float32)
    windowed = data * win

    spectrum = rfft(windowed)
    freqs = rfftfreq(n, d=1.0 / sample_rate)

    magnitudes = np.abs(spectrum) * 2.0 / win.sum()
    magnitudes[0] /= 2.0  # DC bin correction

    with np.errstate(divide="ignore"):
        magnitudes_db = 20.0 * np.log10(
            np.maximum(magnitudes, 1e-12)
        )

    return freqs.astype(np.float32), magnitudes_db.astype(np.float32)


def compute_rms(data: np.ndarray) -> float:
    """Return the root-mean-square voltage of the signal."""
    if len(data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(data**2)))


def compute_vpp(data: np.ndarray) -> float:
    """Return peak-to-peak voltage (Vmax - Vmin)."""
    if len(data) == 0:
        return 0.0
    return float(np.max(data) - np.min(data))


def compute_frequency(data: np.ndarray, sample_rate: float) -> float:
    """Estimate signal frequency via rising zero-crossing detection.

    Each pair of consecutive rising crossings spans exactly one full period,
    so frequency = sample_rate / avg_period_samples (no /2 factor needed).
    Using only rising crossings avoids double-counting the half-period error.
    """
    if len(data) < 4:
        return 0.0
    mean = float(np.mean(data))
    shifted = data - mean
    # Rising crossings only: negative-to-positive transitions
    rising = np.where(np.diff(np.sign(shifted)) > 0)[0]
    if len(rising) < 2:
        return 0.0
    # Distance between consecutive rising crossings = one full period
    period_samples = np.diff(rising)
    avg_period_samples = float(np.mean(period_samples))
    if avg_period_samples == 0:
        return 0.0
    return sample_rate / avg_period_samples


def compute_duty_cycle(data: np.ndarray, threshold: float) -> float:
    """Return duty cycle (0-100 %) of a digital-like signal above threshold."""
    if len(data) == 0:
        return 0.0
    high = np.sum(data >= threshold)
    return float(high / len(data) * 100.0)


def compute_dvdt(data: np.ndarray, sample_rate: float) -> np.ndarray:
    """Return the first derivative of the signal (V/s)."""
    if len(data) < 2:
        return np.zeros_like(data)
    return np.gradient(data, 1.0 / sample_rate).astype(np.float32)
