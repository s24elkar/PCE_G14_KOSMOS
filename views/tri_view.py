from __future__ import annotations

from typing import Dict, Iterable, Optional

from PyQt6.QtWidgets import QMessageBox, QHBoxLayout, QVBoxLayout, QWidget, QLabel

from components.common_metadata import CommonMetadataWidget
from components.specific_metadata import SpecificMetadataWidget
from components.video_list import VideoListWidget


class TriView(QWidget):
    """
    Tri video main view. For now it focuses on the common metadata section.
    """

    def __init__(self, controller=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._specific_controller = None
        self._list_controller = None
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

        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        self.video_list_widget = VideoListWidget()
        body_layout.addWidget(self.video_list_widget, stretch=1)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)

        self.common_metadata_widget = CommonMetadataWidget()
        right_panel.addWidget(self.common_metadata_widget)

        self.specific_metadata_widget = SpecificMetadataWidget()
        right_panel.addWidget(self.specific_metadata_widget)

        body_layout.addLayout(right_panel, stretch=2)
        layout.addLayout(body_layout)

        self.setLayout(layout)

    # ------------------------------------------------------------------ #
    # Controller wiring
    # ------------------------------------------------------------------ #
    def connect_signals(self) -> None:
        if self.controller:
            try:
                self.common_metadata_widget.save_requested.disconnect(
                    self.controller.on_common_metadata_save
                )
            except TypeError:
                pass
            self.common_metadata_widget.save_requested.connect(
                self.controller.on_common_metadata_save
            )
        if self._specific_controller:
            try:
                self.specific_metadata_widget.save_requested.disconnect(
                    self._specific_controller.on_specific_metadata_save
                )
            except TypeError:
                pass
            self.specific_metadata_widget.save_requested.connect(
                self._specific_controller.on_specific_metadata_save
            )
        if self._list_controller:
            try:
                self.video_list_widget.video_selected.disconnect(
                    self._list_controller.on_video_selected
                )
            except TypeError:
                pass
            try:
                self.video_list_widget.rename_requested.disconnect(
                    self._list_controller.on_rename_requested
                )
            except TypeError:
                pass
            try:
                self.video_list_widget.delete_requested.disconnect(
                    self._list_controller.on_delete_requested
                )
            except TypeError:
                pass

            self.video_list_widget.video_selected.connect(
                self._list_controller.on_video_selected
            )
            self.video_list_widget.rename_requested.connect(
                self._list_controller.on_rename_requested
            )
            self.video_list_widget.delete_requested.connect(
                self._list_controller.on_delete_requested
            )

    def set_controller(self, controller) -> None:
        self.controller = controller
        self.connect_signals()

    def set_specific_metadata_controller(self, controller) -> None:
        self._specific_controller = controller
        self.connect_signals()

    def set_video_list_controller(self, controller) -> None:
        self._list_controller = controller
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

    def show_specific_metadata(self, video_name: str, metadata: Dict[str, str]) -> None:
        self.specific_metadata_widget.set_video(video_name, metadata)

    def clear_specific_metadata(self) -> None:
        self.specific_metadata_widget.clear()

    def show_video_list(self, videos: Iterable[dict]) -> None:
        self.video_list_widget.populate(videos)

    def show_video_details(self, *, name: str, date: str, duration: str) -> None:
        self.video_list_widget.set_details(name, date, duration)

    def clear_video_details(self) -> None:
        self.video_list_widget.clear_details()

    def show_video_message(self, message: str) -> None:
        QMessageBox.information(self, "Information", message)

    def select_video_in_list(self, name: str) -> None:
        self.video_list_widget.select_video(name)
