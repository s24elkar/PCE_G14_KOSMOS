import os
import sys
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance for all GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
