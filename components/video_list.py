from __future__ import annotations

from typing import Iterable, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QFormLayout,
)


class VideoListWidget(QWidget):
    """
    Displays the list of videos with rename/delete actions and read-only details.
    """

    video_selected = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Liste des vidéos")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
            """
        )
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget, stretch=1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.rename_button = QPushButton("Renommer")
        self.rename_button.setEnabled(False)
        button_layout.addWidget(self.rename_button)

        self.delete_button = QPushButton("Supprimer")
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        details_group = QGroupBox("Détails")
        details_layout = QFormLayout(details_group)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(6)

        self.name_label = QLabel("-")
        self.date_label = QLabel("-")
        self.duration_label = QLabel("-")

        for label in (self.name_label, self.date_label, self.duration_label):
            label.setObjectName("detailLabel")
            label.setStyleSheet(
                """
                QLabel#detailLabel {
                    font-weight: 500;
                }
                """
            )

        details_layout.addRow("Nom :", self.name_label)
        details_layout.addRow("Date :", self.date_label)
        details_layout.addRow("Durée :", self.duration_label)

        layout.addWidget(details_group)

        # Signal wiring
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.rename_button.clicked.connect(self._on_rename_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    def populate(self, videos: Iterable[dict]) -> None:
        current = self.current_video()
        self.list_widget.clear()
        for video in videos:
            item = QListWidgetItem(video["name"])
            item.setData(Qt.ItemDataRole.UserRole, video)
            self.list_widget.addItem(item)
        if current:
            self.select_video(current)
        else:
            self._clear_details()

    def current_video(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        return item.text() if item else None

    def select_video(self, video_name: str) -> None:
        matching = self.list_widget.findItems(video_name, Qt.MatchFlag.MatchExactly)
        if matching:
            self.list_widget.setCurrentItem(matching[0])
        else:
            self.list_widget.clearSelection()

    def set_details(self, name: str, date: str, duration: str) -> None:
        self.name_label.setText(name)
        self.date_label.setText(date)
        self.duration_label.setText(duration)

    # ------------------------------------------------------------------ #
    # Internal callbacks
    # ------------------------------------------------------------------ #
    def _on_selection_changed(self) -> None:
        video_name = self.current_video()
        has_selection = video_name is not None
        self.rename_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        if video_name:
            self.video_selected.emit(video_name)
        else:
            self._clear_details()

    def _on_rename_clicked(self) -> None:
        video_name = self.current_video()
        if video_name:
            self.rename_requested.emit(video_name)

    def _on_delete_clicked(self) -> None:
        video_name = self.current_video()
        if video_name:
            self.delete_requested.emit(video_name)

    def clear_details(self) -> None:
        self.set_details("-", "-", "-")
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _clear_details(self) -> None:
        self.clear_details()
