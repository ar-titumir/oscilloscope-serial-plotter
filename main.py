"""Entry point for Serial Oscilloscope application."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from config.settings import AppSettings


def load_icon() -> QIcon:
    """Load application icon from project root (icon.png, icon.ico, or icon.svg)."""
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("icon.png", "icon.ico", "icon.svg", "icon.jpg"):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()  # fallback: no icon


def main() -> None:
    """Initialize and launch the oscilloscope application."""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Serial Oscilloscope")
    app.setOrganizationName("SerialOscilloscope")

    # Set icon for taskbar, alt-tab, and window title bar
    icon = load_icon()
    app.setWindowIcon(icon)

    settings = AppSettings()

    qss_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow(settings)
    window.setWindowTitle("Serial Oscilloscope")
    window.setWindowIcon(icon)   # also set on the window itself (belt + braces)
    window.setMinimumSize(1200, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
