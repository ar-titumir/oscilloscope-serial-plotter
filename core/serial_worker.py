"""QThread-based serial port reader for Arduino ADC data."""

import numpy as np
import serial
from PyQt6.QtCore import QThread, pyqtSignal


class SerialWorker(QThread):
    """Reads ADC lines from a serial port and emits voltage chunks."""

    data_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)  # True = connected

    CHUNK_SIZE = 64  # samples emitted per signal

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        vref: float = 5.0,
        adc_bits: int = 10,
        mapping_enabled: bool = True,
        adc_min: float = 0.0,
        adc_max: float = 1023.0,
        volt_min: float = 0.0,
        volt_max: float = 5.0,
        parent=None,
    ) -> None:
        """Initialize worker with port config and voltage mapping parameters."""
        super().__init__(parent)
        self._port = port
        self._baud_rate = baud_rate
        self._vref = vref
        self._adc_bits = adc_bits
        self._mapping_enabled = mapping_enabled
        self._adc_min = adc_min
        self._adc_max = adc_max
        self._volt_min = volt_min
        self._volt_max = volt_max
        self._running = False
        self._serial: serial.Serial | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_mapping(
        self,
        enabled: bool,
        adc_min: float,
        adc_max: float,
        volt_min: float,
        volt_max: float,
        vref: float,
    ) -> None:
        """Update voltage mapping parameters at runtime."""
        self._mapping_enabled = enabled
        self._adc_min = adc_min
        self._adc_max = adc_max
        self._volt_min = volt_min
        self._volt_max = volt_max
        self._vref = vref

    def stop(self) -> None:
        """Signal the thread to stop and wait for it to finish."""
        self._running = False
        self.wait(2000)

    # ------------------------------------------------------------------
    # Thread entry
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Open serial port and continuously read ADC values."""
        try:
            self._serial = serial.Serial(
                self._port, self._baud_rate, timeout=1.0
            )
        except serial.SerialException as exc:
            self.error_occurred.emit(f"Cannot open {self._port}: {exc}")
            self.connection_changed.emit(False)
            return

        self._running = True
        self.connection_changed.emit(True)
        chunk: list[float] = []

        try:
            while self._running:
                try:
                    raw = self._serial.readline()
                except serial.SerialException as exc:
                    self.error_occurred.emit(f"Serial read error: {exc}")
                    break

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    adc_val = float(line)
                except ValueError:
                    continue

                voltage = self._convert(adc_val)
                chunk.append(voltage)

                if len(chunk) >= self.CHUNK_SIZE:
                    self.data_ready.emit(np.array(chunk, dtype=np.float32))
                    chunk.clear()

        finally:
            if chunk:
                self.data_ready.emit(np.array(chunk, dtype=np.float32))
            if self._serial and self._serial.is_open:
                self._serial.close()
            self.connection_changed.emit(False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _convert(self, adc_val: float) -> float:
        """Convert raw ADC value to voltage using current mapping settings."""
        if self._mapping_enabled:
            adc_range = self._adc_max - self._adc_min
            if adc_range == 0:
                return self._volt_min
            volt_range = self._volt_max - self._volt_min
            return self._volt_min + (adc_val - self._adc_min) / adc_range * volt_range
        else:
            adc_max = (2**self._adc_bits) - 1
            return adc_val / adc_max * self._vref
