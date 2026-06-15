"""Left-side controls panel with grouped settings."""

import serial.tools.list_ports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.dsp import WINDOWS


class ControlsPanel(QScrollArea):
    """Collapsible scrollable left-side controls panel."""

    # Signals
    connect_requested = pyqtSignal(str, int)   # port, baud
    disconnect_requested = pyqtSignal()
    settings_changed = pyqtSignal()            # generic re-apply
    mapping_changed = pyqtSignal()

    def __init__(self, settings, parent=None) -> None:
        """Initialize all control groups from settings."""
        super().__init__(parent)
        self._settings = settings
        self._connected = False

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(220)
        self.setMaximumWidth(260)

        container = QWidget()
        self._main_layout = QVBoxLayout(container)
        self._main_layout.setSpacing(6)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        self.setWidget(container)

        self._build_connection_group()
        self._build_mapping_group()
        self._build_timebase_group()
        self._build_yrange_group()
        self._build_trigger_group()
        self._build_dsp_group()
        self._main_layout.addStretch()

    # ------------------------------------------------------------------
    # Group builders
    # ------------------------------------------------------------------

    def _build_connection_group(self) -> None:
        """Build the serial connection controls group."""
        grp = QGroupBox("Connection")
        layout = QGridLayout(grp)

        layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(110)
        layout.addWidget(self.port_combo, 0, 1)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedWidth(28)
        refresh_btn.setToolTip("Refresh port list")
        refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh_btn, 0, 2)

        layout.addWidget(QLabel("Baud:"), 1, 0)
        self.baud_combo = QComboBox()
        for b in ["9600", "115200", "250000"]:
            self.baud_combo.addItem(b)
        self.baud_combo.setCurrentText(str(self._settings.baud_rate))
        layout.addWidget(self.baud_combo, 1, 1, 1, 2)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn, 2, 0, 1, 3)

        self._main_layout.addWidget(grp)
        self.refresh_ports()

    def _build_mapping_group(self) -> None:
        """Build the ADC → voltage mapping controls group."""
        grp = QGroupBox("Signal Mapping")
        layout = QVBoxLayout(grp)

        # Enable toggle with tick mark style
        top = QHBoxLayout()
        self.map_checkbox = QCheckBox("Enable Mapping")
        self.map_checkbox.setChecked(self._settings.mapping_enabled)
        self.map_checkbox.setObjectName("mapToggle")
        self.map_checkbox.stateChanged.connect(self._on_mapping_toggled)
        top.addWidget(self.map_checkbox)
        layout.addLayout(top)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sepLine")
        layout.addWidget(sep)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        grid.addWidget(QLabel("ADC:"), 0, 0)
        self.adc_min_spin = self._make_dspin(0, 9999, self._settings.adc_min, 0)
        self.adc_max_spin = self._make_dspin(0, 9999, self._settings.adc_max, 0)
        grid.addWidget(self.adc_min_spin, 0, 1)
        grid.addWidget(QLabel("→"), 0, 2)
        grid.addWidget(self.adc_max_spin, 0, 3)

        grid.addWidget(QLabel("Volt:"), 1, 0)
        self.volt_min_spin = self._make_dspin(-50, 50, self._settings.volt_min, 2)
        self.volt_max_spin = self._make_dspin(-50, 50, self._settings.volt_max, 2)
        grid.addWidget(self.volt_min_spin, 1, 1)
        grid.addWidget(QLabel("→"), 1, 2)
        grid.addWidget(self.volt_max_spin, 1, 3)

        layout.addLayout(grid)

        vref_row = QHBoxLayout()
        vref_row.addWidget(QLabel("Vref (V):"))
        self.vref_spin = self._make_dspin(0.1, 50, self._settings.vref, 2)
        vref_row.addWidget(self.vref_spin)
        layout.addLayout(vref_row)

        apply_btn = QPushButton("Apply Mapping")
        apply_btn.clicked.connect(self._on_mapping_apply)
        layout.addWidget(apply_btn)

        self._main_layout.addWidget(grp)
        self._mapping_grp = grp

    def _build_timebase_group(self) -> None:
        """Build the time base and buffer size controls group."""
        grp = QGroupBox("Timebase")
        layout = QGridLayout(grp)

        layout.addWidget(QLabel("Time/div (ms):"), 0, 0)
        self.time_div_spin = self._make_dspin(0.1, 5000, self._settings.time_per_div_ms, 2)
        self.time_div_spin.valueChanged.connect(self._on_time_div_changed)
        layout.addWidget(self.time_div_spin, 0, 1)

        layout.addWidget(QLabel("Buffer size:"), 1, 0)
        self.buffer_combo = QComboBox()
        for s in ["512", "1024", "2048", "4096"]:
            self.buffer_combo.addItem(s)
        self.buffer_combo.setCurrentText(str(self._settings.buffer_size))
        self.buffer_combo.currentTextChanged.connect(self._on_buffer_changed)
        layout.addWidget(self.buffer_combo, 1, 1)

        layout.addWidget(QLabel("Sample rate:"), 2, 0)
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(100, 1_000_000)
        self.sample_rate_spin.setValue(self._settings.sample_rate)
        self.sample_rate_spin.setSingleStep(1000)
        self.sample_rate_spin.setSuffix(" Hz")
        self.sample_rate_spin.valueChanged.connect(self._on_sample_rate_changed)
        layout.addWidget(self.sample_rate_spin, 2, 1)

        self._main_layout.addWidget(grp)

    def _build_yrange_group(self) -> None:
        """Build the Y-axis range and dv/dt controls group (merged)."""
        grp = QGroupBox("Vertical / dV/dt")
        layout = QGridLayout(grp)

        layout.addWidget(QLabel("Y min (V):"), 0, 0)
        self.y_min_spin = self._make_dspin(-100, 100, self._settings.y_min, 2)
        self.y_min_spin.valueChanged.connect(self._on_y_range_changed)
        layout.addWidget(self.y_min_spin, 0, 1)

        layout.addWidget(QLabel("Y max (V):"), 1, 0)
        self.y_max_spin = self._make_dspin(-100, 100, self._settings.y_max, 2)
        self.y_max_spin.valueChanged.connect(self._on_y_range_changed)
        layout.addWidget(self.y_max_spin, 1, 1)

        layout.addWidget(QLabel("V/div (V):"), 2, 0)
        self.volts_div_spin = self._make_dspin(0.001, 100, self._settings.volts_per_div, 3)
        self.volts_div_spin.valueChanged.connect(self._on_volts_div_changed)
        layout.addWidget(self.volts_div_spin, 2, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sepLine")
        layout.addWidget(sep, 3, 0, 1, 2)

        self.dvdt_checkbox = QCheckBox("Show dV/dt Overlay")
        self.dvdt_checkbox.setChecked(self._settings.dvdt_enabled)
        self.dvdt_checkbox.stateChanged.connect(self._on_dvdt_toggled)
        layout.addWidget(self.dvdt_checkbox, 4, 0, 1, 2)

        layout.addWidget(QLabel("dV/dt thresh:"), 5, 0)
        self.dvdt_thresh_spin = self._make_dspin(0, 100, self._settings.dvdt_threshold, 3)
        self.dvdt_thresh_spin.valueChanged.connect(self._on_dvdt_thresh_changed)
        layout.addWidget(self.dvdt_thresh_spin, 5, 1)

        self._main_layout.addWidget(grp)

    def _build_trigger_group(self) -> None:
        """Build the trigger settings group."""
        grp = QGroupBox("Trigger")
        layout = QGridLayout(grp)

        self.trigger_enable = QCheckBox("Enable Trigger")
        self.trigger_enable.setChecked(self._settings.trigger_enabled)
        self.trigger_enable.stateChanged.connect(self._on_trigger_enable_changed)
        layout.addWidget(self.trigger_enable, 0, 0, 1, 2)

        layout.addWidget(QLabel("Level (V):"), 1, 0)
        self.trigger_level_spin = self._make_dspin(-50, 50, self._settings.trigger_level, 3)
        self.trigger_level_spin.valueChanged.connect(self._on_trigger_level_changed)
        layout.addWidget(self.trigger_level_spin, 1, 1)

        layout.addWidget(QLabel("Edge:"), 2, 0)
        self.edge_combo = QComboBox()
        self.edge_combo.addItems(["Rising", "Falling"])
        self.edge_combo.setCurrentText(self._settings.trigger_edge.capitalize())
        self.edge_combo.currentTextChanged.connect(self._on_edge_changed)
        layout.addWidget(self.edge_combo, 2, 1)

        self._main_layout.addWidget(grp)

    def _build_dsp_group(self) -> None:
        """Build the FFT/DSP settings group."""
        grp = QGroupBox("FFT / DSP")
        layout = QGridLayout(grp)

        layout.addWidget(QLabel("Window:"), 0, 0)
        self.window_combo = QComboBox()
        self.window_combo.addItems(list(WINDOWS.keys()))
        self.window_combo.setCurrentText(self._settings.fft_window)
        self.window_combo.currentTextChanged.connect(self._on_window_changed)
        layout.addWidget(self.window_combo, 0, 1)

        self.log_scale_check = QCheckBox("Log Freq Scale")
        self.log_scale_check.setChecked(self._settings.fft_log_scale)
        self.log_scale_check.stateChanged.connect(self._on_log_scale_changed)
        layout.addWidget(self.log_scale_check, 1, 0, 1, 2)

        self._main_layout.addWidget(grp)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_dspin(
        mn: float, mx: float, val: float, decimals: int
    ) -> QDoubleSpinBox:
        """Create a configured QDoubleSpinBox."""
        sb = QDoubleSpinBox()
        sb.setRange(mn, mx)
        sb.setDecimals(decimals)
        sb.setValue(val)
        return sb

    def refresh_ports(self) -> None:
        """Repopulate the COM port dropdown from available serial ports."""
        self.port_combo.clear()
        ports = sorted(p.device for p in serial.tools.list_ports.comports())
        self.port_combo.addItems(ports)
        if self._settings.last_port in ports:
            self.port_combo.setCurrentText(self._settings.last_port)

    def set_connected(self, connected: bool) -> None:
        """Update the connect button state to reflect connection status."""
        self._connected = connected
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.connect_btn.setObjectName("disconnectBtn" if connected else "connectBtn")
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

    def set_trigger_level(self, level: float) -> None:
        """Update trigger level spinbox without emitting changed signals."""
        self.trigger_level_spin.blockSignals(True)
        self.trigger_level_spin.setValue(level)
        self.trigger_level_spin.blockSignals(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_connect_clicked(self) -> None:
        """Handle connect/disconnect button click."""
        if self._connected:
            self.disconnect_requested.emit()
        else:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self._settings.last_port = port
            self._settings.baud_rate = baud
            self.connect_requested.emit(port, baud)

    def _on_mapping_toggled(self, state: int) -> None:
        """Sync mapping enabled flag to settings."""
        self._settings.mapping_enabled = bool(state)
        self.mapping_changed.emit()

    def _on_mapping_apply(self) -> None:
        """Push mapping spinbox values to settings and emit signal."""
        self._settings.adc_min = self.adc_min_spin.value()
        self._settings.adc_max = self.adc_max_spin.value()
        self._settings.volt_min = self.volt_min_spin.value()
        self._settings.volt_max = self.volt_max_spin.value()
        self._settings.vref = self.vref_spin.value()
        self._settings.mapping_enabled = self.map_checkbox.isChecked()
        self.mapping_changed.emit()

    def _on_time_div_changed(self, value: float) -> None:
        """Sync time/div setting."""
        self._settings.time_per_div_ms = value
        self.settings_changed.emit()

    def _on_buffer_changed(self, text: str) -> None:
        """Sync buffer size setting."""
        try:
            self._settings.buffer_size = int(text)
            self.settings_changed.emit()
        except ValueError:
            pass

    def _on_sample_rate_changed(self, value: int) -> None:
        """Sync sample rate setting."""
        self._settings.sample_rate = value
        self.settings_changed.emit()

    def _on_y_range_changed(self) -> None:
        """Sync Y min/max settings."""
        self._settings.y_min = self.y_min_spin.value()
        self._settings.y_max = self.y_max_spin.value()
        self.settings_changed.emit()

    def _on_volts_div_changed(self, value: float) -> None:
        """Sync volts/div and auto-adjust Y range symmetrically."""
        self._settings.volts_per_div = value
        total = value * 8
        mid = (self._settings.y_min + self._settings.y_max) / 2.0
        self._settings.y_min = mid - total / 2.0
        self._settings.y_max = mid + total / 2.0
        self.y_min_spin.blockSignals(True)
        self.y_max_spin.blockSignals(True)
        self.y_min_spin.setValue(self._settings.y_min)
        self.y_max_spin.setValue(self._settings.y_max)
        self.y_min_spin.blockSignals(False)
        self.y_max_spin.blockSignals(False)
        self.settings_changed.emit()

    def _on_dvdt_toggled(self, state: int) -> None:
        """Sync dv/dt overlay toggle."""
        self._settings.dvdt_enabled = bool(state)
        self.settings_changed.emit()

    def _on_dvdt_thresh_changed(self, value: float) -> None:
        """Sync dv/dt threshold setting."""
        self._settings.dvdt_threshold = value
        self.settings_changed.emit()

    def _on_trigger_enable_changed(self, state: int) -> None:
        """Sync trigger enable setting."""
        self._settings.trigger_enabled = bool(state)
        self.settings_changed.emit()

    def _on_trigger_level_changed(self, value: float) -> None:
        """Sync trigger level setting."""
        self._settings.trigger_level = value
        self.settings_changed.emit()

    def _on_edge_changed(self, text: str) -> None:
        """Sync trigger edge setting."""
        self._settings.trigger_edge = text.lower()
        self.settings_changed.emit()

    def _on_window_changed(self, text: str) -> None:
        """Sync FFT window setting."""
        self._settings.fft_window = text
        self.settings_changed.emit()

    def _on_log_scale_changed(self, state: int) -> None:
        """Sync FFT log scale setting."""
        self._settings.fft_log_scale = bool(state)
        self.settings_changed.emit()
