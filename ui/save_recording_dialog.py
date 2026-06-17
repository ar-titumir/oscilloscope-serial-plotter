"""Dialog shown after recording stops — lets user edit filename and pick save directory."""

import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SaveRecordingDialog(QDialog):
    """Modal dialog for confirming the recording filename and output directory."""

    def __init__(self, default_name: str, default_dir: str, parent=None) -> None:
        """Initialize with a pre-filled timestamp filename and default directory."""
        super().__init__(parent)
        self.setWindowTitle("Save Recording")
        self.setMinimumWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._dir = default_dir
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # File name row
        layout.addWidget(QLabel("File name:"))
        self._name_edit = QLineEdit(default_name)
        self._name_edit.setPlaceholderText("recording_YYYYMMDD_HHMMSS")
        layout.addWidget(self._name_edit)

        # Directory row
        layout.addWidget(QLabel("Save to folder:"))
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(default_dir)
        self._dir_edit.setReadOnly(True)
        dir_row.addWidget(self._dir_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # Full path preview
        self._preview_lbl = QLabel()
        self._preview_lbl.setObjectName("hexLabel")
        self._preview_lbl.setWordWrap(True)
        layout.addWidget(self._preview_lbl)
        self._update_preview()

        self._name_edit.textChanged.connect(self._update_preview)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_path(self) -> str:
        """Return the full resolved output path including .xlsx extension."""
        name = self._name_edit.text().strip() or self._default_name()
        if not name.endswith(".xlsx"):
            name += ".xlsx"
        return os.path.join(self._dir, name)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _default_name() -> str:
        """Generate a timestamp-based default filename."""
        return datetime.now().strftime("recording_%Y%m%d_%H%M%S")

    def _browse(self) -> None:
        """Open a folder picker and update the directory field."""
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._dir
        )
        if chosen:
            self._dir = chosen
            self._dir_edit.setText(chosen)
            self._update_preview()

    def _update_preview(self) -> None:
        """Refresh the full path preview label."""
        self._preview_lbl.setText(f"→  {self.get_path()}")
