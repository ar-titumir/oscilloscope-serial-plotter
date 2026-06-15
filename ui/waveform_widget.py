"""Scrolling time-domain waveform plot widget."""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from core.dsp import compute_dvdt


class WaveformWidget(QWidget):
    """Displays a scrolling time-domain voltage waveform with trigger line."""

    trigger_level_changed = pyqtSignal(float)

    def __init__(self, settings, parent=None) -> None:
        """Initialize the waveform plot with trigger line and grid."""
        super().__init__(parent)
        self._settings = settings
        self._dvdt_mode = False
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._layout.addWidget(self._plot_widget)

        self._setup_plot()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_plot(self) -> None:
        """Configure plot appearance, axes, and trigger line."""
        s = self._settings
        pw = self._plot_widget

        pw.setBackground(s.plot_bg_color)
        pw.showGrid(x=True, y=True, alpha=0.3)
        pw.setLabel("bottom", "Time", units="ms")
        pw.setLabel("left", "Voltage", units="V")
        pw.setTitle("Waveform", color=s.accent_color, size="11pt")

        self._curve = pw.plot(pen=pg.mkPen(color=s.waveform_color, width=1.5))
        self._dvdt_curve = pw.plot(
            pen=pg.mkPen(color="#ffaa00", width=1.2, style=pg.QtCore.Qt.PenStyle.DashLine)
        )
        self._dvdt_curve.setVisible(False)

        # Trigger level line (draggable)
        self._trigger_line = pg.InfiniteLine(
            angle=0,
            movable=True,
            pos=s.trigger_level,
            pen=pg.mkPen(color="#ff4444", width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
            label="Trig: {value:.2f}V",
            labelOpts={"color": "#ff4444", "position": 0.92},
        )
        pw.addItem(self._trigger_line)
        self._trigger_line.sigPositionChangeFinished.connect(self._on_trigger_moved)

        self._apply_y_range()

    def _apply_y_range(self) -> None:
        """Apply current Y-axis range from settings."""
        s = self._settings
        self._plot_widget.setYRange(s.y_min, s.y_max, padding=0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_plot(
        self,
        data: np.ndarray,
        sample_rate: float,
        trigger_index: int = 0,
    ) -> None:
        """Refresh the waveform display with new data starting at trigger_index."""
        if len(data) == 0:
            return

        triggered = data[trigger_index:] if trigger_index < len(data) else data
        n = len(triggered)
        if n == 0:
            return

        dt_ms = 1000.0 / sample_rate if sample_rate > 0 else 1.0
        t_ms = np.arange(n) * dt_ms

        self._curve.setData(t_ms, triggered)

        if self._dvdt_mode and self._settings.dvdt_enabled:
            dvdt = compute_dvdt(triggered, sample_rate)
            self._dvdt_curve.setData(t_ms, dvdt)
            self._dvdt_curve.setVisible(True)
        else:
            self._dvdt_curve.setVisible(False)

        # Apply time/div windowing
        time_div_ms = self._settings.time_per_div_ms
        num_divs = 10
        self._plot_widget.setXRange(0, time_div_ms * num_divs, padding=0)

    def set_trigger_level(self, level: float) -> None:
        """Move the trigger line to the specified voltage level."""
        self._trigger_line.setValue(level)

    def set_y_range(self, y_min: float, y_max: float) -> None:
        """Set the vertical display range."""
        self._plot_widget.setYRange(y_min, y_max, padding=0)

    def set_dvdt_overlay(self, enabled: bool) -> None:
        """Toggle dv/dt overlay curve visibility."""
        self._dvdt_mode = enabled
        if not enabled:
            self._dvdt_curve.setVisible(False)

    def apply_settings(self) -> None:
        """Re-apply all visual settings (colors, ranges) from the settings object."""
        s = self._settings
        self._plot_widget.setBackground(s.plot_bg_color)
        self._curve.setPen(pg.mkPen(color=s.waveform_color, width=1.5))
        self._trigger_line.setPen(
            pg.mkPen(color="#ff4444", width=1, style=pg.QtCore.Qt.PenStyle.DashLine)
        )
        self._apply_y_range()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_trigger_moved(self) -> None:
        """Emit signal when user drags the trigger line."""
        level = float(self._trigger_line.value())
        self._settings.trigger_level = level
        self.trigger_level_changed.emit(level)
