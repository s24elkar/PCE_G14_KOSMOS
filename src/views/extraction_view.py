"""
Extraction tab view assembling core UI components.

The widget embeds a ``VideoViewer`` for playback alongside the shared
``PlaybackBar`` element. A small header bar exposes an *Ouvrir* button and
the currently loaded media label.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.components import PlaybackBar, VideoViewer


class ExtractionView(QWidget):
    """
    Visual container for the extraction workflow.

    Signals
    -------
    requestOpenMedia:
        Emitted when the *Ouvrir…* button is clicked.
    """

    requestOpenMedia = pyqtSignal()
    requestEnhanceImage = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("KOSMOS – Extraction")
        self.resize(960, 540)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self.video_viewer = VideoViewer(self)
        self.playback_bar = PlaybackBar(self)

        self.open_button = QPushButton("Ouvrir...", self)
        self.enhance_button = QPushButton("Améliorer (U-Net)", self)
        self.media_label = QLabel("Aucune selection", self)
        self.media_label.setObjectName("mediaLabel")

        header = QHBoxLayout()
        header.addWidget(self.open_button)
        header.addWidget(self.enhance_button)
        header.addWidget(self.media_label, stretch=1)

        self.info_label_duration = QLabel("Duree : --:--", self)
        self.info_label_position = QLabel("Position : 00:00", self)
        self.info_label_resolution = QLabel("Resolution : -", self)
        self.info_label_fps = QLabel("FPS : -", self)

        info_bar = QHBoxLayout()
        info_bar.addWidget(self.info_label_duration)
        info_bar.addWidget(self.info_label_position)
        info_bar.addWidget(self.info_label_resolution)
        info_bar.addWidget(self.info_label_fps)
        info_bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addLayout(info_bar)
        layout.addWidget(self.video_viewer, stretch=1)
        layout.addWidget(self.playback_bar)

    def _connect_signals(self) -> None:
        self.open_button.clicked.connect(self.requestOpenMedia.emit)
        self.enhance_button.clicked.connect(self.requestEnhanceImage.emit)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_media_name(self, path: Optional[str]) -> None:
        """Display the active media path."""
        self.media_label.setText(path or "Aucune selection")

    def set_duration(self, value_ms: int) -> None:
        self.info_label_duration.setText(f"Duree : {self._format_ms(value_ms)}")

    def set_position(self, value_ms: int) -> None:
        self.info_label_position.setText(f"Position : {self._format_ms(value_ms)}")

    def set_resolution(self, width: int, height: int) -> None:
        self.info_label_resolution.setText(f"Resolution : {width} x {height}")

    def set_frame_rate(self, fps: float) -> None:
        self.info_label_fps.setText(f"FPS : {fps:.2f}")

    def reset_info(self) -> None:
        self.set_media_name(None)
        self.info_label_duration.setText("Duree : --:--")
        self.info_label_position.setText("Position : 00:00")
        self.info_label_resolution.setText("Resolution : -")
        self.info_label_fps.setText("FPS : -")

    def prompt_file(self, parent: QWidget) -> str:
        """
        Present a file selector dialog and return the chosen path.

        The view exposes this helper so controllers can delegate the UX here
        while still deciding what to do with the result.
        """
        filename, _ = QFileDialog.getOpenFileName(
            parent,
            "Ouvrir une vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.mov *.avi *.mkv);;Tous les fichiers (*)",
        )
        return filename

    def prompt_image(self, parent: QWidget) -> str:
        """
        Helper to select a still image for U-Net enhancement.
        """
        filename, _ = QFileDialog.getOpenFileName(
            parent,
            "Choisir une image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;Tous les fichiers (*)",
        )
        return filename

    def show_enhancement_summary(
        self,
        *,
        width: int,
        height: int,
        latency_ms: Optional[float],
        engine: Optional[str],
    ) -> None:
        """
        Update the info bar to reflect the latest U-Net inference metadata.
        """
        if latency_ms is not None:
            self.info_label_duration.setText(f"Latence : {latency_ms:.1f} ms")
        else:
            self.info_label_duration.setText("Latence : -")

        self.info_label_position.setText("Mode : Image")
        self.info_label_resolution.setText(f"Resolution : {width} x {height}")
        self.info_label_fps.setText(f"Moteur : {engine or 'U-Net'}")

    @staticmethod
    def _format_ms(value: int) -> str:
        seconds = max(0, value // 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
