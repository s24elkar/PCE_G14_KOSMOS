"""
Nouvelle vue d'extraction utilisant les composants améliorés.
"""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from components.commons import COLORS, FONTS, SPACING, RoundedCard, Toast
from components.correction_improved import AdvancedCorrection
from components.explorateur_improved import ExplorerImproved
from components.histogramme import Histogram
from components.lecteur_improved import ModernVideoPlayer
from components.navbar import NavBar
from components.outils_modification import ExtractionTools


class ExtractionView(QWidget):
    """
    Vue Extraction modernisée :
    - colonne gauche : explorateur enrichi
    - colonne droite : lecteur principal + cartes contexte (corrections / analyse / outils)
    """

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.toast = Toast(self)
        self._init_ui()
        self.connect_signals()
        self.load_initial_data()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        main_layout.setSpacing(SPACING["lg"])

        self.navbar = NavBar(tabs=["Fichier", "Tri", "Extraction", "Évènements"], default_tab="Extraction")
        main_layout.addWidget(self.navbar)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(SPACING["lg"])

        # Colonne gauche
        self.media_explorer = ExplorerImproved()
        self.media_explorer.setMinimumWidth(340)
        content.addWidget(self.media_explorer, stretch=1)

        # Colonne droite
        right = QVBoxLayout()
        right.setSpacing(SPACING["lg"])

        self.video_player = ModernVideoPlayer()
        right.addWidget(self.video_player, stretch=3)

        # Cartes du bas
        bottom = QHBoxLayout()
        bottom.setSpacing(SPACING["lg"])

        # Correction
        self.image_correction = AdvancedCorrection()
        bottom.addWidget(self.image_correction, stretch=2)

        # Analyse + outils dans des onglets
        analysis_card = RoundedCard("Analyse & outils", subtitle="Histogramme + exports rapides", padding=SPACING["md"])
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {COLORS['border']}; border-radius: 10px; }}"
            f"QTabBar::tab {{"
            f"background: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_secondary']};"
            f"padding: 8px 14px;"
            f"border: 1px solid {COLORS['border']};"
            f"border-bottom: none;"
            f"border-top-left-radius: 8px;"
            f"border-top-right-radius: 8px;"
            f"font-weight: 700;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QTabBar::tab:selected {{ background: {COLORS['accent_cyan']}; color: {COLORS['bg_primary']}; }}"
        )

        analyse_tab = QWidget()
        analyse_layout = QVBoxLayout(analyse_tab)
        analyse_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        analyse_layout.setSpacing(SPACING["md"])
        self.histogram = Histogram()
        analyse_layout.addWidget(self.histogram)
        tabs.addTab(analyse_tab, "Analyse")

        outils_tab = QWidget()
        outils_layout = QVBoxLayout(outils_tab)
        outils_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        outils_layout.setSpacing(SPACING["md"])
        self.extraction_tools = ExtractionTools()
        outils_layout.addWidget(self.extraction_tools)
        outils_layout.addStretch()
        tabs.addTab(outils_tab, "Outils")

        analysis_card.body_layout.addWidget(tabs)
        bottom.addWidget(analysis_card, stretch=1)

        right.addLayout(bottom, stretch=2)

        content.addLayout(right, stretch=3)
        main_layout.addLayout(content)

        self.setLayout(main_layout)
        self.setObjectName("ExtractionRootImproved")
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(
            f"#ExtractionRootImproved {{"
            f"background-color: {COLORS['bg_primary']};"
            f"color: {COLORS['text_primary']};"
            f"font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif;"
            f"}}"
            f"QLabel {{ color: {COLORS['text_primary']}; }}"
            f"QPushButton {{ font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif; }}"
        )

    # ------------------------------------------------------------------ #
    # Signaux
    # ------------------------------------------------------------------ #
    def connect_signals(self):
        if not self.controller:
            return

        if hasattr(self.navbar, "tab_changed"):
            self.navbar.tab_changed.connect(self.controller.on_tab_changed)

        # Explorateur
        self.media_explorer.video_selected.connect(self.controller.on_video_selected)
        self.media_explorer.directory_selected.connect(self.controller.load_directory)
        self.media_explorer.view_mode_changed.connect(self.controller.on_view_mode_changed)

        # Outils
        if hasattr(self.extraction_tools, "screenshot_clicked"):
            self.extraction_tools.screenshot_clicked.connect(self.controller.on_screenshot)
        if hasattr(self.extraction_tools, "recording_clicked"):
            self.extraction_tools.recording_clicked.connect(self.controller.on_recording)
        if hasattr(self.extraction_tools, "short_clicked"):
            self.extraction_tools.short_clicked.connect(self.controller.on_create_short)
        if hasattr(self.extraction_tools, "crop_clicked"):
            self.extraction_tools.crop_clicked.connect(self.controller.on_crop)

        # Corrections
        self.image_correction.color_correction_clicked.connect(self.controller.on_color_correction)
        self.image_correction.apply_clicked.connect(self.controller.on_apply_corrections)
        self.image_correction.undo_clicked.connect(self.controller.on_undo_correction)
        self.image_correction.contrast_changed.connect(self.controller.on_contrast_changed)
        self.image_correction.brightness_changed.connect(self.controller.on_brightness_changed)
        self.image_correction.saturation_changed.connect(self.controller.on_saturation_changed)
        self.image_correction.hue_changed.connect(self.controller.on_hue_changed)
        self.image_correction.temperature_changed.connect(self.controller.on_temperature_changed)
        self.image_correction.sharpness_changed.connect(self.controller.on_sharpness_changed)
        self.image_correction.gamma_changed.connect(self.controller.on_gamma_changed)
        self.image_correction.denoise_changed.connect(self.controller.on_denoise_changed)
        self.image_correction.preset_selected.connect(self.controller.on_preset_selected)

        # Lecteur
        self.video_player.play_pause_clicked.connect(self.controller.on_play_pause)
        self.video_player.position_changed.connect(self.controller.on_position_changed)
        if hasattr(self.video_player, "controls"):
            c = self.video_player.controls
            if hasattr(c, "previous_clicked"):
                c.previous_clicked.connect(self.controller.on_previous_video)
            if hasattr(c, "next_clicked"):
                c.next_clicked.connect(self.controller.on_next_video)
            if hasattr(c, "rewind_clicked"):
                c.rewind_clicked.connect(self.controller.on_rewind)
            if hasattr(c, "forward_clicked"):
                c.forward_clicked.connect(self.controller.on_forward)
        if hasattr(self.video_player, "metadata_toggle_btn") and hasattr(self.controller, "on_toggle_metadata"):
            self.video_player.metadata_toggle_btn.clicked.connect(
                lambda: self.controller.on_toggle_metadata(already_toggled=True)
            )

    # ------------------------------------------------------------------ #
    # API vue (utilisée par le contrôleur)
    # ------------------------------------------------------------------ #
    def load_initial_data(self):
        if self.controller and hasattr(self.controller, "load_initial_data"):
            self.controller.load_initial_data()

    def update_video_list(self, videos):
        if hasattr(self.media_explorer, "clear_videos"):
            self.media_explorer.clear_videos()
        for video in videos:
            self.media_explorer.add_video(
                video["name"],
                video.get("thumbnail_color", "#0ea5e9"),
                video.get("path"),
            )

    def update_video_player(self, video_data, frame=None):
        if hasattr(self.video_player, "update_metadata") and "metadata" in video_data:
            self.video_player.update_metadata(**video_data["metadata"])
        if frame is not None and hasattr(self.video_player, "set_frame"):
            self.video_player.set_frame(frame)
        elif hasattr(self.video_player, "set_frame") and "path" in video_data:
            self.video_player.set_frame(None)

    def update_histogram(self, histogram_data=None):
        if histogram_data and hasattr(self.histogram, "update_histogram"):
            self.histogram.update_histogram(**histogram_data)
        elif hasattr(self.histogram, "refresh"):
            self.histogram.refresh()

    def show_message(self, message, message_type="info"):
        if hasattr(self, "toast"):
            self.toast.show_message(message, message_type)
        print(f"[{message_type.upper()}] {message}")

    def get_correction_values(self):
        if hasattr(self.image_correction, "get_contrast"):
            return {
                "contrast": self.image_correction.get_contrast(),
                "brightness": self.image_correction.get_brightness(),
                "saturation": self.image_correction.get_saturation(),
                "hue": self.image_correction.get_hue(),
                "temperature": self.image_correction.get_temperature(),
                "sharpness": self.image_correction.get_sharpness(),
                "gamma": self.image_correction.get_gamma(),
                "denoise": self.image_correction.get_denoise(),
            }
        return {}

    def toggle_metadata_visibility(self) -> None:
        if hasattr(self.video_player, "toggle_metadata_overlay"):
            self.video_player.toggle_metadata_overlay()

    def reset_corrections(self):
        if hasattr(self.image_correction, "reset_all"):
            self.image_correction.reset_all()

    def set_correction_values(self, corrections: dict):
        if hasattr(self.image_correction, "set_corrections"):
            self.image_correction.set_corrections(
                contrast=corrections.get("contrast", 0),
                brightness=corrections.get("brightness", 0),
                saturation=corrections.get("saturation", 0),
                hue=corrections.get("hue", 0),
                temperature=corrections.get("temperature", 0),
                sharpness=corrections.get("sharpness", 0),
                gamma=corrections.get("gamma", 0),
                denoise=corrections.get("denoise", 0),
            )

    def apply_corrections_to_preview(self, corrections: dict[str, int]):
        if hasattr(self.video_player, "apply_corrections"):
            self.video_player.apply_corrections(**corrections)
        if hasattr(self.histogram, "update_histogram"):
            payload = self._build_histogram_payload(corrections)
            self.update_histogram(payload)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _build_histogram_payload(self, corrections: dict[str, int]) -> dict:
        contrast = corrections.get("contrast", 0)
        brightness = corrections.get("brightness", 0)
        factor = 1 + (contrast / 200.0)
        shift = brightness * 0.8

        def scaled(channel_bias: int) -> list[int]:
            values = []
            for x in range(256):
                raw = (x + channel_bias) * factor + shift
                values.append(max(0, min(255, int(raw))))
            return values

        red = scaled(20)
        green = scaled(0)
        blue = scaled(-20)
        density = [int((r + g + b) / 3) for r, g, b in zip(red, green, blue)]
        return {"data_r": red, "data_g": green, "data_b": blue, "data_density": density}


# Test manuel
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    view = ExtractionView()
    window.setCentralWidget(view)
    window.resize(1600, 900)
    window.show()
    sys.exit(app.exec())
