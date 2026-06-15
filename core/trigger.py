"""Trigger detection for oscilloscope waveform alignment."""

import numpy as np


def find_trigger_index(
    data: np.ndarray,
    level: float,
    edge: str = "rising",
    hysteresis: float = 0.05,
) -> int:
    """Return the sample index of the first trigger event, or 0 if not found.

    Args:
        data: Voltage array.
        level: Trigger voltage level.
        edge: 'rising' or 'falling'.
        hysteresis: Dead-band around trigger level to prevent re-triggering.
    """
    if len(data) < 2:
        return 0

    if edge == "rising":
        lo = level - hysteresis
        hi = level + hysteresis
        below = data[:-1] < lo
        above = data[1:] > hi
    else:  # falling
        lo = level - hysteresis
        hi = level + hysteresis
        above = data[:-1] > hi
        below = data[1:] < lo

    indices = np.where(below & above)[0] if edge == "rising" else np.where(above & below)[0]

    if len(indices) == 0:
        return 0
    return int(indices[0]) + 1
