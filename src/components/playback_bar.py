"""
Reusable playback bar widget for the KOSMOS interface.

The widget exposes play/pause controls, a seek slider and elapsed/duration
labels. It can drive an external ``QMediaPlayer`` instance or any backend that
listens to the emitted signals.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QStyle,
    QToolButton,
)

try:
    from PyQt6.QtMultimedia import QMediaPlayer
except ImportError:  # pragma: no cover - optional dependency for design time
    QMediaPlayer = None  # type: ignore

if TYPE_CHECKING:
    from PyQt6.QtMultimedia import QMediaPlayer  # noqa: F811


@dataclass
class PlaybackState:
    """Internal state container for the playback bar."""

    duration: int = 0  # milliseconds
    position: int = 0  # milliseconds
    scrubbing: bool = False


class PlaybackBar(QWidget):
    """
    Composite widget exposing transport controls for a media player.

    Signals
    -------
    playRequested: emitted when the play button is pressed.
    pauseRequested: emitted when the pause button is pressed.
    seekRequested(position_ms): emitted when the user releases the slider.
    positionPreview(position_ms): emitted while scrubbing.
    """

    playRequested = pyqtSignal()
    pauseRequested = pyqtSignal()
    seekRequested = pyqtSignal(int)
    positionPreview = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._state = PlaybackState()
        self._player: Optional["QMediaPlayer"] = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        self.play_button = QToolButton(self)
        style = self.style()
        self.play_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setToolTip("Lire/Pause")

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 0)

        self.elapsed_label = QLabel("00:00", self)
        self.elapsed_label.setMinimumWidth(48)
        self.duration_label = QLabel("00:00", self)
        self.duration_label.setMinimumWidth(48)

        layout.addWidget(self.play_button)
        layout.addWidget(self.elapsed_label)
        layout.addWidget(self.slider, stretch=1)
        layout.addWidget(self.duration_label)

    def _connect_signals(self) -> None:
        self.play_button.clicked.connect(self._toggle_playback)
        self.slider.sliderPressed.connect(self._start_scrub)
        self.slider.sliderReleased.connect(self._finish_scrub)
        self.slider.sliderMoved.connect(self._preview_position)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_player(self, player: "QMediaPlayer") -> None:
        """
        Attach a QMediaPlayer instance to drive automatically.

        Parameters
        ----------
        player:
            The media player to control.
        """
        if QMediaPlayer is None:
            raise RuntimeError(
                "QtMultimedia is not available; cannot attach QMediaPlayer."
            )

        if self._player is player:
            return

        if self._player is not None:
            self._disconnect_player_signals(self._player)

        self._player = player
        player.durationChanged.connect(self._update_duration)
        player.positionChanged.connect(self._update_position)
        player.playbackStateChanged.connect(self._update_play_icon)

        self.playRequested.connect(player.play)
        self.pauseRequested.connect(player.pause)
        self.seekRequested.connect(player.setPosition)

    def set_duration(self, duration_ms: int) -> None:
        self._state.duration = max(0, duration_ms)
        self.slider.setRange(0, self._state.duration)
        self.duration_label.setText(self._format_ms(self._state.duration))

    def set_position(self, position_ms: int) -> None:
        if self._state.scrubbing:
            return
        self._state.position = max(0, min(position_ms, self._state.duration))
        self.slider.setValue(self._state.position)
        self.elapsed_label.setText(self._format_ms(self._state.position))

    def reset(self) -> None:
        self.set_duration(0)
        self.set_position(0)
        self._update_play_icon()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _toggle_playback(self) -> None:
        if not self._is_playing():
            self.playRequested.emit()
        else:
            self.pauseRequested.emit()

    def _start_scrub(self) -> None:
        self._state.scrubbing = True

    def _preview_position(self, position: int) -> None:
        self.positionPreview.emit(position)
        self.elapsed_label.setText(self._format_ms(position))

    def _finish_scrub(self) -> None:
        self._state.scrubbing = False
        position = self.slider.value()
        self.seekRequested.emit(position)
        self.set_position(position)

    def _update_duration(self, duration: int) -> None:
        self.set_duration(duration)

    def _update_position(self, position: int) -> None:
        self.set_position(position)

    def _update_play_icon(self) -> None:
        style = self.style()
        is_playing = self._is_playing()
        icon = (
            style.standardIcon(QStyle.StandardPixmap.SP_MediaPause)
            if is_playing
            else style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.play_button.setIcon(icon)

    def _is_playing(self) -> bool:
        if self._player is None or QMediaPlayer is None:
            return False
        return (
            self._player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def _disconnect_player_signals(self, player: "QMediaPlayer") -> None:
        try:
            player.durationChanged.disconnect(self._update_duration)
            player.positionChanged.disconnect(self._update_position)
            player.playbackStateChanged.disconnect(self._update_play_icon)
        except TypeError:
            pass

        try:
            self.playRequested.disconnect(player.play)
        except TypeError:
            pass
        try:
            self.pauseRequested.disconnect(player.pause)
        except TypeError:
            pass
        try:
            self.seekRequested.disconnect(player.setPosition)
        except TypeError:
            pass

    @staticmethod
    def _format_ms(value: int) -> str:
        seconds = max(0, value // 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
