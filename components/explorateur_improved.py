"""
Explorateur média amélioré.
Empile un header riche (stats + filtres rapides) au-dessus de l'explorateur existant.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from components.commons import COLORS, FONTS, SPACING, IconButton, PillButton, RoundedCard, StatChip
from components.explorateur import MediaExplorer


class ExplorerImproved(QWidget):
    """
    Wrapper autour de MediaExplorer qui ajoute :
    - barre d'en-tête (titre + actions)
    - bandeau de stats (compte, mode, filtre)
    - boutons de filtre rapide
    """

    video_selected = pyqtSignal(str)
    directory_selected = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_directory: str | None = None
        self._init_ui()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        header_card = RoundedCard(
            "Explorateur média",
            subtitle="Liste + miniatures avec filtre rapide",
            padding=SPACING["lg"],
        )

        # Ligne d'actions
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(SPACING["sm"])

        self.folder_btn = IconButton("📂", tooltip="Ouvrir un dossier")
        self.folder_btn.clicked.connect(self._on_pick_folder)
        actions.addWidget(self.folder_btn)

        self.refresh_btn = IconButton("⟳", tooltip="Rafraîchir le dossier courant")
        self.refresh_btn.clicked.connect(self._emit_refresh)
        actions.addWidget(self.refresh_btn)

        actions.addStretch()

        self.mode_chip = PillButton("Grille", checked=True)
        self.mode_chip.clicked.connect(self._toggle_mode)
        actions.addWidget(self.mode_chip)
        header_card.body_layout.addLayout(actions)

        # Bandeau stats
        stats_bar = QHBoxLayout()
        stats_bar.setContentsMargins(0, 0, 0, 0)
        stats_bar.setSpacing(SPACING["sm"])
        self.count_stat = StatChip("Clips", "0", kind="info")
        self.mode_stat = StatChip("Mode", "Grille", kind="neutral")
        self.filter_stat = StatChip("Filtre", "—", kind="neutral")
        stats_bar.addWidget(self.count_stat)
        stats_bar.addWidget(self.mode_stat)
        stats_bar.addWidget(self.filter_stat)
        stats_bar.addStretch()
        header_card.body_layout.addLayout(stats_bar)

        # Explorateur existant
        self.explorer = MediaExplorer()
        self.explorer.video_selected.connect(self.video_selected.emit)
        self.explorer.directory_selected.connect(self._on_directory_selected)
        self.explorer.view_mode_changed.connect(self._on_view_mode_changed)
        header_card.body_layout.addWidget(self.explorer)

        layout.addWidget(header_card)
        self.setLayout(layout)
        self.setStyleSheet(
            f"ExplorerImproved {{ background-color: transparent; }}"
            f"QLabel {{ font-family: '{FONTS['primary']}'; }}"
        )

    # ------------------------------------------------------------------ #
    # API publique (proxy vers MediaExplorer)
    # ------------------------------------------------------------------ #
    def add_video(self, name: str, color: str | None = None, path: str | None = None) -> None:
        self.explorer.add_video(name, color, path)
        self._update_count()

    def clear_videos(self) -> None:
        self.explorer.clear_videos()
        self._update_count()

    def set_view_mode(self, mode: str) -> None:
        self.explorer.set_view_mode(mode)
        self._update_mode_stat(mode)

    def set_filter_badge(self, text: str) -> None:
        self.filter_stat.findChild(QLabel, "StatChipValue").setText(text or "—")

    # ------------------------------------------------------------------ #
    # Slots internes
    # ------------------------------------------------------------------ #
    def _update_count(self) -> None:
        value_label = self.count_stat.findChild(QLabel, "StatChipValue")
        if value_label:
            value_label.setText(str(len(self.explorer.thumbnails)))

    def _update_mode_stat(self, mode: str) -> None:
        value_label = self.mode_stat.findChild(QLabel, "StatChipValue")
        if value_label:
            value_label.setText("Liste" if mode == "list" else "Grille")

    def _on_directory_selected(self, directory: str) -> None:
        self._last_directory = directory
        self.directory_selected.emit(directory)

    def _on_view_mode_changed(self, mode: str) -> None:
        self._update_mode_stat(mode)
        self.view_mode_changed.emit(mode)
        self.mode_chip.setChecked(mode == "grid")
        self.mode_chip.setText("Grille" if mode == "grid" else "Liste")

    def _toggle_mode(self) -> None:
        next_mode = "list" if self.explorer.view_mode == "grid" else "grid"
        self.set_view_mode(next_mode)

    def _on_pick_folder(self) -> None:
        # Délègue au MediaExplorer qui gère le QFileDialog
        self.explorer._choose_directory()

    def _emit_refresh(self) -> None:
        self.refresh_requested.emit()
        # Si un dossier est connu, relance un signal directory_selected pour recharger
        if self._last_directory:
            self.directory_selected.emit(self._last_directory)
