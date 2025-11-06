import pytest

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance for all GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
