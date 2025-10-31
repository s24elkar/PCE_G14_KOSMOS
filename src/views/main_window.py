"""
Top-level application window hosting the KOSMOS workspaces.
"""
from __future__ import annotations

from typing import Dict

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from src.views.extraction_view import ExtractionView


class MainWindow(QMainWindow):
    """
    Single point of entry for the desktop application.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KOSMOS – Interface")
        self.resize(1280, 720)

        self._controllers: Dict[str, object] = {}

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.extraction_view = ExtractionView(self)
        self.tabs.addTab(self.extraction_view, "Extraction")

    def register_controller(self, name: str, controller: object) -> None:
        """
        Store controllers to avoid garbage collection and future access.
        """
        self._controllers[name] = controller
