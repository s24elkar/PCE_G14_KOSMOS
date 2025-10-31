from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.controllers.extraction_controller import ExtractionController
from src.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    window = MainWindow()
    extraction_controller = ExtractionController(window.extraction_view, parent=window)
    window.register_controller("extraction", extraction_controller)

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
