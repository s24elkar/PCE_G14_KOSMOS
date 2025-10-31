"""
Video viewer widget used throughout the KOSMOS interface.

The widget wraps a ``QVideoWidget`` and provides a clean placeholder when no
media is loaded. The class also exposes small helpers for displaying still
frames provided as ``QImage`` objects, which makes it usable with OpenCV
processing pipelines.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtMultimediaWidgets import QVideoWidget
except ImportError:  # pragma: no cover - optional multimedia dependency
    QVideoWidget = None  # type: ignore

if TYPE_CHECKING:
    from PyQt6.QtMultimedia import QMediaPlayer


class VideoViewer(QWidget):
    """
    High-level video display widget with a placeholder state.

    Parameters
    ----------
    parent:
        Optional parent widget.
    placeholder_text:
        Message shown when no media is currently loaded.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        placeholder_text: str = "Aucune vidéo chargée",
    ) -> None:
        super().__init__(parent)
        self._player: Optional["QMediaPlayer"] = None
        self._placeholder_text = placeholder_text

        self._build_ui()
        self.setMinimumSize(320, 180)

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self._stack = QStackedLayout()
        self._placeholder = QLabel(self._placeholder_text, self)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        if QVideoWidget is not None:
            self._video_widget: QWidget = QVideoWidget(self)
            self._video_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
        else:
            missing = QLabel("QtMultimediaWidgets manquant : affichage image", self)
            missing.setAlignment(Qt.AlignmentFlag.AlignCenter)
            missing.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self._video_widget = missing

        self._frame_label = QLabel(self)
        self._frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._frame_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._frame_label.setScaledContents(True)
        self._frame_label.hide()

        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._video_widget)
        self._stack.addWidget(self._frame_label)

        outer_layout.addLayout(self._stack)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_player(self, player: "QMediaPlayer") -> None:
        """
        Attach a ``QMediaPlayer`` instance to the viewer.

        The player video output is automatically redirected to the embedded
        ``QVideoWidget``. When QtMultimedia widgets are not available the call
        raises ``RuntimeError``.
        """
        if QVideoWidget is None:
            raise RuntimeError(
                "QtMultimediaWidgets is not available; cannot bind video output."
            )

        if self._player is player:
            return

        if self._player is not None:
            self._player.setVideoOutput(None)

        self._player = player
        player.setVideoOutput(self._video_widget)
        self.show_video()

    def show_placeholder(self, text: Optional[str] = None) -> None:
        if text is not None:
            self._placeholder_text = text
            self._placeholder.setText(text)
        self._frame_label.clear()
        self._frame_label.hide()
        self._stack.setCurrentWidget(self._placeholder)

    def show_video(self) -> None:
        self._frame_label.clear()
        self._frame_label.hide()
        self._stack.setCurrentWidget(self._video_widget)

    def display_frame(self, frame: QImage) -> None:
        """
        Display a pre-rendered frame in the viewer.

        This helper is handy when the processing pipeline produces frames via
        OpenCV (converted to ``QImage``) instead of using ``QMediaPlayer``.
        """
        self._frame_label.setPixmap(QPixmap.fromImage(frame))
        self._frame_label.show()
        self._stack.setCurrentWidget(self._frame_label)

    def clear(self) -> None:
        """Return the widget to its initial placeholder state."""
        if self._player is not None:
            self._player.stop()
        self.show_placeholder(self._placeholder_text)
