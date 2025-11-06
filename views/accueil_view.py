from __future__ import annotations

from typing import Iterable, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AccueilView(QWidget):
    """
    Landing page for campaign selection/creation.
    """

    new_campaign_requested = pyqtSignal(str)
    open_campaign_requested = pyqtSignal(str)

    def __init__(self, controller=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self.connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("KOSMOS - Accueil campagnes")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: 700;
            }
            """
        )
        layout.addWidget(title)

        self.campaign_list = QListWidget()
        self.campaign_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.campaign_list, stretch=1)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom de la nouvelle campagne")
        form_layout.addWidget(self.name_input, stretch=1)

        self.create_button = QPushButton("Créer")
        form_layout.addWidget(self.create_button)

        self.open_button = QPushButton("Ouvrir")
        self.open_button.setEnabled(False)
        form_layout.addWidget(self.open_button)

        layout.addLayout(form_layout)

    # ------------------------------------------------------------------ #
    # Controller wiring
    # ------------------------------------------------------------------ #
    def connect_signals(self) -> None:
        self.create_button.clicked.connect(self._handle_create_clicked)
        self.open_button.clicked.connect(self._handle_open_clicked)
        self.campaign_list.itemSelectionChanged.connect(self._handle_selection_changed)
        self.campaign_list.itemDoubleClicked.connect(
            lambda item: self.open_campaign_requested.emit(item.text())
        )

        if self.controller:
            self.set_controller(self.controller)

    def set_controller(self, controller) -> None:
        self.controller = controller
        self.new_campaign_requested.connect(controller.on_new_campaign)
        self.open_campaign_requested.connect(controller.on_open_campaign)

    # ------------------------------------------------------------------ #
    # UI helpers
    # ------------------------------------------------------------------ #
    def show_campaigns(self, campaigns: Iterable[str]) -> None:
        previous_selection = self.selected_campaign()
        self.campaign_list.clear()
        for name in campaigns:
            QListWidgetItem(str(name), self.campaign_list)
        self._restore_selection(previous_selection)

    def show_information(self, message: str) -> None:
        QMessageBox.information(self, "Information", message)

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Erreur", message)

    def selected_campaign(self) -> Optional[str]:
        item = self.campaign_list.currentItem()
        return item.text() if item else None

    def clear_name_input(self) -> None:
        self.name_input.clear()

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def _handle_create_clicked(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Veuillez saisir un nom de campagne.")
            return
        self.new_campaign_requested.emit(name)

    def _handle_open_clicked(self) -> None:
        name = self.selected_campaign()
        if name:
            self.open_campaign_requested.emit(name)

    def _handle_selection_changed(self) -> None:
        self.open_button.setEnabled(self.selected_campaign() is not None)

    def _restore_selection(self, campaign_name: Optional[str]) -> None:
        if campaign_name is None:
            self.campaign_list.clearSelection()
            self.open_button.setEnabled(False)
            return
        matching_items = self.campaign_list.findItems(
            campaign_name, Qt.MatchFlag.MatchExactly
        )
        if matching_items:
            self.campaign_list.setCurrentItem(matching_items[0])
        else:
            self.campaign_list.clearSelection()
            self.open_button.setEnabled(False)
