from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QWidget, QLabel

from components.common_metadata import CommonMetadataWidget


class TriView(QWidget):
    """
    Tri video main view. For now it focuses on the common metadata section.
    """

    def __init__(self, controller=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self.connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel("Tri vidéo - Métadonnées")
        header.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 700;
            }
            """
        )
        layout.addWidget(header)

        self.common_metadata_widget = CommonMetadataWidget()
        layout.addWidget(self.common_metadata_widget)

    # ------------------------------------------------------------------ #
    # Controller wiring
    # ------------------------------------------------------------------ #
    def connect_signals(self) -> None:
        if not self.controller:
            return
        self.common_metadata_widget.save_requested.connect(
            self.controller.on_common_metadata_save
        )

    def set_controller(self, controller) -> None:
        self.controller = controller
        self.connect_signals()

    # ------------------------------------------------------------------ #
    # Methods used by the controller
    # ------------------------------------------------------------------ #
    def show_common_metadata(self, metadata: Dict[str, str]) -> None:
        self.common_metadata_widget.set_metadata(metadata)

    def show_success_dialog(self) -> None:
        QMessageBox.information(
            self,
            "Succès",
            "Modifié avec succès",
        )
