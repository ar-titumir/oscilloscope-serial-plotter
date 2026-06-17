"""Main application window: assembles all panels, toolbar, and menu bar."""

import os
from datetime import datetime

import numpy as np
from PyQt6.QtCore import QTimer, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.dsp import (
    WINDOWS,
    compute_duty_cycle,
    compute_dvdt,
    compute_fft,
    compute_frequency,
    compute_rms,
    compute_vpp,
)
from core.recorder import SignalRecorder
from core.ring_buffer import RingBuffer
from core.screen_keepalive import ScreenKeepAlive
from core.serial_worker import SerialWorker
from core.trigger import find_trigger_index
from file_io.file_exporter import save_csv, save_fft_csv, save_screenshot, save_wav
from ui.controls_panel import ControlsPanel
from ui.fft_widget import FftWidget
from ui.measurements_panel import MeasurementsPanel
from ui.save_recording_dialog import SaveRecordingDialog
from ui.settings_dialog import SettingsDialog
from ui.waveform_widget import WaveformWidget


class MainWindow(QMainWindow):
    """Top-level oscilloscope window — wires all subsystems together."""

    def __init__(self, settings, parent=None) -> None:
        """Initialize all subsystems and load persisted settings."""
        super().__init__(parent)
        self._settings = settings
        self._settings.load()

        self._worker: SerialWorker | None = None
        self._running = self._settings.run_state

        self._ring = RingBuffer(self._settings.buffer_size)
        self._last_freqs: np.ndarray = np.array([0.0])
        self._last_mags: np.ndarray = np.array([-120.0])
        self._keepalive = ScreenKeepAlive()

        self._recorder = SignalRecorder(float(self._settings.sample_rate))

        self._build_ui()
        self._build_menu()
        self._build_toolbar()

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps
        self._timer.timeout.connect(self._refresh_plots)
        self._timer.start()

        # Status bar blink timer for recording indicator
        self._rec_blink_timer = QTimer(self)
        self._rec_blink_timer.setInterval(600)
        self._rec_blink_timer.timeout.connect(self._blink_rec_status)
        self._rec_blink_state = False

        self._apply_theme()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct and arrange all child widgets."""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        # Left: controls panel
        self._controls = ControlsPanel(self._settings)
        self._controls.connect_requested.connect(self._on_connect)
        self._controls.disconnect_requested.connect(self._on_disconnect)
        self._controls.settings_changed.connect(self._on_settings_changed)
        self._controls.mapping_changed.connect(self._on_mapping_changed)
        root_layout.addWidget(self._controls)

        # Centre column: splitter (waveform + FFT) on top, measurements bar below
        centre_col = QWidget()
        centre_col_layout = QVBoxLayout(centre_col)
        centre_col_layout.setContentsMargins(0, 0, 0, 0)
        centre_col_layout.setSpacing(2)

        self._centre_splitter = QSplitter(Qt.Orientation.Vertical)

        self._waveform = WaveformWidget(self._settings)
        self._waveform.trigger_level_changed.connect(self._controls.set_trigger_level)
        self._centre_splitter.addWidget(self._waveform)

        self._fft = FftWidget(self._settings)
        self._centre_splitter.addWidget(self._fft)
        self._centre_splitter.setSizes([400, 200])

        self._measurements = MeasurementsPanel()

        centre_col_layout.addWidget(self._centre_splitter, stretch=1)
        centre_col_layout.addWidget(self._measurements)

        root_layout.addWidget(centre_col, stretch=1)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready — not connected.")

    def _build_menu(self) -> None:
        """Build the File menu and Settings menu."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        act_csv = QAction("Save Waveform CSV…", self)
        act_csv.setShortcut(QKeySequence("Ctrl+S"))
        act_csv.triggered.connect(self._save_waveform_csv)
        file_menu.addAction(act_csv)

        act_fft_csv = QAction("Save FFT CSV…", self)
        act_fft_csv.triggered.connect(self._save_fft_csv)
        file_menu.addAction(act_fft_csv)

        act_shot = QAction("Save Screenshot…", self)
        act_shot.setShortcut(QKeySequence("Ctrl+P"))
        act_shot.triggered.connect(self._save_screenshot)
        file_menu.addAction(act_shot)

        act_wav = QAction("Save WAV…", self)
        act_wav.triggered.connect(self._save_wav)
        file_menu.addAction(act_wav)

        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = menubar.addMenu("&View")
        act_fft_toggle = QAction("Toggle FFT Panel", self)
        act_fft_toggle.setCheckable(True)
        act_fft_toggle.setChecked(True)
        act_fft_toggle.triggered.connect(
            lambda checked: self._fft.setVisible(checked)
        )
        view_menu.addAction(act_fft_toggle)

        settings_menu = menubar.addMenu("&Settings")
        act_settings = QAction("Preferences…", self)
        act_settings.triggered.connect(self._open_settings_dialog)
        settings_menu.addAction(act_settings)

    def _build_toolbar(self) -> None:
        """Build the main toolbar with Run/Pause, Record, Settings, and Clear buttons."""
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Run / Pause
        self._run_action = QAction("⏸  Pause", self)
        self._run_action.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self._run_action.setToolTip("Run / Pause (Space)")
        self._run_action.triggered.connect(self._toggle_run)
        tb.addAction(self._run_action)

        tb.addSeparator()

        # Record
        self._record_action = QAction("⏺  Record", self)
        self._record_action.setToolTip("Start / Stop recording signal to Excel")
        self._record_action.setObjectName("recordBtn")
        self._record_action.triggered.connect(self._toggle_recording)
        tb.addAction(self._record_action)

        tb.addSeparator()

        # Settings
        act_settings_tb = QAction("⚙  Settings", self)
        act_settings_tb.triggered.connect(self._open_settings_dialog)
        tb.addAction(act_settings_tb)

        tb.addSeparator()

        # Clear buffer
        act_clear = QAction("🗑  Clear Buffer", self)
        act_clear.triggered.connect(self._clear_buffer)
        tb.addAction(act_clear)

    # ------------------------------------------------------------------
    # Slots — serial
    # ------------------------------------------------------------------

    @pyqtSlot(str, int)
    def _on_connect(self, port: str, baud: int) -> None:
        """Start the serial worker for the given port and baud rate."""
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

        s = self._settings
        self._worker = SerialWorker(
            port=port,
            baud_rate=baud,
            vref=s.vref,
            mapping_enabled=s.mapping_enabled,
            adc_min=s.adc_min,
            adc_max=s.adc_max,
            volt_min=s.volt_min,
            volt_max=s.volt_max,
        )
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_serial_error)
        self._worker.connection_changed.connect(self._on_connection_changed)
        self._worker.start()
        self._status_bar.showMessage(f"Connecting to {port} @ {baud}…")

    @pyqtSlot()
    def _on_disconnect(self) -> None:
        """Stop the serial worker."""
        if self._recorder.is_recording:
            self._stop_recording()
        if self._worker:
            self._worker.stop()
            self._worker = None
        self._controls.set_connected(False)
        self._status_bar.showMessage("Disconnected.")

    @pyqtSlot(np.ndarray)
    def _on_data_ready(self, chunk: np.ndarray) -> None:
        """Receive a new data chunk — feed ring buffer and recorder."""
        self._ring.append(chunk)
        self._recorder.feed(chunk)

    @pyqtSlot(str)
    def _on_serial_error(self, message: str) -> None:
        """Show a serial error in a message box."""
        QMessageBox.critical(self, "Serial Error", message)
        self._controls.set_connected(False)
        self._status_bar.showMessage(f"Error: {message}")

    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool) -> None:
        """Update controls to reflect new connection state."""
        self._controls.set_connected(connected)
        if connected:
            self._status_bar.showMessage("Connected.")
        else:
            self._status_bar.showMessage("Disconnected.")

    # ------------------------------------------------------------------
    # Slots — settings
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_settings_changed(self) -> None:
        """Re-apply settings to all widgets when a control changes."""
        self._ring.resize(self._settings.buffer_size)
        self._recorder.update_sample_rate(float(self._settings.sample_rate))
        self._waveform.set_y_range(self._settings.y_min, self._settings.y_max)
        self._waveform.set_dvdt_overlay(self._settings.dvdt_enabled)
        self._waveform.set_trigger_level(self._settings.trigger_level)
        self._settings.save()

    @pyqtSlot()
    def _on_mapping_changed(self) -> None:
        """Push updated mapping parameters to the running serial worker."""
        if self._worker is not None:
            s = self._settings
            self._worker.update_mapping(
                enabled=s.mapping_enabled,
                adc_min=s.adc_min,
                adc_max=s.adc_max,
                volt_min=s.volt_min,
                volt_max=s.volt_max,
                vref=s.vref,
            )
        self._settings.save()

    # ------------------------------------------------------------------
    # Plot refresh
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _refresh_plots(self) -> None:
        """Main plot refresh cycle called every 33 ms."""
        self._update_keepalive()

        if not self._running:
            return

        data = self._ring.get_data()
        if len(data) < 4:
            return

        s = self._settings
        sample_rate = float(s.sample_rate)

        # Trigger alignment
        trigger_index = 0
        if s.trigger_enabled:
            trigger_index = find_trigger_index(data, s.trigger_level, s.trigger_edge)

        self._waveform.update_plot(data, sample_rate, trigger_index)

        # FFT
        freqs, mags = compute_fft(data, sample_rate, s.fft_window)
        self._last_freqs = freqs
        self._last_mags = mags
        self._fft.update_fft(freqs, mags)

        # Measurements
        triggered_data = data[trigger_index:]
        if len(triggered_data) < 2:
            triggered_data = data

        freq = compute_frequency(triggered_data, sample_rate)
        vpp = compute_vpp(triggered_data)
        vmax = float(np.max(triggered_data))
        vmin = float(np.min(triggered_data))
        vrms = compute_rms(triggered_data)
        duty = compute_duty_cycle(triggered_data, s.trigger_level)

        dvdt = compute_dvdt(triggered_data, sample_rate)
        dvdt_rms = float(np.sqrt(np.mean(dvdt**2))) if len(dvdt) > 0 else 0.0

        self._measurements.update_measurements(freq, vpp, vmax, vmin, vrms, duty, dvdt_rms)

    # ------------------------------------------------------------------
    # Toolbar / menu actions
    # ------------------------------------------------------------------

    def _toggle_run(self) -> None:
        """Toggle between running and paused states."""
        self._running = not self._running
        self._settings.run_state = self._running
        self._run_action.setText("⏸  Pause" if self._running else "▶  Run")
        self._status_bar.showMessage("Running." if self._running else "Paused.")
        self._update_keepalive()

    def _toggle_recording(self) -> None:
        """Start or stop signal recording."""
        if self._recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        """Begin accumulating samples into the recorder."""
        self._recorder.start()
        self._record_action.setText("⏹  Stop Rec")
        self._record_action.setToolTip("Stop recording and save to Excel")
        self._rec_blink_timer.start()
        self._status_bar.showMessage("● Recording…")

    def _stop_recording(self) -> None:
        """Stop the recorder and open the save dialog."""
        self._recorder.stop()
        self._rec_blink_timer.stop()
        self._record_action.setText("⏺  Record")
        self._record_action.setToolTip("Start recording signal to Excel")

        n = self._recorder.sample_count
        if n == 0:
            self._status_bar.showMessage("Recording stopped — no data captured.")
            return

        # Build default filename from recording start time
        t = self._recorder.start_time
        default_name = t.strftime("recording_%Y%m%d_%H%M%S") if t else "recording"
        default_dir = os.path.abspath("storage")
        os.makedirs(default_dir, exist_ok=True)

        dlg = SaveRecordingDialog(default_name, default_dir, self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            self._status_bar.showMessage(f"Recording discarded ({n} samples).")
            return

        path = dlg.get_path()
        try:
            saved = self._recorder.save_xlsx(path)
            self._status_bar.showMessage(f"Recording saved → {path}  ({saved} samples)")
        except (ValueError, OSError) as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            self._status_bar.showMessage("Recording save failed.")

    def _blink_rec_status(self) -> None:
        """Toggle the recording indicator in the status bar."""
        self._rec_blink_state = not self._rec_blink_state
        n = self._recorder.sample_count
        if self._rec_blink_state:
            self._status_bar.showMessage(f"● Recording…  {n} samples")
        else:
            self._status_bar.showMessage(f"  Recording…  {n} samples")

    def _clear_buffer(self) -> None:
        """Clear the ring buffer."""
        self._ring.clear()

    def _open_settings_dialog(self) -> None:
        """Show the preferences dialog."""
        dlg = SettingsDialog(self._settings, self)
        dlg.settings_applied.connect(self._apply_theme)
        dlg.exec()

    def _apply_theme(self) -> None:
        """Re-apply the current theme QSS to the application."""
        qss = self._settings.apply_theme_to_qss()
        if qss:
            QApplication.instance().setStyleSheet(qss)
        self._waveform.apply_settings()
        self._fft.apply_settings()

    # ------------------------------------------------------------------
    # File exports
    # ------------------------------------------------------------------

    def _save_waveform_csv(self) -> None:
        """Prompt for path and save current waveform data as CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Waveform CSV", "storage/waveform.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        data = self._ring.get_data()
        try:
            save_csv(data, float(self._settings.sample_rate), path)
            self._status_bar.showMessage(f"Saved waveform CSV → {path}")
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _save_fft_csv(self) -> None:
        """Prompt for path and save current FFT data as CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save FFT CSV", "storage/fft.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            save_fft_csv(self._last_freqs, self._last_mags, path)
            self._status_bar.showMessage(f"Saved FFT CSV → {path}")
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _save_screenshot(self) -> None:
        """Prompt for path and save a screenshot of the main window."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "storage/screenshot.png", "PNG Images (*.png)"
        )
        if not path:
            return
        if not save_screenshot(self, path):
            QMessageBox.warning(self, "Screenshot", "Screenshot could not be saved.")
        else:
            self._status_bar.showMessage(f"Screenshot saved → {path}")

    def _save_wav(self) -> None:
        """Prompt for path and save current buffer as a WAV file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save WAV", "storage/waveform.wav", "WAV Audio (*.wav)"
        )
        if not path:
            return
        data = self._ring.get_data()
        try:
            save_wav(data, float(self._settings.sample_rate), path)
            self._status_bar.showMessage(f"Saved WAV → {path}")
        except (ImportError, OSError) as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Stop recording, clean up serial worker, and save settings on close."""
        if self._recorder.is_recording:
            self._recorder.stop()
        self._timer.stop()
        self._rec_blink_timer.stop()
        self._keepalive.disable()
        if self._worker:
            self._worker.stop()
        self._settings.save()
        event.accept()

    def keyPressEvent(self, event) -> None:
        """Handle Space (run/pause) and R (record toggle) keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Space:
            self._toggle_run()
        elif event.key() == Qt.Key.Key_R and not event.isAutoRepeat():
            self._toggle_recording()
        else:
            super().keyPressEvent(event)

    def _update_keepalive(self) -> None:
        """Enable screen keep-awake when running and visible; release otherwise."""
        is_minimized = bool(self.windowState() & Qt.WindowState.WindowMinimized)
        should_keep = self._running and not is_minimized
        if should_keep:
            self._keepalive.enable()
        else:
            self._keepalive.disable()

    def changeEvent(self, event) -> None:
        """Release keep-awake when window is minimized, re-enable on restore."""
        super().changeEvent(event)
        self._update_keepalive()
