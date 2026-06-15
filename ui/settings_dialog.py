"""Settings dialog for theme and global application preferences."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ColorButton(QPushButton):
    """A button that shows and picks a color."""

    color_changed = pyqtSignal(str)  # hex color string

    def __init__(self, color: str, parent=None) -> None:
        """Initialize with initial hex color string."""
        super().__init__(parent)
        self._color = color
        self._update_swatch()
        self.setFixedWidth(60)
        self.clicked.connect(self._pick_color)

    def get_color(self) -> str:
        """Return current hex color string."""
        return self._color

    def set_color(self, color: str) -> None:
        """Set the current color and update the button swatch."""
        self._color = color
        self._update_swatch()

    def _update_swatch(self) -> None:
        """Repaint button background to the current color."""
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._color}; border: 1px solid #555; border-radius: 3px; }}"
        )

    def _pick_color(self) -> None:
        """Open the color picker dialog."""
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_swatch()
            self.color_changed.emit(self._color)


class SettingsDialog(QDialog):
    """Modal settings dialog; emits settings_applied when saved."""

    settings_applied = pyqtSignal()

    def __init__(self, settings, parent=None) -> None:
        """Initialize dialog tabs and controls from settings."""
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_theme_tab(), "Theme & Colors")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_theme_tab(self) -> QWidget:
        """Build the color/theme customization tab."""
        w = QWidget()
        layout = QVBoxLayout(w)

        grp = QGroupBox("Colors")
        form = QFormLayout(grp)

        self._color_btns: dict[str, ColorButton] = {}

        color_fields = [
            ("bg_color",        "Background"),
            ("panel_color",     "Panel"),
            ("accent_color",    "Accent"),
            ("plot_bg_color",   "Plot Background"),
            ("waveform_color",  "Waveform"),
            ("fft_color",       "FFT Curve"),
        ]

        for field, label in color_fields:
            btn = ColorButton(getattr(self._settings, field))
            self._color_btns[field] = btn
            row = QHBoxLayout()
            row.addWidget(btn)
            swatch_lbl = QLabel(getattr(self._settings, field))
            swatch_lbl.setObjectName("hexLabel")
            btn.color_changed.connect(lambda c, lbl=swatch_lbl: lbl.setText(c))
            row.addWidget(swatch_lbl)
            row.addStretch()
            form.addRow(label + ":", row)

        layout.addWidget(grp)
        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_accept(self) -> None:
        """Apply and persist settings from dialog controls."""
        for field, btn in self._color_btns.items():
            setattr(self._settings, field, btn.get_color())

        self._settings.save()
        self.settings_applied.emit()
        self.accept()
