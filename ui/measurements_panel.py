"""Horizontal measurements bar showing real-time signal parameters."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)


class MeasurementItem(QWidget):
    """A single name + value label pair for one measurement."""

    def __init__(self, name: str, unit: str, parent=None) -> None:
        """Initialize with measurement name and unit."""
        super().__init__(parent)
        self._unit = unit
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self._name_lbl = QLabel(name + ":")
        self._name_lbl.setObjectName("measName")
        self._val_lbl = QLabel("—")
        self._val_lbl.setObjectName("measValue")
        self._val_lbl.setMinimumWidth(70)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._name_lbl)
        layout.addWidget(self._val_lbl)

    def set_value(self, value: float | None, fmt: str = ".4f") -> None:
        """Update the displayed value; use None to show '—'."""
        if value is None:
            self._val_lbl.setText("—")
        else:
            self._val_lbl.setText(f"{value:{fmt}} {self._unit}")


class MeasurementsPanel(QWidget):
    """Horizontal bar of live signal measurement readouts."""

    def __init__(self, parent=None) -> None:
        """Initialize all measurement label pairs."""
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        specs = [
            ("Freq",    "Hz",   ".2f"),
            ("Period",  "ms",   ".4f"),
            ("Vpp",     "V",    ".4f"),
            ("Vmax",    "V",    ".4f"),
            ("Vmin",    "V",    ".4f"),
            ("Vrms",    "V",    ".4f"),
            ("Duty",    "%",    ".1f"),
            ("dV/dt",   "V/s",  ".2f"),
        ]

        self._items: dict[str, tuple[MeasurementItem, str]] = {}

        for name, unit, fmt in specs:
            item = MeasurementItem(name, unit)
            self._items[name] = (item, fmt)
            layout.addWidget(item)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setObjectName("measSep")
            layout.addWidget(sep)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_measurements(
        self,
        freq: float,
        vpp: float,
        vmax: float,
        vmin: float,
        vrms: float,
        duty: float,
        dvdt_rms: float = 0.0,
    ) -> None:
        """Refresh all measurement labels with new computed values."""
        period_ms = (1.0 / freq * 1000.0) if freq > 0 else 0.0

        updates = {
            "Freq":   freq,
            "Period": period_ms,
            "Vpp":    vpp,
            "Vmax":   vmax,
            "Vmin":   vmin,
            "Vrms":   vrms,
            "Duty":   duty,
            "dV/dt":  dvdt_rms,
        }

        for name, value in updates.items():
            item, fmt = self._items[name]
            item.set_value(value, fmt)

    def clear(self) -> None:
        """Reset all values to '—'."""
        for item, _ in self._items.values():
            item.set_value(None)
