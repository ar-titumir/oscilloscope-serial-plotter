"""Application settings with JSON persistence."""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any


SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "settings.json")


@dataclass
class AppSettings:
    """Stores all user-configurable application settings."""

    # Connection
    baud_rate: int = 115200
    last_port: str = ""

    # Signal mapping
    adc_min: float = 0.0
    adc_max: float = 1023.0
    volt_min: float = 0.0
    volt_max: float = 5.0
    mapping_enabled: bool = True
    vref: float = 5.0

    # Timebase
    time_per_div_ms: float = 10.0
    buffer_size: int = 1024
    sample_rate: int = 10000

    # Y-axis / vertical
    y_min: float = -0.5
    y_max: float = 5.5
    volts_per_div: float = 1.0

    # dv/dt
    dvdt_enabled: bool = False
    dvdt_threshold: float = 0.5

    # Trigger
    trigger_level: float = 2.5
    trigger_edge: str = "rising"
    trigger_enabled: bool = True

    # DSP
    fft_window: str = "Hanning"
    fft_log_scale: bool = False

    # Theme
    theme: str = "dark"
    accent_color: str = "#00bfff"
    bg_color: str = "#1e1e1e"
    panel_color: str = "#2d2d2d"
    plot_bg_color: str = "#0d0d0d"
    grid_color: str = "#333333"
    waveform_color: str = "#00ff88"
    fft_color: str = "#ff6b35"

    # UI state
    run_state: bool = True
    show_fft: bool = True
    show_measurements: bool = True

    def load(self) -> "AppSettings":
        """Load settings from disk, return self with applied values."""
        path = os.path.normpath(SETTINGS_PATH)
        if not os.path.exists(path):
            return self
        try:
            with open(path, "r") as f:
                data: dict[str, Any] = json.load(f)
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except (json.JSONDecodeError, OSError):
            pass
        return self

    def save(self) -> None:
        """Persist current settings to disk."""
        path = os.path.normpath(SETTINGS_PATH)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w") as f:
                json.dump(asdict(self), f, indent=2)
        except OSError as e:
            print(f"[Settings] Could not save: {e}")

    def apply_theme_to_qss(self) -> str:
        """Return a QSS string with current theme colors substituted."""
        qss_path = os.path.join(os.path.dirname(__file__), "..", "ui", "styles.qss")
        if not os.path.exists(qss_path):
            return ""
        with open(qss_path, "r") as f:
            qss = f.read()
        qss = qss.replace("__BG__", self.bg_color)
        qss = qss.replace("__PANEL__", self.panel_color)
        qss = qss.replace("__ACCENT__", self.accent_color)
        return qss
