"""Frequency-domain FFT plot widget."""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class FftWidget(QWidget):
    """Displays the FFT spectrum with peak frequency annotation."""

    def __init__(self, settings, parent=None) -> None:
        """Initialize FFT plot with axes and peak label."""
        super().__init__(parent)
        self._settings = settings
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._layout.addWidget(self._plot_widget)

        self._setup_plot()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_plot(self) -> None:
        """Configure FFT plot appearance and peak annotation."""
        s = self._settings
        pw = self._plot_widget

        pw.setBackground(s.plot_bg_color)
        pw.showGrid(x=True, y=True, alpha=0.3)
        pw.setLabel("bottom", "Frequency", units="Hz")
        pw.setLabel("left", "Magnitude", units="dBV")
        pw.setTitle("FFT Spectrum", color=s.accent_color, size="11pt")
        pw.setYRange(-120, 10, padding=0)

        self._curve = pw.plot(
            pen=pg.mkPen(color=s.fft_color, width=1.5),
            fillLevel=-120,
            brush=pg.mkBrush(color=(*pg.colorTuple(pg.mkColor(s.fft_color))[:3], 40)),
        )

        self._peak_label = pg.TextItem(
            text="",
            color=s.accent_color,
            anchor=(0.5, 1.0),
        )
        pw.addItem(self._peak_label)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_fft(self, freqs: np.ndarray, magnitudes: np.ndarray) -> None:
        """Refresh FFT display with new frequency and magnitude arrays."""
        if len(freqs) == 0:
            return

        self._curve.setData(freqs, magnitudes)

        if self._settings.fft_log_scale:
            self._plot_widget.setLogMode(x=True, y=False)
        else:
            self._plot_widget.setLogMode(x=False, y=False)

        # Annotate peak frequency (skip DC)
        if len(magnitudes) > 1:
            start = 1 if freqs[0] == 0 else 0
            peak_idx = int(np.argmax(magnitudes[start:])) + start
            peak_freq = float(freqs[peak_idx])
            peak_mag = float(magnitudes[peak_idx])
            self._peak_label.setPos(peak_freq, peak_mag + 3)
            self._peak_label.setText(f"{peak_freq:.1f} Hz")
        else:
            self._peak_label.setText("")

    def apply_settings(self) -> None:
        """Re-apply colors and scale mode from the settings object."""
        s = self._settings
        self._plot_widget.setBackground(s.plot_bg_color)
        self._curve.setPen(pg.mkPen(color=s.fft_color, width=1.5))
        self._peak_label.setColor(s.accent_color)
