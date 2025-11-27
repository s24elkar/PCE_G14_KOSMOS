"""
Lecteur vidéo modernisé.
Habille le VideoPlayer existant dans une carte + stats rapides.
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from components.commons import COLORS, FONTS, SPACING, IconButton, RoundedCard, StatChip
from components.lecteur import VideoPlayer


class ModernVideoPlayer(QWidget):
    """
    Fournit la même API que VideoPlayer mais avec un habillage enrichi.
    Signaux proxys pour que le contrôleur n'ait rien à changer.
    """

    play_pause_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.player = VideoPlayer()
        self.controls = self.player.controls  # exposé pour compatibilité
        self._init_ui()
        self._wire_signals()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = RoundedCard(
            "Lecture principale",
            subtitle="Overlay contextuel + timeline + contrôles rapides",
            accent=True,
            padding=SPACING["lg"],
        )

        # Bandeau stats
        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(SPACING["sm"])
        self.time_stat = StatChip("Temps", "00:00")
        self.dur_stat = StatChip("Durée", "--:--")
        self.res_stat = StatChip("Info", "—")
        stats.addWidget(self.time_stat)
        stats.addWidget(self.dur_stat)
        stats.addWidget(self.res_stat)
        stats.addStretch()

        self.metadata_toggle_btn = IconButton("🛈", tooltip="Afficher/masquer les métadonnées")
        self.metadata_toggle_btn.clicked.connect(self.toggle_metadata_overlay)
        stats.addWidget(self.metadata_toggle_btn)

        card.body_layout.addLayout(stats)
        card.body_layout.addWidget(self.player)
        layout.addWidget(card)

        self.setLayout(layout)
        self.setObjectName("ModernVideoPlayer")
        self.setStyleSheet(
            f"#ModernVideoPlayer {{ background-color: transparent; }}"
            f"QLabel {{ font-family: '{FONTS['primary']}'; }}"
        )

    def _wire_signals(self) -> None:
        self.player.play_pause_clicked.connect(self.play_pause_clicked.emit)
        self.player.position_changed.connect(self.position_changed.emit)

    # ------------------------------------------------------------------ #
    # Proxies vers VideoPlayer
    # ------------------------------------------------------------------ #
    def update_metadata(self, **kwargs):
        self.player.update_metadata(**kwargs)
        timecode = kwargs.get("time") or kwargs.get("timecode")
        duration = kwargs.get("duration")
        if timecode:
            self._set_stat_text(self.time_stat, timecode)
        if duration:
            self._set_stat_text(self.dur_stat, duration)
        info_parts = []
        if "temp" in kwargs and kwargs["temp"] is not None:
            info_parts.append(f"{kwargs['temp']}°C")
        if "depth" in kwargs and kwargs["depth"] is not None:
            info_parts.append(f"{kwargs['depth']}m")
        if "salinity" in kwargs and kwargs["salinity"] is not None:
            info_parts.append(f"{kwargs['salinity']}")
        self._set_stat_text(self.res_stat, " • ".join(info_parts) or "—")

    def set_frame(self, frame_rgb):
        self.player.set_frame(frame_rgb)

    def apply_corrections(self, **kwargs):
        self.player.apply_corrections(**kwargs)

    def toggle_metadata_overlay(self) -> None:
        self.player.toggle_metadata_overlay()
        self._refresh_metadata_button()

    def metadata_is_visible(self) -> bool:
        return self.player.metadata_is_visible()

    def set_markers(self, markers: list[dict]) -> None:
        self.player.set_markers(markers)

    def clear_timeline_markers(self) -> None:
        self.player.clear_timeline_markers()

    def add_timeline_marker(self, position: int, kind: str = "poi", label: str | None = None) -> None:
        self.player.add_timeline_marker(position, kind=kind, label=label)

    def set_duration_seconds(self, seconds: float) -> None:
        self.player.set_duration_seconds(seconds)

    def set_export_range(self, start: int | None, end: int | None) -> None:
        self.player.set_export_range(start, end)

    def set_position(self, position: int) -> None:
        self.player.set_position(position)

    def get_position(self) -> int:
        return self.player.get_position()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _set_stat_text(self, chip: StatChip, text: str) -> None:
        label = chip.findChild(QLabel, "StatChipValue")
        if label:
            label.setText(text)

    def _refresh_metadata_button(self) -> None:
        visible = self.metadata_is_visible()
        self.metadata_toggle_btn.setText("🛈" if visible else "🙈")
        self.metadata_toggle_btn.setToolTip(
            "Masquer l'overlay métadonnées (M)" if visible else "Afficher l'overlay métadonnées (M)"
        )
