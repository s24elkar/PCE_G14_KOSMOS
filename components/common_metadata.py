from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFormLayout,
)


class CommonMetadataWidget(QWidget):
    """
    Scrollable form used to edit metadata shared across videos.
    """

    save_requested = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._inputs: Dict[str, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Métadonnées communes")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )
        layout.addWidget(title)

        self._form_widget = QWidget()
        self._form_layout = QFormLayout(self._form_widget)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self._form_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._on_save_clicked)
        self.ok_button.setFixedWidth(120)
        layout.addWidget(self.ok_button)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_metadata(self, metadata: Dict[str, str]) -> None:
        """Populate the form with the provided dictionary."""
        # Remove existing widgets from the layout.
        for key, line_edit in list(self._inputs.items()):
            self._form_layout.removeWidget(line_edit)
            line_edit.deleteLater()
            self._inputs.pop(key, None)

        for key, value in metadata.items():
            line_edit = QLineEdit()
            line_edit.setText(value)
            line_edit.setObjectName(f"metadata_{key}")
            self._form_layout.addRow(f"{key} :", line_edit)
            self._inputs[key] = line_edit

    def metadata(self) -> Dict[str, str]:
        """Return the current values from the form."""
        return {key: line_edit.text() for key, line_edit in self._inputs.items()}

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def _on_save_clicked(self) -> None:
        self.save_requested.emit(self.metadata())
