"""Entry point for Arduino Oscilloscope application."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from config.settings import AppSettings


def main() -> None:
    """Initialize and launch the oscilloscope application."""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Arduino Oscilloscope")
    app.setOrganizationName("ArduinoOscilloscope")

    settings = AppSettings()

    qss_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow(settings)
    window.setWindowTitle("Arduino Oscilloscope")
    window.setMinimumSize(1200, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
