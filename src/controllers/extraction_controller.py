"""
Controller binding the extraction view with Qt multimedia backends.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QMessageBox, QWidget

from src.kosmos_processing import DeepSeaEnhancer, DeepSeaEnhancerResult
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


LOG = logging.getLogger(__name__)


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
        self._enhancer: Optional[DeepSeaEnhancer] = None
        self._last_overlay: Optional[np.ndarray] = None

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
        self.view.requestEnhanceImage.connect(self._handle_enhance_request)
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

    # ------------------------------------------------------------------
    # Deep learning enhancer integration
    # ------------------------------------------------------------------
    def _handle_enhance_request(self) -> None:
        if not self.window:
            return
        enhancer = self._get_enhancer()
        if enhancer is None:
            return

        path = self.view.prompt_image(self.window)
        if not path:
            return

        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        if frame is None:
            self._show_message(
                "Lecture image impossible",
                f"Impossible de charger l'image sélectionnée : {path}",
            )
            return

        try:
            result = enhancer.enhance(frame)
        except Exception as exc:  # pragma: no cover - safeguard
            LOG.exception("U-Net inference failed")
            self._show_message("Erreur U-Net", f"Le traitement a échoué : {exc}")
            return

        display_frame = self._pick_display_frame(frame, result)
        image = self._bgr_to_qimage(display_frame)
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
        self.view.video_viewer.display_frame(image)
        self.view.playback_bar.setEnabled(False)
        self.view.playback_bar.reset()
        self.view.set_media_name(os.path.basename(path))

        latency = float(result.meta.get("latency_ms")) if "latency_ms" in result.meta else None
        engine = str(result.meta.get("device")) if "device" in result.meta else None
        self.view.show_enhancement_summary(
            width=display_frame.shape[1],
            height=display_frame.shape[0],
            latency_ms=latency,
            engine=engine,
        )
        self._last_overlay = result.overlay_bgr

    def _get_enhancer(self) -> Optional[DeepSeaEnhancer]:
        if self._enhancer is not None:
            return self._enhancer
        try:
            self._enhancer = DeepSeaEnhancer()
            return self._enhancer
        except FileNotFoundError as exc:
            self._show_message("Dépendances manquantes", str(exc))
        except Exception as exc:  # pragma: no cover - safeguard
            LOG.exception("Unable to initialise DeepSeaEnhancer")
            self._show_message("Initialisation impossible", f"Impossible d'initialiser le modèle U-Net : {exc}")
        return None

    @staticmethod
    def _pick_display_frame(original: np.ndarray, result: DeepSeaEnhancerResult) -> np.ndarray:
        if result.restored_bgr:
            return result.restored_bgr[0]
        if result.overlay_bgr is not None:
            return result.overlay_bgr
        return original

    @staticmethod
    def _bgr_to_qimage(frame_bgr: np.ndarray) -> QImage:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        bytes_per_line = channels * width
        return QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()

    def _show_message(self, title: str, text: str) -> None:
        if not self.window:
            return
        QMessageBox.information(self.window, title, text)

    @staticmethod
    def _extract_resolution(resolution) -> tuple[int, int]:
        if hasattr(resolution, "width") and hasattr(resolution, "height"):
            return int(resolution.width()), int(resolution.height())
        if isinstance(resolution, (tuple, list)) and len(resolution) >= 2:
            return int(resolution[0]), int(resolution[1])
        return (0, 0)
