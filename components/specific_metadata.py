from __future__ import annotations

from typing import Dict, Optional

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


class SpecificMetadataWidget(QWidget):
    """
    Scrollable editor for per-video metadata entries.
    """

    save_requested = pyqtSignal(str, dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_video: Optional[str] = None
        self._inputs: Dict[str, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.title_label = QLabel("Métadonnées propres")
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )
        layout.addWidget(self.title_label)

        self.video_label = QLabel("Aucune vidéo sélectionnée")
        self.video_label.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 13px;
            }
            """
        )
        layout.addWidget(self.video_label)

        self._form_container = QWidget()
        self._form_layout = QFormLayout(self._form_container)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self._form_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)
        self.ok_button.setFixedWidth(120)
        self.ok_button.clicked.connect(self._handle_save_clicked)
        layout.addWidget(self.ok_button)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_video(self, video_name: str, metadata: Dict[str, str]) -> None:
        self._current_video = video_name
        self.video_label.setText(f"Vidéo sélectionnée : {video_name}")
        self.ok_button.setEnabled(True)
        self._populate(metadata)

    def clear(self) -> None:
        self._current_video = None
        self.video_label.setText("Aucune vidéo sélectionnée")
        self.ok_button.setEnabled(False)
        self._populate({})

    def metadata(self) -> Dict[str, str]:
        return {key: line_edit.text() for key, line_edit in self._inputs.items()}

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _populate(self, metadata: Dict[str, str]) -> None:
        for key, widget in list(self._inputs.items()):
            self._form_layout.removeWidget(widget)
            widget.deleteLater()
            self._inputs.pop(key, None)

        for key, value in metadata.items():
            line_edit = QLineEdit()
            line_edit.setText(value)
            line_edit.setObjectName(f"specific_metadata_{key}")
            self._form_layout.addRow(f"{key} :", line_edit)
            self._inputs[key] = line_edit

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def _handle_save_clicked(self) -> None:
        if not self._current_video:
            return
        self.save_requested.emit(self._current_video, self.metadata())
