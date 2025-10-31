"""
Controller binding the extraction view with Qt multimedia backends.
"""
from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtWidgets import QMessageBox, QWidget

from src.views.extraction_view import ExtractionView

try:
    from PyQt6.QtMultimedia import (
        QAudioOutput,
        QMediaMetaData,
        QMediaPlayer,
    )
except ImportError as exc:  # pragma: no cover - multimedia optional
    raise ImportError(
        "QtMultimedia is required to use the extraction controller."
    ) from exc


class ExtractionController(QObject):
    """
    Lightweight controller orchestrating playback interactions.
    """

    def __init__(
        self,
        view: ExtractionView,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.view = view
        self.window: Optional[QWidget] = view

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.view.video_viewer.set_player(self.player)
        self.view.playback_bar.set_player(self.player)
        self.view.playback_bar.reset()
        self.view.playback_bar.setEnabled(False)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.view.requestOpenMedia.connect(self.open_media_dialog)
        self.player.mediaStatusChanged.connect(self._update_title)
        self.player.errorOccurred.connect(self._handle_error)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)

    def open_media_dialog(self) -> None:
        if not self.window:
            return
        filename = self.view.prompt_file(self.window)
        if filename:
            self.load_media(filename)

    def load_media(self, path: str) -> None:
        """Load the provided media file into the player."""
        url = QUrl.fromLocalFile(path)
        self.view.reset_info()
        self.player.setSource(url)
        self.view.set_media_name(os.path.basename(path))
        self.view.playback_bar.setEnabled(True)

    def _update_title(self) -> None:
        if not self.window:
            return
        status = self.player.mediaStatus()
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.window.setWindowTitle(
                f"KOSMOS – Extraction · {self.view.media_label.text()}"
            )
            self._refresh_media_metrics()

    def _handle_error(self, error: QMediaPlayer.Error, detail: str) -> None:
        if error == QMediaPlayer.Error.NoError or not self.window:
            return
        QMessageBox.critical(
            self.window,
            "Lecture impossible",
            f"Impossible de lire la vidéo : {detail}",
        )

    def _on_duration_changed(self, duration: int) -> None:
        self.view.set_duration(duration)

    def _on_position_changed(self, position: int) -> None:
        self.view.set_position(position)

    def _refresh_media_metrics(self) -> None:
        self.view.set_duration(self.player.duration())
        metadata = self.player.metaData()
        if metadata is None:
            return

        resolution = metadata.value(QMediaMetaData.Key.VideoResolution)
        if resolution:
            width, height = self._extract_resolution(resolution)
            if width and height:
                self.view.set_resolution(width, height)

        fps = metadata.value(QMediaMetaData.Key.VideoFrameRate)
        if fps:
            try:
                self.view.set_frame_rate(float(fps))
            except (TypeError, ValueError):
                pass

    @staticmethod
    def _extract_resolution(resolution) -> tuple[int, int]:
        if hasattr(resolution, "width") and hasattr(resolution, "height"):
            return int(resolution.width()), int(resolution.height())
        if isinstance(resolution, (tuple, list)) and len(resolution) >= 2:
            return int(resolution[0]), int(resolution[1])
        return (0, 0)
